"""
RAG Retriever using local embeddings cache with cosine similarity search.
No Supabase required - works entirely from CSV + generated embeddings.
"""
import json
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from backend.models.schemas import DoctorSearchQuery, VerifiedDoctor
from backend.modules.doctors.retriever import (
    CLINICAL_SYMPTOM_MAP,
    get_cached_doctors,
    search_doctors_in_dataset,
)

EMBEDDING_CACHE = Path(__file__).resolve().parent.parent.parent.parent / "backend" / "data" / "doctor_embeddings.json"

_CACHED_EMBEDDINGS: Optional[List[Dict[str, Any]]] = None


def get_embeddings() -> List[Dict[str, Any]]:
    """Load pre-computed embeddings from JSON cache."""
    global _CACHED_EMBEDDINGS
    if _CACHED_EMBEDDINGS is None:
        if not EMBEDDING_CACHE.exists():
            raise FileNotFoundError(
                f"Embeddings cache not found at {EMBEDDING_CACHE}. "
                f"Run 'python backend/scripts/seed_embeddings.py' first."
            )
        with open(EMBEDDING_CACHE, 'r', encoding='utf-8') as f:
            _CACHED_EMBEDDINGS = json.load(f)
    return _CACHED_EMBEDDINGS


def get_doctor_records() -> List[Dict[str, Any]]:
    """Return indexed records when available, otherwise use the local dataset."""
    try:
        return get_embeddings()
    except FileNotFoundError:
        return get_cached_doctors()


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def generate_query_embedding(query: str) -> List[float]:
    """Generate embedding for a user query using Gemini."""
    from backend.core.config import settings
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=30_000),
    )
    result = client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=[query],
    )
    return result.embeddings[0].values


def map_symptoms_to_specialties(query_text: str) -> Tuple[List[str], List[str]]:
    """Returns (primary_specialties, secondary_specialties) inferred from clinical keywords."""
    q_lower = query_text.lower()
    primary = []
    secondary = []
    for symptom, mapping in CLINICAL_SYMPTOM_MAP.items():
        if re.search(r"\b" + re.escape(symptom) + r"\b", q_lower):
            for p in mapping["primary"]:
                if p not in primary:
                    primary.append(p)
            for s in mapping["secondary"]:
                if s not in secondary:
                    secondary.append(s)
    return primary, secondary


def compute_hybrid_score(
    query_embedding: List[float],
    query_tokens: List[str],
    primary_specs: List[str],
    secondary_specs: List[str],
    doc: Dict[str, Any],
    target_city: Optional[str],
    semantic_weight: float = 0.6,
    keyword_weight: float = 0.4
) -> float:
    """Combine semantic similarity with keyword/clinical matching."""
    # Semantic similarity (0-1) -> scaled to 0-100
    semantic_score = cosine_similarity(query_embedding, doc["embedding"]) * 100

    # Keyword/clinical scoring (same as original retriever)
    keyword_score = 0.0
    doc_text_lower = doc["search_document"].lower()
    doc_specs_lower = [s.lower() for s in doc["specializations"]]
    doc_city_lower = doc["city"].lower()

    # Primary specialty match: +50 points
    for spec in primary_specs:
        if any(spec.lower() in ds for ds in doc_specs_lower):
            keyword_score += 50.0

    # Secondary specialty match (fallback): +5 points
    for spec in secondary_specs:
        if any(spec.lower() in ds for ds in doc_specs_lower):
            keyword_score += 5.0

    # City match boost: +20 points
    if target_city:
        if target_city.lower() in doc_city_lower:
            keyword_score += 20.0
        elif primary_specs:
            keyword_score += 5.0

    # Lexical token matches
    for token in query_tokens:
        if token in doc_text_lower:
            if token in doc["doctor_name"].lower():
                keyword_score += 8.0
            elif any(token in ds for ds in doc_specs_lower):
                keyword_score += 5.0
            else:
                keyword_score += 1.0

    # Quality tiebreaker
    keyword_score += (doc["patient_satisfaction_pct"] / 100.0) * 2.0

    # Combine: normalize keyword_score to roughly 0-100 range
    # Max possible keyword_score ~ 50+5+20+8*tokens+2 ≈ 100-150
    norm_keyword = min(keyword_score / 100.0, 1.0) * 100

    return semantic_weight * semantic_score + keyword_weight * norm_keyword


def search_doctors_rag(query_req: DoctorSearchQuery) -> List[VerifiedDoctor]:
    """
    Hybrid RAG search: semantic embeddings + clinical keyword matching.
    Guarantees 100% genuine Pakistani doctors from dataset.
    """
    try:
        all_docs = get_embeddings()
    except FileNotFoundError:
        return search_doctors_in_dataset(query_req)

    # Extract target city if mentioned in natural language query
    q_lower = query_req.query.lower()
    detected_city = query_req.city
    if not detected_city:
        for doc in all_docs:
            c = doc["city"]
            if len(c) > 3 and re.search(r"\b" + re.escape(c.lower()) + r"\b", q_lower):
                detected_city = c
                break

    # Infer clinical specialty from symptoms
    primary_specs, secondary_specs = map_symptoms_to_specialties(query_req.query)
    if query_req.specialization:
        if query_req.specialization not in primary_specs:
            primary_specs.insert(0, query_req.specialization)

    # Tokenize query words
    q_tokens = [w.lower() for w in re.findall(r"\b\w{3,}\b", query_req.query)]

    # Generate query embedding
    print("[RAG] Generating query embedding")
    query_embedding = generate_query_embedding(query_req.query)

    # Filter and score doctors
    scored_candidates = []
    for doc in all_docs:
        # Structured filters
        if query_req.max_fee and doc["fee_pkr"] > query_req.max_fee:
            continue
        if query_req.min_experience_years and doc["experience_years"] < query_req.min_experience_years:
            continue
        if query_req.min_satisfaction_rate and doc["patient_satisfaction_pct"] < query_req.min_satisfaction_rate:
            continue

        # Hard city filter
        if detected_city and detected_city.lower() not in doc["city"].lower():
            continue

        score = compute_hybrid_score(
            query_embedding, q_tokens, primary_specs, secondary_specs,
            doc, detected_city
        )
        if score > 0:
            scored_candidates.append({**doc, "score": score})

    # Sort descending by hybrid score, then satisfaction, then experience
    scored_candidates.sort(
        key=lambda x: (x["score"], x["patient_satisfaction_pct"], x["experience_years"]),
        reverse=True
    )

    top_candidates = scored_candidates[:query_req.limit]

    # Convert to VerifiedDoctor model
    results: List[VerifiedDoctor] = []
    for d in top_candidates:
        hosp_str = f"at {d['hospital_name']}" if d.get("hospital_name") else f"in {d['city']}"
        rec_reason = (
            f"Recommended {d['specialization_primary']} {hosp_str} with {d['experience_years']:.0f} years experience, "
            f"{d['patient_satisfaction_pct']:.0f}% satisfaction across {d['total_reviews']} reviews. "
            f"Consultation fee: {d['fee_pkr']} PKR. (Hybrid score: {d['score']:.1f})"
        )

        results.append(VerifiedDoctor(
            id=d["raw_hash"],
            doctor_name=d["doctor_name"],
            title_prefix=d.get("title_prefix", "Dr."),
            city=d["city"],
            specialization_primary=d["specialization_primary"],
            specializations=d["specializations"],
            qualifications=d["qualifications"],
            experience_years=d["experience_years"],
            total_reviews=d["total_reviews"],
            patient_satisfaction_pct=d["patient_satisfaction_pct"],
            avg_time_to_patients_mins=d["avg_time_to_patients_mins"],
            wait_time_mins=d["wait_time_mins"],
            hospital_name=d["hospital_name"],
            hospital_address=d["hospital_address"],
            profile_url=d["profile_url"],
            fee_pkr=d["fee_pkr"],
            relevance_score=float(d["score"]),
            recommendation_reason=rec_reason
        ))

    return results
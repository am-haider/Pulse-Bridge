import re
from typing import List, Dict, Any, Optional
from backend.core.supabase_client import get_supabase_client
from backend.models.schemas import DoctorSearchQuery, VerifiedDoctor
from backend.modules.doctors.cleaner import load_and_clean_doctors

# Clinical Symptom to Specialty Hierarchy: Primary specialists get heavy weight; General Physicians get minor fallback weight
CLINICAL_SYMPTOM_MAP: Dict[str, Dict[str, List[str]]] = {
    "heart": {
        "primary": ["Cardiologist", "Pulmonologist / Lung Specialist, Cardiologist", "Cardiologist, Diabetologist, Gastroenterologist"],
        "secondary": ["General Physician"]
    },
    "cardiac": {
        "primary": ["Cardiologist", "Pulmonologist / Lung Specialist, Cardiologist"],
        "secondary": ["General Physician"]
    },
    "chest pain": {
        "primary": ["Cardiologist", "Pulmonologist / Lung Specialist"],
        "secondary": ["General Physician"]
    },
    "blood pressure": {
        "primary": ["Cardiologist"],
        "secondary": ["General Physician"]
    },
    "hypertension": {
        "primary": ["Cardiologist"],
        "secondary": ["General Physician"]
    },
    "skin": {
        "primary": ["Dermatologist", "Cosmetic Surgeon"],
        "secondary": ["General Physician"]
    },
    "acne": {
        "primary": ["Dermatologist"],
        "secondary": ["General Physician"]
    },
    "child": {
        "primary": ["Pediatrician"],
        "secondary": ["General Physician"]
    },
    "baby": {
        "primary": ["Pediatrician"],
        "secondary": ["General Physician"]
    },
    "kidney": {
        "primary": ["Nephrologist", "Urologist"],
        "secondary": ["General Physician"]
    },
    "urine": {
        "primary": ["Urologist", "Nephrologist"],
        "secondary": ["General Physician"]
    },
    "stomach": {
        "primary": ["Gastroenterologist"],
        "secondary": ["General Physician"]
    },
    "liver": {
        "primary": ["Gastroenterologist"],
        "secondary": ["General Physician"]
    },
    "brain": {
        "primary": ["Neurologist", "Neuro Surgeon"],
        "secondary": ["General Physician"]
    },
    "headache": {
        "primary": ["Neurologist"],
        "secondary": ["General Physician"]
    },
    "bone": {
        "primary": ["Orthopedic Surgeon"],
        "secondary": []
    },
    "fracture": {
        "primary": ["Orthopedic Surgeon"],
        "secondary": []
    },
    "joint": {
        "primary": ["Orthopedic Surgeon"],
        "secondary": []
    },
    "eye": {
        "primary": ["Eye Surgeon", "Eye Specialist"],
        "secondary": []
    },
    "vision": {
        "primary": ["Eye Surgeon", "Eye Specialist"],
        "secondary": []
    },
    "ear": {
        "primary": ["Ent Specialist"],
        "secondary": []
    },
    "nose": {
        "primary": ["Ent Specialist"],
        "secondary": []
    },
    "throat": {
        "primary": ["Ent Specialist"],
        "secondary": []
    },
    "lung": {
        "primary": ["Pulmonologist / Lung Specialist"],
        "secondary": ["General Physician"]
    },
    "cough": {
        "primary": ["Pulmonologist / Lung Specialist"],
        "secondary": ["General Physician"]
    },
    "women": {
        "primary": ["Gynecologist"],
        "secondary": []
    },
    "pregnancy": {
        "primary": ["Gynecologist"],
        "secondary": []
    },
    "teeth": {
        "primary": ["Dentist"],
        "secondary": []
    },
    "dental": {
        "primary": ["Dentist"],
        "secondary": []
    },
    "diabetes": {
        "primary": ["Cardiologist, Diabetologist, Gastroenterologist"],
        "secondary": ["General Physician"]
    },
    "general": {
        "primary": ["General Physician"],
        "secondary": []
    }
}

_CACHED_DOCTORS: Optional[List[Dict[str, Any]]] = None


def get_cached_doctors() -> List[Dict[str, Any]]:
    global _CACHED_DOCTORS
    if _CACHED_DOCTORS is None:
        _CACHED_DOCTORS = load_and_clean_doctors()
    return _CACHED_DOCTORS


def map_symptoms_to_specialties(query_text: str) -> tuple[List[str], List[str]]:
    """
    Returns (primary_specialties, secondary_specialties) inferred from clinical keywords in query.
    """
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


def compute_relevance_score(
    query_tokens: List[str],
    primary_specs: List[str],
    secondary_specs: List[str],
    doc: Dict[str, Any],
    target_city: Optional[str]
) -> float:
    score = 0.0
    doc_text_lower = doc["search_document"].lower()
    doc_specs_lower = [s.lower() for s in doc["specializations"]]
    doc_city_lower = doc["city"].lower()

    # Primary specialty match: +50 points
    for spec in primary_specs:
        if any(spec.lower() in ds for ds in doc_specs_lower):
            score += 50.0

    # Secondary specialty match (fallback): +5 points
    for spec in secondary_specs:
        if any(spec.lower() in ds for ds in doc_specs_lower):
            score += 5.0

    # City match boost: +20 points
    if target_city:
        if target_city.lower() in doc_city_lower:
            score += 20.0
        elif primary_specs:
            # If specific specialist is needed and not in target city, still allow them but with lower location priority
            score += 5.0

    # Lexical token matches
    for token in query_tokens:
        if token in doc_text_lower:
            if token in doc["doctor_name"].lower():
                score += 8.0
            elif any(token in ds for ds in doc_specs_lower):
                score += 5.0
            else:
                score += 1.0

    # Quality tiebreaker
    score += (doc["patient_satisfaction_pct"] / 100.0) * 2.0

    return score


def search_doctors_in_dataset(query_req: DoctorSearchQuery) -> List[VerifiedDoctor]:
    """
    Executes grounded hybrid retrieval:
    1. Extracts clinical intent (e.g. 'heart' -> Cardiologist).
    2. Identifies target city from query text or explicit city filter.
    3. Searches Supabase or in-memory cleaned records.
    4. Guarantees 100% genuine Pakistani doctors present in dataset.
    """
    all_docs = get_cached_doctors()

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

        # Hard city filter: when city is explicitly provided, exclude doctors from other cities
        if detected_city and detected_city.lower() not in doc["city"].lower():
            continue

        score = compute_relevance_score(q_tokens, primary_specs, secondary_specs, doc, detected_city)
        if score > 0:
            scored_candidates.append({**doc, "score": score})

    # Sort descending by relevance score, then satisfaction, then experience
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
            f"Consultation fee: {d['fee_pkr']} PKR."
        )

        results.append(VerifiedDoctor(
            id=d["raw_hash"],
            doctor_name=d["doctor_name"],
            title_prefix=d["title_prefix"],
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

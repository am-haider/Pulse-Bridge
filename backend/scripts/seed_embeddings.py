#!/usr/bin/env python
"""
Generate Gemini embeddings for all doctors from CSV and save to local JSON cache.
Run this once to build the vector index for RAG.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.modules.doctors.cleaner import load_and_clean_doctors
from backend.core.config import settings
from google import genai
from google.genai import types


EMBEDDING_CACHE = Path(__file__).resolve().parent.parent.parent / "backend" / "data" / "doctor_embeddings.json"
CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "doctors.csv"


def generate_embeddings():
    """Generate embeddings for all doctors using Gemini embedding model."""
    if not settings.GEMINI_API_KEY or "your-gemini" in settings.GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not configured in backend/.env")
        sys.exit(1)

    print(f"[INFO] Loading doctors from {CSV_PATH}...")
    doctors = load_and_clean_doctors()
    print(f"[INFO] Loaded {len(doctors)} doctors")

    print("[INFO] Initializing Gemini client...")
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=60_000),
    )

    embeddings = []
    batch_size = 20  # Smaller batches to avoid rate limits

    for i in range(0, len(doctors), batch_size):
        batch = doctors[i:i+batch_size]
        texts = [d["search_document"] for d in batch]

        print(f"[INFO] Generating embeddings for batch {i//batch_size + 1}/{(len(doctors)-1)//batch_size + 1} ({len(batch)} docs)...")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = client.models.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    contents=texts,
                )

                for j, embedding in enumerate(result.embeddings):
                    doc = batch[j]
                    embeddings.append({
                        "raw_hash": doc["raw_hash"],
                        "doctor_name": doc["doctor_name"],
                        "city": doc["city"],
                        "specialization_primary": doc["specialization_primary"],
                        "specializations": doc["specializations"],
                        "qualifications": doc["qualifications"],
                        "experience_years": doc["experience_years"],
                        "total_reviews": doc["total_reviews"],
                        "patient_satisfaction_pct": doc["patient_satisfaction_pct"],
                        "avg_time_to_patients_mins": doc["avg_time_to_patients_mins"],
                        "wait_time_mins": doc["wait_time_mins"],
                        "hospital_name": doc["hospital_name"],
                        "hospital_address": doc["hospital_address"],
                        "profile_url": doc["profile_url"],
                        "fee_pkr": doc["fee_pkr"],
                        "search_document": doc["search_document"],
                        "embedding": embedding.values,
                    })
                break  # Success, exit retry loop

            except Exception as e:
                error_str = str(e)
                if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                    wait_time = 60 if attempt < max_retries - 1 else 0
                    print(f"[WARN] Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    if wait_time > 0:
                        time.sleep(wait_time)
                    else:
                        print(f"[ERROR] Max retries reached for batch {i//batch_size + 1}: {e}")
                        sys.exit(1)
                else:
                    print(f"[ERROR] Failed batch {i//batch_size + 1}: {e}")
                    sys.exit(1)

        # Small delay between batches
        if i + batch_size < len(doctors):
            time.sleep(2)

    print(f"[INFO] Saving {len(embeddings)} embeddings to {EMBEDDING_CACHE}...")
    with open(EMBEDDING_CACHE, 'w', encoding='utf-8') as f:
        json.dump(embeddings, f)

    print("[OK] Embeddings cache created successfully!")


if __name__ == "__main__":
    generate_embeddings()
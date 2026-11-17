import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
CSV_PATH = DATA_DIR / "doctors.csv"


def canonicalize_city(raw_city: str) -> str:
    """
    Transforms uppercase and hyphenated city strings into clean canonical names.
    e.g. 'LAHORE' -> 'Lahore', 'BAJAUR-AGENCY' -> 'Bajaur Agency', 'TANDO-MUHAMMAD-KHAN' -> 'Tando Muhammad Khan'
    """
    if not raw_city or not isinstance(raw_city, str):
        return "Unknown"
    cleaned = raw_city.strip().replace("-", " ")
    return cleaned.title()


def parse_specializations(raw_spec: str) -> List[str]:
    """
    Splits composite specializations, trims whitespace, and deduplicates preserving order.
    e.g. 'Dermatologist, Cosmetic Surgeon, Dermatologist' -> ['Dermatologist', 'Cosmetic Surgeon']
    """
    if not raw_spec or not isinstance(raw_spec, str):
        return ["General Physician"]
    parts = [p.strip() for p in raw_spec.split(",") if p.strip()]
    unique_specs = []
    seen = set()
    for p in parts:
        lower_p = p.lower()
        if lower_p not in seen:
            seen.add(lower_p)
            unique_specs.append(p)
    return unique_specs if unique_specs else ["General Physician"]


def extract_title_prefix(name: str) -> tuple[str, str]:
    """
    Extracts the academic or clinical title prefix from the doctor's name.
    e.g. 'Prof. Dr. Syed Shamsuddin' -> ('Prof. Dr.', 'Syed Shamsuddin')
    """
    prefixes = [
        "Prof. Dr.", "Assoc. Prof. Dr.", "Asst. Prof. Dr.",
        "Assist. Prof. Dr.", "Professor Dr.", "Dr."
    ]
    name_str = name.strip()
    for prefix in prefixes:
        if name_str.startswith(prefix):
            clean_name = name_str[len(prefix):].strip()
            return prefix, clean_name
    return "Dr.", name_str


def generate_doctor_hash(name: str, city: str, hospital: str) -> str:
    """
    Computes a deterministic SHA256 signature for idempotent ingestion.
    """
    key = f"{name.strip().lower()}|{city.strip().lower()}|{hospital.strip().lower()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def build_search_document(
    name: str,
    city: str,
    primary_spec: str,
    specs: List[str],
    qualifications: str,
    experience_years: float,
    hospital: Optional[str],
    fee: int,
    satisfaction: float
) -> str:
    """
    Creates a rich, coherent textual document for dense embeddings and hybrid full-text search.
    """
    spec_str = ", ".join(specs)
    hosp_str = f"at {hospital}" if hospital else "clinic/hospital unlisted"
    return (
        f"Doctor {name} is a verified {primary_spec} practicing in {city} {hosp_str}. "
        f"Specialties: {spec_str}. Qualifications: {qualifications}. "
        f"Clinical Experience: {experience_years:.0f} years. "
        f"Patient Satisfaction Rating: {satisfaction:.0f}%. Consultation Fee: {fee} PKR."
    )


def load_and_clean_doctors() -> List[Dict[str, Any]]:
    """
    Loads data/doctors.csv, cleans duplicates and placeholders without altering the original file.
    Returns a list of clean dictionary records ready for database seeding and search.
    """
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Doctors CSV file not found at {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    # Drop exact duplicated rows
    df = df.drop_duplicates()

    cleaned_doctors: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        raw_name = str(row["Doctor Name"]).strip()
        title_prefix, clean_name = extract_title_prefix(raw_name)

        city = canonicalize_city(str(row["City"]))
        raw_spec = str(row["Specialization"])
        specs = parse_specializations(raw_spec)
        primary_spec = specs[0] if specs else "General Physician"

        quals = str(row["Doctor Qualification"]).strip()
        exp = float(row.get("Experience(Years)", 0.0))
        reviews = int(row.get("Total_Reviews", 0))
        satisfaction = float(row.get("Patient Satisfaction Rate(%age)", 100.0))
        avg_time = int(row.get("Avg Time to Patients(mins)", 15))
        wait_time = int(row.get("Wait Time(mins)", 15))

        raw_addr = str(row.get("Hospital Address", "")).strip()
        hospital_address = None if raw_addr in ["No Address Available", "nan", ""] else raw_addr

        # Extract hospital name if address is present
        hospital_name = None
        if hospital_address:
            hospital_name = hospital_address.split(",")[0].strip()

        raw_link = str(row.get("Doctors Link", "")).strip()
        profile_url = None if raw_link in ["No Link Available", "nan", ""] else raw_link

        fee = int(row.get("Fee(PKR)", 0))

        raw_hash = generate_doctor_hash(raw_name, city, hospital_address or "unlisted")
        search_doc = build_search_document(
            raw_name, city, primary_spec, specs, quals, exp, hospital_name, fee, satisfaction
        )

        record = {
            "raw_hash": raw_hash,
            "doctor_name": raw_name,
            "title_prefix": title_prefix,
            "city": city,
            "specialization_primary": primary_spec,
            "specializations": specs,
            "qualifications": quals,
            "experience_years": exp,
            "total_reviews": reviews,
            "patient_satisfaction_pct": satisfaction,
            "avg_time_to_patients_mins": avg_time,
            "wait_time_mins": wait_time,
            "hospital_name": hospital_name,
            "hospital_address": hospital_address,
            "profile_url": profile_url,
            "fee_pkr": fee,
            "search_document": search_doc
        }
        cleaned_doctors.append(record)

    return cleaned_doctors

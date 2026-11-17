from typing import List, Dict, Any
from backend.core.config import settings
from backend.models.schemas import (
    DoctorSearchQuery,
    DoctorSearchResponse,
    VerifiedDoctor,
    DoctorFilterMetaResponse
)
from backend.modules.doctors.rag_retriever import search_doctors_rag, get_doctor_records


def generate_grounded_summary(query: str, doctors: List[VerifiedDoctor], city: str = None) -> str:
    """
    Synthesizes a grounded, patient-friendly summary strictly based on retrieved doctor records.
    """
    if not doctors:
        loc_str = f" in {city}" if city else ""
        return (
            f"No verified doctors matching your exact search criteria were located{loc_str}. "
            f"Try adjusting your filters or expanding your consultation fee limit."
        )

    count = len(doctors)
    first = doctors[0]
    first_exp = f"{first.experience_years:.0f} years of clinical experience"
    first_rating = f"{first.patient_satisfaction_pct:.0f}% patient satisfaction"

    summary = (
        f"Found {count} verified practitioner{'s' if count > 1 else ''} matching your inquiry. "
        f"Top match is {first.doctor_name} ({first.specialization_primary} in {first.city}) "
        f"with {first_exp} and {first_rating} across {first.total_reviews} verified reviews. "
        f"Consultation fee: {first.fee_pkr} PKR."
    )
    return summary


class DoctorRAGService:
    @staticmethod
    def search(query_req: DoctorSearchQuery) -> DoctorSearchResponse:
        """
        Executes hybrid RAG retrieval (semantic + clinical keywords) and synthesizes the final response.
        """
        doctors = search_doctors_rag(query_req)
        summary = generate_grounded_summary(query_req.query, doctors, query_req.city)

        applied = {}
        if query_req.city:
            applied["city"] = query_req.city
        if query_req.specialization:
            applied["specialization"] = query_req.specialization
        if query_req.max_fee:
            applied["max_fee"] = query_req.max_fee

        return DoctorSearchResponse(
            total_found=len(doctors),
            query_interpreted=f"Search for {query_req.query}",
            applied_filters=applied,
            grounded_summary=summary,
            doctors=doctors
        )

    @staticmethod
    def get_filter_meta() -> DoctorFilterMetaResponse:
        """
        Extracts sorted unique cities and specializations for frontend dropdown filters.
        """
        all_docs = get_doctor_records()
        cities = sorted(list(set(d["city"] for d in all_docs if d["city"])))
        specs = sorted(list(set(d["specialization_primary"] for d in all_docs if d["specialization_primary"])))
        return DoctorFilterMetaResponse(
            cities=cities,
            specializations=specs,
            total_doctors=len(all_docs)
        )

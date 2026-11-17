from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


# ------------------------------------------------------------------------------
# 1. SYSTEM HEALTH SCHEMAS
# ------------------------------------------------------------------------------
class SystemHealthResponse(BaseModel):
    status: str
    version: str = "2.0.0"
    supabase_configured: bool
    gemini_configured: bool
    missing_configurations: List[str] = []


class DoctorAssistantChatRequest(BaseModel):
    user_message: str = Field(min_length=1, max_length=4000)

    @field_validator("user_message")
    @classmethod
    def strip_user_message(cls, value: str) -> str:
        message = value.strip()
        if not message:
            raise ValueError("Message cannot be blank.")
        return message


class DoctorAssistantChatResponse(BaseModel):
    reply: str = Field(min_length=1)


# ------------------------------------------------------------------------------
# 2. MEDICAL REPORT EXPLAINER SCHEMAS
# ------------------------------------------------------------------------------
class BiomarkerItem(BaseModel):
    name: str = Field(description="Name of the test or biomarker, e.g. Hemoglobin, Fasting Blood Sugar")
    observed_value: str = Field(description="Patient's test value with unit, e.g. 9.5 g/dL")
    reference_range: str = Field(description="Standard reference interval, e.g. 12.0 - 15.5 g/dL")
    status: str = Field(description="'NORMAL', 'LOW', 'ELEVATED', or 'INDETERMINATE'")
    clinical_note_layman: str = Field(description="Plain-language definition of what this marker measures")


class ReportExplanationResponse(BaseModel):
    id: Optional[str] = None
    report_title: str
    detected_category: str
    language: str = "en"
    biomarkers: List[BiomarkerItem]
    abnormal_findings_summary: str
    overall_health_insight: str
    suggested_questions_for_doctor: List[str]
    dietary_lifestyle_considerations: List[str] = []
    key_takeaways: List[str] = []
    mandatory_disclaimer: str


# ------------------------------------------------------------------------------
# 3. BLOOD DONOR MATCHING SCHEMAS
# ------------------------------------------------------------------------------
class BloodMatchRequest(BaseModel):
    recipient_blood_group: str = Field(description="A+, A-, B+, B-, AB+, AB-, O+, O-")
    city: str
    area: Optional[str] = None
    urgency: str = Field(default="Urgent", description="Emergency, Urgent, or Standard")
    only_available: bool = True


class MatchedDonor(BaseModel):
    donor_code: str
    full_name: str
    blood_group: str
    compatibility_reason: str
    city: str
    area: str
    full_address: str
    masked_contact: str
    raw_contact: Optional[str] = None  # Revealed only on explicit user click
    whatsapp_link: str
    availability_status: str
    last_donation_date: Optional[str] = None
    eligible_now: bool
    distance_rank: int


class BloodMatchResponse(BaseModel):
    recipient_group: str
    compatible_donor_groups: List[str]
    total_matches: int
    donors: List[MatchedDonor]


class DonorRegistrationRequest(BaseModel):
    full_name: str
    age: int = Field(ge=18, le=65)
    gender: str = Field(description="Male, Female, or Other")
    blood_group: str = Field(description="A+, A-, B+, B-, AB+, AB-, O+, O-")
    city: str
    area: Optional[str] = ""
    address: str
    contact_number: str
    availability: str = Field(default="Available")
    last_donation_date: Optional[str] = None
    email: Optional[str] = None
    medical_conditions: Optional[str] = None
    weight_kg: Optional[float] = None
    notes: Optional[str] = None


class BloodRequestCreate(BaseModel):
    patient_name: str
    blood_group_needed: str
    units_required: int = Field(default=1, ge=1, le=20)
    city: str
    hospital_name: str
    urgency_level: str = Field(default="Urgent")
    contact_person: str
    contact_phone: str


class BloodRequestResponse(BaseModel):
    id: str
    request_code: str
    patient_name: str
    blood_group_needed: str
    units_required: int
    city: str
    hospital_name: str
    urgency_level: str
    contact_person: str
    contact_phone: str
    request_status: str
    created_at: str


# ------------------------------------------------------------------------------
# 4. DOCTOR RAG SEARCH SCHEMAS
# ------------------------------------------------------------------------------
class DoctorSearchQuery(BaseModel):
    query: str = Field(description="Natural language query, e.g. 'Affordable child specialist in Lahore'")
    city: Optional[str] = None
    specialization: Optional[str] = None
    max_fee: Optional[int] = None
    min_experience_years: Optional[float] = None
    min_satisfaction_rate: Optional[float] = None
    limit: int = Field(default=6, ge=1, le=20)


class VerifiedDoctor(BaseModel):
    id: str
    doctor_name: str
    title_prefix: str
    city: str
    specialization_primary: str
    specializations: List[str]
    qualifications: str
    experience_years: float
    total_reviews: int
    patient_satisfaction_pct: float
    avg_time_to_patients_mins: int
    wait_time_mins: int
    hospital_name: Optional[str] = None
    hospital_address: Optional[str] = None
    profile_url: Optional[str] = None
    fee_pkr: int
    relevance_score: float = 1.0
    recommendation_reason: str


class DoctorSearchResponse(BaseModel):
    total_found: int
    query_interpreted: str
    applied_filters: Dict[str, Any]
    grounded_summary: str
    doctors: List[VerifiedDoctor]


class DoctorFilterMetaResponse(BaseModel):
    cities: List[str]
    specializations: List[str]
    total_doctors: int

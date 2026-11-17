import logging
from typing import List
import httpx
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.core.config import settings
from backend.models.schemas import (
    DoctorAssistantChatRequest,
    DoctorAssistantChatResponse,
    SystemHealthResponse,
    ReportExplanationResponse,
    DoctorSearchQuery,
    DoctorSearchResponse,
    DoctorFilterMetaResponse,
    BloodMatchRequest,
    BloodMatchResponse,
    DonorRegistrationRequest,
    BloodRequestCreate,
    BloodRequestResponse,
)
from backend.modules.report.explainer import ReportExplainerService
from backend.modules.donors.service import BloodDonorService
from backend.modules.doctors.synthesizer import DoctorRAGService
from backend.modules.doctors.gemini_client import call_gemini_chat
from backend.modules.doctors.nvidia_client import call_nvidia_chat
from backend.modules.doctors.openrouter_client import call_openrouter_chat

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


@router.post(
    "/rag/chat",
    response_model=DoctorAssistantChatResponse,
    tags=["Doctor RAG"],
)
async def rag_chat_endpoint(request: DoctorAssistantChatRequest):
    """Forward user query to NVIDIA NIM, with Gemini and OpenRouter as fallbacks.
    This endpoint is used by the floating chat button in the UI.
    """
    if not settings.NVIDIA_NIMS_API_KEY and not settings.GEMINI_API_KEY and not settings.OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI chat is not configured. Set NVIDIA_NIMS_API_KEY, GEMINI_API_KEY, or OPENROUTER_API_KEY in backend/.env.",
        )

    # 1. Try NVIDIA NIM
    if settings.NVIDIA_NIMS_API_KEY:
        try:
            return DoctorAssistantChatResponse(
                reply=await call_nvidia_chat(request.user_message)
            )
        except Exception as nvidia_error:
            status_code = (
                nvidia_error.response.status_code
                if isinstance(nvidia_error, httpx.HTTPStatusError)
                else None
            )
            logger.warning(
                "NVIDIA chat provider failed (%s, HTTP %s); trying Gemini fallback",
                type(nvidia_error).__name__,
                status_code or "n/a",
            )

    # 2. Try Gemini
    if settings.GEMINI_API_KEY:
        try:
            return DoctorAssistantChatResponse(
                reply=await call_gemini_chat(request.user_message)
            )
        except Exception as gemini_error:
            status_code = getattr(gemini_error, "code", None) or getattr(
                gemini_error, "status_code", None
            )
            logger.warning(
                "Gemini chat fallback failed (%s, HTTP %s); trying OpenRouter fallback",
                type(gemini_error).__name__,
                status_code or "n/a",
            )
    else:
        logger.warning(
            "Gemini chat fallback is not configured; set GEMINI_API_KEY in backend/.env"
        )

    # 3. Try OpenRouter
    if settings.OPENROUTER_API_KEY:
        try:
            return DoctorAssistantChatResponse(
                reply=await call_openrouter_chat(request.user_message)
            )
        except Exception as openrouter_error:
            logger.warning(
                "OpenRouter chat fallback failed (%s)",
                type(openrouter_error).__name__,
            )
    else:
        logger.warning(
            "OpenRouter chat fallback is not configured; set OPENROUTER_API_KEY in backend/.env"
        )

    raise HTTPException(
        status_code=503,
        detail="The AI assistant is temporarily unavailable. Check backend provider logs and try again.",
    )

@router.get("/health", response_model=SystemHealthResponse, tags=["Health"])
def get_system_health():
    """
    Returns system status, Supabase configuration readiness, and AI service status.
    """
    missing = settings.validate_runtime_credentials()
    return SystemHealthResponse(
        status="HEALTHY" if not missing else "CONFIG_REQUIRED",
        version="2.0.0",
        supabase_configured=bool(settings.SUPABASE_URL and "your-project" not in settings.SUPABASE_URL),
        gemini_configured=bool(settings.GEMINI_API_KEY and "your-gemini" not in settings.GEMINI_API_KEY),
        missing_configurations=missing
    )


# ------------------------------------------------------------------------------
# 2. MEDICAL REPORT EXPLAINER
# ------------------------------------------------------------------------------
@router.post("/reports/explain", response_model=ReportExplanationResponse, tags=["Medical AI Explainer"])
async def explain_medical_report(
    file: UploadFile = File(...),
    language: str = Form("en"),
    disclaimer_accepted: bool = Form(True)
):
    """
    Upload a medical laboratory report (PDF, PNG, JPG, WebP) to receive a
    structured biomarker extraction and patient-friendly layman explanation in EN or UR.
    """
    if not disclaimer_accepted:
        raise HTTPException(
            status_code=400,
            detail="The mandatory medical disclaimer must be acknowledged before analyzing reports."
        )

    allowed_exts = (".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt")
    if not any(file.filename.lower().endswith(ext) for ext in allowed_exts):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Please upload one of: {', '.join(allowed_exts)}"
        )

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum 10MB limit.")

    try:
        response = ReportExplainerService.process_and_explain(
            file_bytes=file_bytes,
            filename=file.filename,
            language=language
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Medical report analysis error: {str(e)}")


# ------------------------------------------------------------------------------
# 3. DOCTOR FINDER USING GROUNDED RAG
# ------------------------------------------------------------------------------
@router.post("/doctors/search", response_model=DoctorSearchResponse, tags=["Doctor RAG"])
def search_doctors(query: DoctorSearchQuery):
    """
    Executes hybrid retrieval across the 2,652 verified doctor dataset.
    Never hallucinates or fabricates doctors.
    """
    try:
        return DoctorRAGService.search(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Doctor search retrieval error: {str(e)}")


@router.get("/doctors/filters/meta", response_model=DoctorFilterMetaResponse, tags=["Doctor RAG"])
def get_doctor_filter_meta():
    """
    Returns unique cities and specialties for UI filter dropdowns.
    """
    return DoctorRAGService.get_filter_meta()


# ------------------------------------------------------------------------------
# 4. BLOOD DONOR MATCHING & REGISTRATION
# ------------------------------------------------------------------------------
@router.post("/blood/match", response_model=BloodMatchResponse, tags=["Blood Donor Network"])
def match_blood_donors(request: BloodMatchRequest):
    """
    Finds compatible voluntary donors according to ABO/Rh transfusion rules
    and proximity ranking (City + Area > City > Other).
    """
    try:
        return BloodDonorService.match_donors(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blood donor matching error: {str(e)}")


@router.post("/blood/donors/register", tags=["Blood Donor Network"])
def register_donor(data: DonorRegistrationRequest):
    """
    Enrolls a community member into the voluntary donor registry.
    """
    try:
        res = BloodDonorService.register_donor(data)
        return {
            "success": True,
            "message": "Donor registered successfully and saved to the temporary donor registry sheet.",
            "data": res,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Donor registration error: {str(e)}")


@router.post("/blood/requests", response_model=BloodRequestResponse, tags=["Blood Donor Network"])
def broadcast_blood_request(data: BloodRequestCreate):
    """
    Broadcasts an urgent blood requirement for patient transfusion.
    """
    try:
        return BloodDonorService.create_blood_request(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blood request creation error: {str(e)}")


@router.get("/blood/requests", response_model=List[BloodRequestResponse], tags=["Blood Donor Network"])
def list_blood_requests():
    """
    Lists open emergency blood requests.
    """
    return BloodDonorService.list_blood_requests()

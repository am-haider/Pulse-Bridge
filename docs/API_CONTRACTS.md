# PULSE BRIDGE — API CONTRACT SPECIFICATION
**Version:** 2.0.0-APPROVED-FASTAPI-NEXTJS  
**Author:** Chief Architect & Technical Project Manager  
**Backend:** FastAPI (Python 3.13)  
**Frontend Consumer:** Next.js 14 (TypeScript App Router)  
**Base URL:** `http://localhost:8000/api/v1`  

---

## 1. Authentication & Security Headers

All requests originating from the Next.js frontend to protected backend routes pass the Supabase session JWT:
```http
Authorization: Bearer <supabase_access_token>
Content-Type: application/json
```
For public endpoints (`/api/v1/health`, public doctor search, public blood match), the `Authorization` header is optional.

CORS is strictly configured for `http://localhost:3000` (Next.js development) and production frontend domains.

---

## 2. API Endpoints Overview

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/health` | Service health, Supabase status & Gemini readiness | No |
| `POST` | `/api/v1/rag/chat` | Doctor Assistant chat (NVIDIA NIM, Gemini fallback) | No |
| `POST` | `/api/v1/reports/explain` | Multipart upload (PDF/Image) for bilingual AI breakdown | Optional (Saves to user profile if authed) |
| `GET` | `/api/v1/reports/history` | Fetches authenticated user's past explained reports | Yes |
| `POST` | `/api/v1/doctors/search` | Grounded hybrid semantic & structured doctor search | No |
| `GET` | `/api/v1/doctors/{id}` | Full profile for a verified doctor | No |
| `GET` | `/api/v1/doctors/filters/meta` | Unique cities and specialties for UI dropdowns | No |
| `POST` | `/api/v1/blood/match` | Compatibility & proximity emergency donor search | No |
| `POST` | `/api/v1/blood/donors/register` | Register as a voluntary donor | Optional (Links to profile if authed) |
| `POST` | `/api/v1/blood/requests` | Broadcast urgent blood requirement | Optional |
| `GET` | `/api/v1/blood/requests` | List active emergency blood broadcasts | No |

---

## 3. Pydantic Models & Endpoint Specifications

### 3.1 Health Check
#### `GET /api/v1/health`
```json
{
  "status": "HEALTHY",
  "version": "2.0.0",
  "supabase": {
    "connected": true,
    "url": "https://xyzcompany.supabase.co"
  },
  "ai": {
    "gemini": "READY",
    "embeddings": "READY"
  }
}
```

### Doctor Assistant Chat
#### `POST /api/v1/rag/chat`
- Content-Type: `application/json`
- `user_message`: required, trimmed string from 1 to 4,000 characters
- Provider configuration: set `NVIDIA_NIMS_API_KEY` and/or `GEMINI_API_KEY` in `backend/.env`
- NVIDIA uses `NVIDIA_NIMS_CHAT_MODEL` (defaults to `deepseek-ai/deepseek-v4.1-flash`); Gemini is used if NVIDIA is unavailable.

**Request:**
```json
{
  "user_message": "Can you explain what a blood test measures?"
}
```

**Success response:**
```json
{
  "reply": "..."
}
```

Invalid messages return `422`; if all configured providers fail, the service returns `503`.

### 3.2 Medical Report Explainer
#### `POST /api/v1/reports/explain`
- Content-Type: `multipart/form-data`
- Form fields:
  - `file`: UploadFile (PDF, PNG, JPG; max 10MB)
  - `language`: `en` or `ur` (default `en`)
  - `disclaimer_accepted`: bool (must be `true`)

**Response Payload (`ReportExplanationResponse`):**
```json
{
  "id": "c1f7b764-6d93-4e31-9964-b81b853514a1",
  "report_title": "Complete Blood Count (CBC)",
  "language": "en",
  "biomarkers": [
    {
      "name": "Hemoglobin",
      "observed_value": "9.5 g/dL",
      "reference_range": "12.0 - 15.5 g/dL",
      "status": "LOW",
      "clinical_note_layman": "Carries oxygen throughout your body via red blood cells."
    },
    {
      "name": "Platelet Count",
      "observed_value": "240,000 /uL",
      "reference_range": "150,000 - 450,000 /uL",
      "status": "NORMAL",
      "clinical_note_layman": "Helps blood clot properly to stop bleeding."
    }
  ],
  "abnormal_findings_summary": "Hemoglobin is below typical range, which may explain sensations of fatigue or weakness.",
  "overall_health_insight": "Most cellular blood counts are healthy. Mildly reduced hemoglobin indicates potential iron or nutritional anemia.",
  "suggested_questions_for_doctor": [
    "Should we evaluate serum ferritin or vitamin levels?",
    "Do you recommend dietary adjustments or specific iron supplementation?"
  ],
  "mandatory_disclaimer": "CRITICAL: This AI analysis is purely for educational health literacy. It does NOT diagnose conditions or prescribe medications. Please consult your physician."
}
```

### 3.3 Doctor Search (Grounded RAG)
#### `POST /api/v1/doctors/search`
**Request Body (`DoctorSearchQuery`):**
```json
{
  "query": "Affordable child specialist in Lahore",
  "city": "Lahore",
  "specialization": "Pediatrician",
  "max_fee": 2000,
  "min_experience_years": 5,
  "limit": 5
}
```

**Response Payload (`DoctorSearchResponse`):**
```json
{
  "total_found": 3,
  "query_interpreted": "Pediatrician in Lahore with consultation fee under 2,000 PKR",
  "grounded_summary": "Retrieved 3 verified pediatricians in Lahore within your budget.",
  "doctors": [
    {
      "id": "f8a129d3-579c-4eb2-a6b4-2b721867c4d1",
      "doctor_name": "Dr. Muhammad Usman",
      "title_prefix": "Dr.",
      "city": "Lahore",
      "specialization_primary": "Pediatrician",
      "specializations": ["Pediatrician", "Neonatologist"],
      "qualifications": "MBBS, FCPS (Pediatrics)",
      "experience_years": 14.0,
      "total_reviews": 312,
      "patient_satisfaction_pct": 98.0,
      "avg_time_to_patients_mins": 15,
      "wait_time_mins": 10,
      "hospital_name": "Children Hospital Lahore",
      "hospital_address": "Ferozepur Road, Lahore",
      "profile_url": "https://www.marham.pk/doctors/lahore/pediatrician/dr-muhammad-usman",
      "fee_pkr": 1500,
      "relevance_score": 0.95,
      "recommendation_reason": "Top rated pediatrician in Lahore with 14 years clinical experience within your 2000 PKR budget."
    }
  ]
}
```

### 3.4 Blood Matching & Registration
#### `POST /api/v1/blood/match`
**Request Body (`BloodMatchRequest`):**
```json
{
  "recipient_blood_group": "A+",
  "city": "Lahore",
  "area": "Gulberg",
  "urgency": "Emergency",
  "only_available": true
}
```

**Response Payload (`BloodMatchResponse`):**
```json
{
  "recipient_group": "A+",
  "compatible_donor_groups": ["A+", "A-", "O+", "O-"],
  "total_matches": 6,
  "donors": [
    {
      "donor_code": "PKD0014",
      "full_name": "Zubair Ali",
      "blood_group": "O+",
      "city": "Lahore",
      "area": "Gulberg III",
      "masked_contact": "+92 300 ••••• 89",
      "whatsapp_link": "https://wa.me/923001234589?text=URGENT%3A%20Emergency%20blood%20request%20via%20Pulse%20Bridge",
      "availability_status": "Available",
      "distance_priority": 1,
      "eligible_now": true
    }
  ]
}
```

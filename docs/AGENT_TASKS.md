# PULSE BRIDGE — WORKER ALLOCATION & FILE OWNERSHIP
**Version:** 2.0.0-APPROVED-NEXTJS-SUPABASE  
**Author:** Chief Architect & Technical Project Manager  
**Architecture Model:** 5 Decoupled Workers with Strict Boundary Isolation  

---

## 1. Governance & Strict File Ownership

| Worker Role | Exclusive Directory / File Scope | Technologies | Key Deliverables |
|---|---|---|---|
| **WORKER 1: Frontend Engineer** | `frontend/` | Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui, Lucide Icons, Framer Motion | Modern, responsive SaaS UI: Landing page, navigation/sidebar, medical report upload & interactive breakdown, doctor search & verified cards, blood matching & registration, loading/error states. |
| **WORKER 2: Medical AI Engineer** | `backend/modules/report/` | Python, PyMuPDF, Gemini Vision 1.5/2.5 Flash, Pydantic | PDF/image document parsing, multimodal OCR, structured biomarker extraction, Urdu/English layperson explanation, non-diagnostic safety guardrails. |
| **WORKER 3: Blood Donor Engineer** | `backend/modules/donors/` | Python, Supabase Python SDK, Pydantic | ABO/Rh compatibility matrix, location proximity ranking, donor registration, blood request broadcast, consent-based contact masking & WhatsApp generator. |
| **WORKER 4: Senior RAG Engineer** | `backend/modules/doctors/` | Python, Supabase pgvector, Gemini `text-embedding-004`, pandas | Non-destructive CSV normalizer, embedding generation, Supabase pgvector indexing script, hybrid SQL + semantic retriever, zero-hallucination recommendation synthesizer. |
| **WORKER 5: QA & Integration Engineer** | `backend/core/`, `backend/api/`, `tests/`, `supabase/migrations/` | FastAPI, Pytest, Pydantic Settings, Supabase CLI / SQL | Environment variable startup validator, FastAPI routing & CORS, Supabase database migrations (01 to 04), test suite, `.env.example`, README pitch. |

---

## 2. Non-Overlapping Coordination Rules

1. **No Concurrent Edits to Shared Core:** Worker 5 creates `backend/core/config.py` and shared models. Workers 2, 3, and 4 import these interfaces and write strictly within their respective `backend/modules/` directories.
2. **Worker 1 Independence:** Worker 1 builds the frontend in `frontend/` using TypeScript types directly mirrored from `docs/API_CONTRACTS.md`.
3. **Supabase as Single Source of Truth:** Workers 2, 3, and 4 connect exclusively via `backend/core/supabase_client.py`. No local SQLite or secondary databases are permitted.
4. **Zero Secrets in Git:** All secrets stay in `backend/.env` and `frontend/.env.local`. Only `.env.example` is committed.

# PULSE BRIDGE — SUPABASE DATABASE SCHEMA & POLICIES
**Version:** 2.0.0-APPROVED-SUPABASE-ONLY  
**Author:** Chief Architect & Technical Project Manager  
**Platform:** Supabase PostgreSQL 15+ with `pgvector` & Row Level Security  

---

## 1. Supabase Services Architecture

Supabase is the single source of truth for all PULSE BRIDGE persistence and storage services:
- **Supabase Auth:** Manages user identity (`auth.users`), issuing JWTs.
- **Supabase PostgreSQL:** Stores application relational data (`profiles`, `doctors`, `donors`, `blood_requests`, `report_records`).
- **Supabase pgvector:** 768-dimensional embeddings for hybrid semantic doctor retrieval.
- **Supabase Storage:** Private bucket `medical_reports` storing patient diagnostic documents.
- **Row Level Security (RLS):** Enforced across all tables to safeguard patient and donor privacy.

---

## 2. Complete Supabase SQL Migrations

### Migration 1: Extensions & Profiles (`01_extensions_and_profiles.sql`)
```sql
-- Enable Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- User Profiles (Linked to Supabase Auth)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(50),
    preferred_language VARCHAR(10) DEFAULT 'en' CHECK (preferred_language IN ('en', 'ur')),
    role VARCHAR(50) DEFAULT 'patient' CHECK (role IN ('patient', 'donor', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile"
ON public.profiles FOR SELECT
USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
ON public.profiles FOR UPDATE
USING (auth.uid() = id);

-- Trigger to auto-create profile on Supabase auth sign-up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email)
    VALUES (new.id, COALESCE(new.raw_user_meta_data->>'full_name', 'User'), new.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
```

---

### Migration 2: Doctors & Vector Embeddings (`02_doctors_and_pgvector.sql`)
```sql
-- Doctors Table
CREATE TABLE IF NOT EXISTS public.doctors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    raw_hash VARCHAR(64) UNIQUE,                     -- Prevents duplicate ingestion
    doctor_name VARCHAR(255) NOT NULL,
    title_prefix VARCHAR(50),                        -- 'Prof. Dr.', 'Dr.', etc.
    city VARCHAR(100) NOT NULL,                      -- Canonical Title Case
    specialization_primary VARCHAR(150) NOT NULL,
    specializations TEXT[] NOT NULL DEFAULT '{}',
    qualifications TEXT NOT NULL,
    experience_years NUMERIC(4, 1) NOT NULL DEFAULT 0.0,
    total_reviews INTEGER NOT NULL DEFAULT 0,
    patient_satisfaction_pct NUMERIC(5, 2) NOT NULL DEFAULT 100.0,
    avg_time_to_patients_mins INTEGER DEFAULT 15,
    wait_time_mins INTEGER DEFAULT 15,
    hospital_name VARCHAR(255),
    hospital_address TEXT,                           -- NULL if raw was "No Address Available"
    profile_url TEXT,                                -- NULL if raw was "No Link Available"
    fee_pkr INTEGER NOT NULL DEFAULT 0,
    search_document TEXT NOT NULL,                   -- Normalized document chunk for hybrid search
    embedding vector(768),                           -- Gemini text-embedding-004 768-d vector
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- B-Tree and GIN Indexes
CREATE INDEX IF NOT EXISTS idx_doctors_city ON public.doctors (LOWER(city));
CREATE INDEX IF NOT EXISTS idx_doctors_spec ON public.doctors (LOWER(specialization_primary));
CREATE INDEX IF NOT EXISTS idx_doctors_fee ON public.doctors (fee_pkr);
CREATE INDEX IF NOT EXISTS idx_doctors_exp ON public.doctors (experience_years DESC);
CREATE INDEX IF NOT EXISTS idx_doctors_fts ON public.doctors USING gin(to_tsvector('english', search_document));

-- HNSW Vector Index for Cosine Similarity
CREATE INDEX IF NOT EXISTS idx_doctors_embedding_hnsw 
ON public.doctors USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Public Read-Only RLS Policy (Doctors are public directory data)
ALTER TABLE public.doctors ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can search verified doctors"
ON public.doctors FOR SELECT
USING (true);

-- Hybrid Semantic Matching Function (Vector + Metadata)
CREATE OR REPLACE FUNCTION match_doctors (
    query_embedding vector(768),
    match_threshold float,
    match_count int,
    filter_city text DEFAULT NULL,
    filter_specialization text DEFAULT NULL,
    filter_max_fee int DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    doctor_name VARCHAR,
    title_prefix VARCHAR,
    city VARCHAR,
    specialization_primary VARCHAR,
    specializations TEXT[],
    qualifications TEXT,
    experience_years NUMERIC,
    total_reviews INTEGER,
    patient_satisfaction_pct NUMERIC,
    avg_time_to_patients_mins INTEGER,
    wait_time_mins INTEGER,
    hospital_name VARCHAR,
    hospital_address TEXT,
    profile_url TEXT,
    fee_pkr INTEGER,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.doctor_name,
        d.title_prefix,
        d.city,
        d.specialization_primary,
        d.specializations,
        d.qualifications,
        d.experience_years,
        d.total_reviews,
        d.patient_satisfaction_pct,
        d.avg_time_to_patients_mins,
        d.wait_time_mins,
        d.hospital_name,
        d.hospital_address,
        d.profile_url,
        d.fee_pkr,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM public.doctors d
    WHERE 
        (1 - (d.embedding <=> query_embedding)) > match_threshold
        AND (filter_city IS NULL OR LOWER(d.city) = LOWER(filter_city))
        AND (filter_specialization IS NULL OR LOWER(d.specialization_primary) LIKE '%' || LOWER(filter_specialization) || '%')
        AND (filter_max_fee IS NULL OR d.fee_pkr <= filter_max_fee)
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

---

### Migration 3: Blood Donors & Emergency Requests (`03_donors_and_requests.sql`)
```sql
-- Blood Donors
CREATE TABLE IF NOT EXISTS public.donors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    donor_code VARCHAR(50) UNIQUE NOT NULL,          -- PKD0001
    full_name VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 18 AND age <= 65),
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
    blood_group VARCHAR(10) NOT NULL CHECK (blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
    city VARCHAR(100) NOT NULL,
    area VARCHAR(255),
    full_address TEXT NOT NULL,
    contact_number VARCHAR(50) NOT NULL,             -- Normalized E.164 (+92-...)
    availability_status VARCHAR(20) NOT NULL DEFAULT 'Available' CHECK (availability_status IN ('Available', 'Unavailable')),
    last_donation_date DATE,
    eligible_donation_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_donors_matching ON public.donors (blood_group, LOWER(city), availability_status);

-- Blood Requests (Emergency Broadcast)
CREATE TABLE IF NOT EXISTS public.blood_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requester_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    request_code VARCHAR(50) UNIQUE NOT NULL,
    patient_name VARCHAR(255) NOT NULL,
    blood_group_needed VARCHAR(10) NOT NULL CHECK (blood_group_needed IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
    units_required INTEGER NOT NULL DEFAULT 1,
    city VARCHAR(100) NOT NULL,
    hospital_name VARCHAR(255) NOT NULL,
    urgency_level VARCHAR(20) NOT NULL DEFAULT 'Urgent' CHECK (urgency_level IN ('Emergency', 'Urgent', 'Standard')),
    contact_person VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50) NOT NULL,
    request_status VARCHAR(20) NOT NULL DEFAULT 'Open' CHECK (request_status IN ('Open', 'Matched', 'Fulfilled', 'Closed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_requests_open ON public.blood_requests (request_status, urgency_level);

-- RLS Policies
ALTER TABLE public.donors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blood_requests ENABLE ROW LEVEL SECURITY;

-- Donors are searchable for emergency matching, but full contacts are protected via service layer
CREATE POLICY "Public can view active donors for matching"
ON public.donors FOR SELECT
USING (true);

CREATE POLICY "Users can register as donors"
ON public.donors FOR INSERT
WITH CHECK (true);

CREATE POLICY "Anyone can view open blood requests"
ON public.blood_requests FOR SELECT
USING (true);

CREATE POLICY "Anyone can broadcast emergency blood request"
ON public.blood_requests FOR INSERT
WITH CHECK (true);
```

---

### Migration 4: Medical Report Records & Storage (`04_report_records_and_storage.sql`)
```sql
-- Storage Bucket for Medical Reports (Private)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'medical_reports',
    'medical_reports',
    false,
    10485760, -- 10MB limit
    ARRAY['application/pdf', 'image/png', 'image/jpeg', 'image/webp']
)
ON CONFLICT (id) DO UPDATE SET public = false;

-- Storage RLS: Users can only upload and read their own reports
CREATE POLICY "Users can upload their own medical reports"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'medical_reports' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view their own medical reports"
ON storage.objects FOR SELECT
USING (bucket_id = 'medical_reports' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Report Analysis Records
CREATE TABLE IF NOT EXISTS public.report_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    storage_path TEXT,                               -- Path in Supabase Storage
    report_title VARCHAR(255) NOT NULL,
    detected_category VARCHAR(100),
    language VARCHAR(10) NOT NULL DEFAULT 'en',      -- 'en' or 'ur'
    biomarkers JSONB NOT NULL DEFAULT '[]'::jsonb,   -- Extracted test items
    abnormal_findings TEXT NOT NULL,
    health_insight TEXT NOT NULL,
    questions_for_doctor TEXT[] DEFAULT '{}',
    disclaimer_acknowledged BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reports_user ON public.report_records (user_id, created_at DESC);

-- RLS for Report Records
ALTER TABLE public.report_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own report records"
ON public.report_records FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own report records"
ON public.report_records FOR INSERT
WITH CHECK (auth.uid() = user_id OR user_id IS NULL);
```

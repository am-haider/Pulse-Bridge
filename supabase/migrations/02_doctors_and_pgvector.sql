-- ==============================================================================
-- MIGRATION 02: DOCTORS DIRECTORY AND PGVECTOR EMBEDDINGS
-- Description: Creates verified doctors table, indexes, and hybrid RAG search
--              function using Supabase pgvector.
-- ==============================================================================

-- 1. Create Doctors Table
CREATE TABLE IF NOT EXISTS public.doctors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    raw_hash VARCHAR(64) UNIQUE,                     -- SHA256(Name + City + Hospital) prevents duplicate insertion
    doctor_name VARCHAR(255) NOT NULL,
    title_prefix VARCHAR(50),                        -- 'Prof. Dr.', 'Dr.', etc.
    city VARCHAR(100) NOT NULL,                      -- Normalized Title Case (e.g. 'Lahore')
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
    search_document TEXT NOT NULL,                   -- Normalized textual chunk for hybrid keyword matching
    embedding vector(768),                           -- Gemini text-embedding-004 768-dimensional vector
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Indexes for Ultra-Fast Structured Filtering
CREATE INDEX IF NOT EXISTS idx_doctors_city ON public.doctors (LOWER(city));
CREATE INDEX IF NOT EXISTS idx_doctors_spec ON public.doctors (LOWER(specialization_primary));
CREATE INDEX IF NOT EXISTS idx_doctors_fee ON public.doctors (fee_pkr);
CREATE INDEX IF NOT EXISTS idx_doctors_exp ON public.doctors (experience_years DESC);
CREATE INDEX IF NOT EXISTS idx_doctors_satisfaction ON public.doctors (patient_satisfaction_pct DESC);
CREATE INDEX IF NOT EXISTS idx_doctors_fts ON public.doctors USING gin(to_tsvector('english', search_document));

-- 3. HNSW Vector Index for Cosine Distance Nearest-Neighbor Search
CREATE INDEX IF NOT EXISTS idx_doctors_embedding_hnsw 
ON public.doctors USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 4. Row Level Security: Public Read-Only for Doctor Directory
ALTER TABLE public.doctors ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read-only for verified doctors"
ON public.doctors FOR SELECT
USING (true);

-- 5. Hybrid Semantic + Metadata Matching Function (PostgreSQL Stored Procedure)
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
        (d.embedding IS NOT NULL)
        AND (1 - (d.embedding <=> query_embedding)) > match_threshold
        AND (filter_city IS NULL OR LOWER(d.city) = LOWER(filter_city))
        AND (filter_specialization IS NULL OR LOWER(d.specialization_primary) LIKE '%' || LOWER(filter_specialization) || '%')
        AND (filter_max_fee IS NULL OR d.fee_pkr <= filter_max_fee)
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

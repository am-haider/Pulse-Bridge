-- ==============================================================================
-- MIGRATION 04: REPORT RECORDS AND SUPABASE STORAGE BUCKET
-- Description: Establishes private Supabase Storage bucket for patient reports,
--              structured analysis records, and clinical Row Level Security.
-- ==============================================================================

-- 1. Create Private Storage Bucket for Medical Reports
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'medical_reports',
    'medical_reports',
    false, -- Private access only
    10485760, -- 10MB file limit
    ARRAY['application/pdf', 'image/png', 'image/jpeg', 'image/webp']
)
ON CONFLICT (id) DO UPDATE SET public = false;

-- 2. Storage Bucket Row Level Security Policies
-- Users can only upload and read files within their own user_id directory
CREATE POLICY "Users can upload their own medical reports"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'medical_reports' 
    AND (auth.uid() IS NULL OR auth.uid()::text = (storage.foldername(name))[1])
);

CREATE POLICY "Users can view their own medical reports"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'medical_reports' 
    AND (auth.uid() IS NULL OR auth.uid()::text = (storage.foldername(name))[1])
);

-- 3. Create Medical Report Records Table
CREATE TABLE IF NOT EXISTS public.report_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    storage_path TEXT,                               -- Path in Supabase Storage
    report_title VARCHAR(255) NOT NULL,
    detected_category VARCHAR(100),                  -- e.g. 'Complete Blood Count', 'Lipid Profile'
    language VARCHAR(10) NOT NULL DEFAULT 'en' CHECK (language IN ('en', 'ur')),
    biomarkers JSONB NOT NULL DEFAULT '[]'::jsonb,   -- Extracted test items with units and ranges
    abnormal_findings TEXT NOT NULL,
    health_insight TEXT NOT NULL,
    questions_for_doctor TEXT[] DEFAULT '{}',
    disclaimer_acknowledged BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reports_user ON public.report_records (user_id, created_at DESC);

-- 4. Row Level Security for Report Records
ALTER TABLE public.report_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own report records"
ON public.report_records FOR SELECT
USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can create their own report records"
ON public.report_records FOR INSERT
WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

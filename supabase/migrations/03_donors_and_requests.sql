-- ==============================================================================
-- MIGRATION 03: BLOOD DONORS AND EMERGENCY BLOOD REQUESTS
-- Description: Creates voluntary blood donors registry, emergency broadcast
--              requests, indexes, and Row Level Security.
-- ==============================================================================

-- 1. Create Voluntary Blood Donors Table
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
    eligible_donation_date DATE,                     -- Typically last_donation_date + 90 days
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for Rapid Emergency Compatibility Matching
CREATE INDEX IF NOT EXISTS idx_donors_match ON public.donors (blood_group, LOWER(city), availability_status);

-- 2. Create Emergency Blood Requests Table
CREATE TABLE IF NOT EXISTS public.blood_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requester_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    request_code VARCHAR(50) UNIQUE NOT NULL,
    patient_name VARCHAR(255) NOT NULL,
    blood_group_needed VARCHAR(10) NOT NULL CHECK (blood_group_needed IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
    units_required INTEGER NOT NULL DEFAULT 1 CHECK (units_required >= 1 AND units_required <= 20),
    city VARCHAR(100) NOT NULL,
    hospital_name VARCHAR(255) NOT NULL,
    urgency_level VARCHAR(20) NOT NULL DEFAULT 'Urgent' CHECK (urgency_level IN ('Emergency', 'Urgent', 'Standard')),
    contact_person VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50) NOT NULL,
    request_status VARCHAR(20) NOT NULL DEFAULT 'Open' CHECK (request_status IN ('Open', 'Matched', 'Fulfilled', 'Closed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_requests_open ON public.blood_requests (request_status, urgency_level);

-- 3. Row Level Security Policies
ALTER TABLE public.donors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blood_requests ENABLE ROW LEVEL SECURITY;

-- Donors are searchable for emergency matching
CREATE POLICY "Public can view active donors for matching"
ON public.donors FOR SELECT
USING (true);

-- Anyone can register as a voluntary donor
CREATE POLICY "Anyone can register as a voluntary donor"
ON public.donors FOR INSERT
WITH CHECK (true);

-- Donors can update their own profile / availability
CREATE POLICY "Donors can update their availability"
ON public.donors FOR UPDATE
USING (auth.uid() = user_id);

-- Blood requests are publicly viewable for emergency mobilization
CREATE POLICY "Public can view open blood requests"
ON public.blood_requests FOR SELECT
USING (true);

-- Anyone can broadcast an emergency request
CREATE POLICY "Anyone can create emergency blood requests"
ON public.blood_requests FOR INSERT
WITH CHECK (true);

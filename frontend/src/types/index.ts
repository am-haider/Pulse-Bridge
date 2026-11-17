export type Language = 'en' | 'ur';

export type BiomarkerStatus = 'NORMAL' | 'LOW' | 'ELEVATED' | 'INDETERMINATE';

export interface BiomarkerItem {
  name: string;
  observed_value: string;
  reference_range: string;
  status: BiomarkerStatus;
  clinical_note_layman: string;
}

export interface ReportExplanationResponse {
  id?: string;
  report_title: string;
  detected_category: string;
  language: Language;
  biomarkers: BiomarkerItem[];
  abnormal_findings_summary: string;
  overall_health_insight: string;
  suggested_questions_for_doctor: string[];
  dietary_lifestyle_considerations: string[];
  mandatory_disclaimer: string;
}

export interface VerifiedDoctor {
  id: string;
  doctor_name: string;
  title_prefix: string;
  city: string;
  specialization_primary: string;
  specializations: string[];
  qualifications: string;
  experience_years: number;
  total_reviews: number;
  patient_satisfaction_pct: number;
  avg_time_to_patients_mins: number;
  wait_time_mins: number;
  hospital_name?: string | null;
  hospital_address?: string | null;
  profile_url?: string | null;
  fee_pkr: number;
  relevance_score: number;
  recommendation_reason: string;
}

export interface DoctorSearchQuery {
  query: string;
  city?: string;
  specialization?: string;
  max_fee?: number;
  min_experience_years?: number;
  min_satisfaction_rate?: number;
  limit?: number;
}

export interface DoctorSearchResponse {
  total_found: number;
  query_interpreted: string;
  applied_filters: Record<string, unknown>;
  grounded_summary: string;
  doctors: VerifiedDoctor[];
}

export interface DoctorFilterMetaResponse {
  cities: string[];
  specializations: string[];
  total_doctors: number;
}

export interface MatchedDonor {
  donor_code: string;
  full_name: string;
  blood_group: string;
  compatibility_reason: string;
  city: string;
  area: string;
  full_address: string;
  masked_contact: string;
  raw_contact?: string;
  whatsapp_link: string;
  availability_status: string;
  last_donation_date?: string | null;
  eligible_now: boolean;
  distance_rank: number;
}

export interface BloodMatchRequest {
  recipient_blood_group: string;
  city: string;
  area?: string;
  urgency?: string;
  only_available?: boolean;
}

export interface BloodMatchResponse {
  recipient_group: string;
  compatible_donor_groups: string[];
  total_matches: number;
  donors: MatchedDonor[];
}

export interface DonorRegistrationRequest {
  full_name: string;
  age: number;
  gender: string;
  blood_group: string;
  city: string;
  area?: string;
  address: string;
  contact_number: string;
  availability?: string;
  last_donation_date?: string;
}

export interface BloodRequestCreate {
  patient_name: string;
  blood_group_needed: string;
  units_required: number;
  city: string;
  hospital_name: string;
  urgency_level: string;
  contact_person: string;
  contact_phone: string;
}

export interface BloodRequestResponse {
  id: string;
  request_code: string;
  patient_name: string;
  blood_group_needed: string;
  units_required: number;
  city: string;
  hospital_name: string;
  urgency_level: string;
  contact_person: string;
  contact_phone: string;
  request_status: string;
  created_at: string;
}

export interface SystemHealthResponse {
  status: string;
  version: string;
  supabase_configured: boolean;
  gemini_configured: boolean;
  missing_configurations: string[];
}

export interface DoctorAssistantChatResponse {
  reply: string;
}

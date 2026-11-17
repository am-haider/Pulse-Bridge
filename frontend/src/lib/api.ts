import {
  ReportExplanationResponse,
  DoctorSearchQuery,
  DoctorSearchResponse,
  DoctorFilterMetaResponse,
  BloodMatchRequest,
  BloodMatchResponse,
  DonorRegistrationRequest,
  BloodRequestCreate,
  BloodRequestResponse,
  SystemHealthResponse,
  DoctorAssistantChatResponse,
  Language,
} from '@/types';

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace(/\/+$/, '');
const CHAT_REQUEST_TIMEOUT_MS = 75_000;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

export async function checkHealth(): Promise<SystemHealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function chatWithDoctor(userMessage: string): Promise<DoctorAssistantChatResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), CHAT_REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch(`${API_BASE_URL}/rag/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_message: userMessage }),
      signal: controller.signal,
    });

    if (!res.ok) {
      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const errorBody: unknown = await res.json().catch(() => null);
        if (isRecord(errorBody) && typeof errorBody.detail === 'string') {
          throw new Error(errorBody.detail);
        }
      }
      throw new Error(
        `The backend returned an unexpected response (HTTP ${res.status}). Check the backend service and try again.`
      );
    }

    const responseBody: unknown = await res.json().catch(() => null);
    if (!isRecord(responseBody) || typeof responseBody.reply !== 'string' || !responseBody.reply.trim()) {
      throw new Error('The backend returned an invalid chat response. Please try again.');
    }
    return { reply: responseBody.reply.trim() };
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error('The AI assistant took too long to respond. Please try again.');
    }
    if (error instanceof TypeError) {
      throw new Error(
        `Could not connect to the backend at ${API_BASE_URL}. Check that the backend is running and NEXT_PUBLIC_API_URL is correct.`
      );
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function explainReport(file: File, language: Language = 'en'): Promise<ReportExplanationResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('language', language);
  formData.append('disclaimer_accepted', 'true');

  const res = await fetch(`${API_BASE_URL}/reports/explain`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to explain medical report');
  }

  return res.json();
}

export async function searchDoctors(query: DoctorSearchQuery): Promise<DoctorSearchResponse> {
  const res = await fetch(`${API_BASE_URL}/doctors/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(query),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to search verified doctors');
  }

  return res.json();
}

export async function getDoctorFilterMeta(): Promise<DoctorFilterMetaResponse> {
  const res = await fetch(`${API_BASE_URL}/doctors/filters/meta`, { cache: 'force-cache' });
  if (!res.ok) throw new Error('Failed to load doctor filter metadata');
  return res.json();
}

export async function matchBloodDonors(request: BloodMatchRequest): Promise<BloodMatchResponse> {
  const res = await fetch(`${API_BASE_URL}/blood/match`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to search blood donors');
  }

  return res.json();
}

export async function registerDonor(data: DonorRegistrationRequest): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/blood/donors/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to register blood donor');
  }

  return res.json();
}

export async function broadcastBloodRequest(data: BloodRequestCreate): Promise<BloodRequestResponse> {
  const res = await fetch(`${API_BASE_URL}/blood/requests`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to broadcast emergency blood request');
  }

  return res.json();
}

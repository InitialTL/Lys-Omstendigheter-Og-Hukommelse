import type { Language } from './i18n';
export type { Language } from './i18n';
export type Condition = 'WARM' | 'COOL' | 'DARK';
export type Phase = 'setup' | 'acclimation' | 'learning' | 'distraction' | 'recall';

export type Pair = { word: string; meaning: string };
export type ReviewItem = { word: string; answer: string; expected: string; correct: boolean };
export type RoundReview = {
  round_index: number; condition: Condition; score: number; max_score: number;
  math_attempts: number; math_correct: number; items: ReviewItem[];
};
export type StudyState = {
  participant_id: string;
  language: Language;
  group: string;
  completed: number;
  total: number;
  finished: boolean;
  server_now: number;
  round_index?: number;
  condition?: Condition;
  list_id?: number;
  phase?: Phase;
  phase_end_at?: number | null;
  words?: string[];
  pairs?: Pair[];
  review?: RoundReview[];
};

export type Registration = {
  language: Language;
  age_band: string;
  gender: string;
  consent: true;
};

export const COLORS: Record<Condition, string> = {
  WARM: '#D9AA91',
  COOL: '#9BB6E4',
  DARK: '#080B11',
};

const TOKEN_KEY = 'lm_v2_auth';
export function storeParticipantToken(token: string): void { localStorage.setItem(TOKEN_KEY, token); }
export function clearParticipantToken(): void { localStorage.removeItem(TOKEN_KEY); }
function authenticatedHeaders(): Record<string, string> {
  const token = localStorage.getItem(TOKEN_KEY);
  return token ? { 'X-Participant-Token': token } : {};
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    cache: 'no-store',
    referrerPolicy: 'no-referrer',
    headers: { ...(options?.body ? { 'Content-Type': 'application/json' } : {}), ...options?.headers },
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({})) as { detail?: string };
    throw new Error(detail.detail || `Serverfeil (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  register: (payload: Registration) => request<{ participant_id: string; group: string; access_token: string }>(
    '/api/participants', { method: 'POST', body: JSON.stringify(payload) }
  ),
  next: (id: string) => request<StudyState>(`/api/participants/${encodeURIComponent(id)}/next`, { headers: authenticatedHeaders() }),
  start: (id: string) => request<StudyState>(`/api/participants/${encodeURIComponent(id)}/rounds/start`, {
    method: 'POST', headers: authenticatedHeaders(),
  }),
  withdraw: async (id: string): Promise<void> => {
    const response = await fetch(`/api/participants/${encodeURIComponent(id)}`, { method: 'DELETE', cache: 'no-store', referrerPolicy: 'no-referrer', headers: authenticatedHeaders() });
    if (!response.ok) throw new Error(`Unable to withdraw (${response.status})`);
  },
  submit: (id: string, round: number, answers: string[], hidden_count: number, math_attempts: number, math_correct: number) =>
    request<{ saved: boolean }>(
      `/api/participants/${encodeURIComponent(id)}/rounds/${round}/submit`,
      { method: 'POST', body: JSON.stringify({ answers, hidden_count, math_attempts, math_correct }), headers: authenticatedHeaders() }
    ),
};

export type Language = 'nb' | 'en';
export type Condition = 'WARM' | 'COOL' | 'DARK';
export type Phase = 'setup' | 'learning' | 'distraction' | 'recall';

export type Pair = { word: string; meaning: string };
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

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: { ...(options?.body ? { 'Content-Type': 'application/json' } : {}), ...options?.headers },
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({})) as { detail?: string };
    throw new Error(detail.detail || `Serverfeil (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  register: (payload: Registration) => request<{ participant_id: string; group: string }>(
    '/api/participants', { method: 'POST', body: JSON.stringify(payload) }
  ),
  next: (id: string) => request<StudyState>(`/api/participants/${encodeURIComponent(id)}/next`),
  start: (id: string) => request<StudyState>(`/api/participants/${encodeURIComponent(id)}/rounds/start`, {
    method: 'POST',
  }),
  withdraw: async (id: string): Promise<void> => {
    const response = await fetch(`/api/participants/${encodeURIComponent(id)}`, { method: 'DELETE' });
    if (!response.ok) throw new Error(`Unable to withdraw (${response.status})`);
  },
  submit: (id: string, round: number, answers: string[], hidden_count: number) =>
    request<{ score: number; max_score: number; submitted_late: boolean }>(
      `/api/participants/${encodeURIComponent(id)}/rounds/${round}/submit`,
      { method: 'POST', body: JSON.stringify({ answers, hidden_count }) }
    ),
};

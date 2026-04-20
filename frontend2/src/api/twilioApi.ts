import twilioClient from './twilioClient';

// ── Types ──────────────────────────────────────────────────────────────────

export interface TwilioTarget {
  target_id: string;
  name: string;
  phone_no: string;
  roll_no: string | null;
  department: string | null;
  program: string | null;
  created_at: string;
}

export interface TwilioTargetCreate {
  name: string;
  phone_no: string;
  roll_no?: string;
  department?: string;
  program?: string;
}

export interface TwilioResponse {
  response_id: string;
  call_id: string;
  question_index: number;
  question_text: string;
  response_type: string;
  response_value: string | null;
  twilio_recording_url: string | null;
  minio_recording_url: string | null;
  recording_playback_url: string | null;
  response_label: string | null;
  recording_sid: string | null;
  recording_duration: number | null;
  analysis_score: number | null;
  responded_at: string;
}

export interface TwilioCall {
  call_id: string;
  twilio_call_sid: string | null;
  target_id: string;
  scheduled_time: string;
  started_time: string | null;
  ended_time: string | null;
  status: string;
  total_questions: number;
  questions_answered: number;
  overall_duration: number | null;
  total_response_duration: number | null;
  depression_risk: number | null;
  depression_risk_probability: number | null;
  depression_risk_level: string | null;
  depression_risk_confidence: number | null;
  depression_analysis_timestamp: string | null;
  created_at: string;
  responses: TwilioResponse[];
}

// ── Targets ────────────────────────────────────────────────────────────────

export async function fetchTwilioTargets(): Promise<TwilioTarget[]> {
  const res = await twilioClient.get<TwilioTarget[]>('/targets');
  return res.data;
}

export async function createTwilioTarget(body: TwilioTargetCreate): Promise<TwilioTarget> {
  const res = await twilioClient.post<TwilioTarget>('/targets', body);
  return res.data;
}

export async function deleteTwilioTarget(targetId: string): Promise<void> {
  await twilioClient.delete(`/targets/${targetId}`);
}

export async function bulkImportTwilioTargets(rows: TwilioTargetCreate[]): Promise<void> {
  for (const row of rows) {
    await createTwilioTarget(row);
  }
}

// ── Calls ──────────────────────────────────────────────────────────────────

export async function fetchCallsForTarget(targetId: string): Promise<TwilioCall[]> {
  const res = await twilioClient.get<TwilioCall[]>(`/targets/${targetId}/calls`);
  return res.data;
}

export async function initiateCallsBulk(targetIds: string[]): Promise<void> {
  await twilioClient.post('/calls/initiate-bulk', { target_ids: targetIds });
}

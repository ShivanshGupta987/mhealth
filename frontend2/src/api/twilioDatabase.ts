import twilioClient from './twilioClient';

// ── Types ──────────────────────────────────────────────────────────────────

export interface TwilioDbTarget {
  target_id: string;
  name: string;
  phone_no: string;
  roll_no: string | null;
  department: string | null;
  program: string | null;
  created_at: string;
}

export interface TwilioDbCall {
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
  responses: TwilioDbResponse[];
}

export interface TwilioDbResponse {
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

// ── Targets ────────────────────────────────────────────────────────────────

export async function twilioDB_listTargets(): Promise<TwilioDbTarget[]> {
  const res = await twilioClient.get<TwilioDbTarget[]>('/targets');
  return res.data;
}

export async function twilioDB_createTarget(body: {
  name: string;
  phone_no: string;
  roll_no?: string;
  department?: string;
  program?: string;
}): Promise<TwilioDbTarget> {
  const res = await twilioClient.post<TwilioDbTarget>('/targets', body);
  return res.data;
}

export async function twilioDB_deleteTarget(targetId: string): Promise<void> {
  await twilioClient.delete(`/targets/${targetId}`);
}

// ── Calls ──────────────────────────────────────────────────────────────────

export async function twilioDB_listCalls(): Promise<TwilioDbCall[]> {
  const res = await twilioClient.get<TwilioDbCall[]>('/calls');
  return res.data;
}

export async function twilioDB_deleteCall(callId: string): Promise<void> {
  await twilioClient.delete(`/calls/${callId}`);
}

// ── Responses ──────────────────────────────────────────────────────────────

export async function twilioDB_listResponses(): Promise<TwilioDbResponse[]> {
  const res = await twilioClient.get<TwilioDbResponse[]>('/responses');
  return res.data;
}

export async function twilioDB_deleteResponse(responseId: string): Promise<void> {
  await twilioClient.delete(`/responses/${responseId}`);
}

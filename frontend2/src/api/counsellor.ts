import { z } from 'zod';
import apiClient from './client';

const TargetSchema = z.object({
  Target_Id: z.string(),
  Name: z.string().nullable().optional(),
  Roll_No: z.string().nullable().optional(),
  Phone_No: z.string().nullable().optional(),
  Department_Name: z.string().nullable().optional(),
  Program: z.string().nullable().optional(),
  City: z.string().nullable().optional(),
  State: z.string().nullable().optional(),
});

const CallHistorySchema = z.object({
  Call_Id: z.string(),
  Call_Sid: z.string().nullable().optional(),
  Scheduled_Time: z.string().nullable().optional(),
  Started_Time: z.string().nullable().optional(),
  Status: z.string().nullable().optional(),
  Emotion: z.string().nullable().optional(),
  Emotion_Id: z.string().nullable().optional(),
  Analysis_Score: z.number().nullable().optional(),
  Duration: z.number().nullable().optional(),
  Attempts: z.number().nullable().optional(),
  Recording_Url: z.string().nullable().optional(),
  Recording_Proxy_Url: z.string().nullable().optional(),
});

const TargetDetailsSchema = z.object({
  Target_Id: z.string(),
  Name: z.string().nullable().optional(),
  Phone_No: z.string().nullable().optional(),
  Department_Name: z.string().nullable().optional(),
  Program: z.string().nullable().optional(),
  Is_Flagged: z.boolean().optional(),
  Call_Scheduled_DateTime: z.string().nullable().optional(),
  Total_Calls: z.number().nullable().optional(),
  Call_History: z.array(CallHistorySchema).default([]),
});

const TargetWithLatestSchema = z.object({
  Target_Id: z.string(),
  Name: z.string().nullable().optional(),
  Roll_No: z.string().nullable().optional(),
  Phone_No: z.string().nullable().optional(),
  Department_Name: z.string().nullable().optional(),
  Program: z.string().nullable().optional(),
  Latest_Status: z.string().nullable().optional(),
  Last_Call_Time: z.string().nullable().optional(),
  Latest_Emotion: z.string().nullable().optional(),
  Is_Flagged: z.boolean().nullable().optional(),
});

const DashboardStatsSchema = z.object({
  total_targets: z.number().default(0),
  flagged_count: z.number().default(0),
  total_calls: z.number().default(0),
});

const LiveCallSchema = z
  .object({
    target_name: z.string().nullable().optional(),
    target_phone: z.string().nullable().optional(),
    started_time: z.string().nullable().optional(),
    emotion: z.string().nullable().optional(),
    status: z.string().nullable().optional(),
    recording_url: z.string().nullable().optional(),
    recording_proxy_url: z.string().nullable().optional(),
  })
  .passthrough();

const FlaggedCounsellorTargetSchema = z
  .object({
    Flag_Id: z.string().nullable().optional(),
    Target_Id: z.string().nullable().optional(),
    Name: z.string().nullable().optional(),
    Roll_No: z.string().nullable().optional(),
    Phone_No: z.string().nullable().optional(),
    Department_Name: z.string().nullable().optional(),
    Program: z.string().nullable().optional(),
    Call_Scheduled_DateTime: z.string().nullable().optional(),
    Analysis_Score: z.number().nullable().optional(),
  })
  .passthrough();

const PotentialCaseExportRowSchema = z
  .object({
    Name: z.string().nullable().optional(),
    Roll_No: z.string().nullable().optional(),
    Phone_No: z.string().nullable().optional(),
    Department_Name: z.string().nullable().optional(),
    Program: z.string().nullable().optional(),
    Call_Made_DateTime: z.string().nullable().optional(),
    Analysis_Score: z.number().nullable().optional(),
  })
  .passthrough();

export type Target = z.infer<typeof TargetSchema>;
export type TargetDetails = z.infer<typeof TargetDetailsSchema>;
export type CallHistoryEntry = z.infer<typeof CallHistorySchema>;
export type TargetWithLatest = z.infer<typeof TargetWithLatestSchema>;
export type DashboardStats = z.infer<typeof DashboardStatsSchema>;
export type LiveCallEntry = z.infer<typeof LiveCallSchema>;
export type FlaggedCounsellorTarget = z.infer<typeof FlaggedCounsellorTargetSchema>;
export type PotentialCaseExportRow = z.infer<typeof PotentialCaseExportRowSchema>;
export type CreateTargetPayload = {
  Name: string;
  Roll_No: string;
  Phone_No: string;
  Department_Name: string;
  Program: string;
};

export interface TargetListFilters {
  department?: string | null;
  emotion?: string | null;
  call_status?: string | null;
  flagged?: boolean | null;
  search?: string | null;
}

export async function fetchTargets() {
  const response = await apiClient.get('/api/targets');
  return z.array(TargetSchema).parse(response.data);
}

export async function fetchTargetsWithLatest(filters: TargetListFilters = {}) {
  const params = new URLSearchParams();
  if (filters.department && filters.department !== 'All') params.append('department', String(filters.department));
  if (filters.emotion && filters.emotion !== 'All') params.append('emotion', String(filters.emotion));
  if (filters.call_status && filters.call_status !== 'All') params.append('call_status', String(filters.call_status));
  if (filters.flagged !== null && filters.flagged !== undefined) params.append('flagged', String(filters.flagged));
  if (filters.search) params.append('search', filters.search);

  const response = await apiClient.get('/api/counsellor/targets', { params });
  return z.array(TargetWithLatestSchema).parse(response.data);
}

export async function createTarget(payload: CreateTargetPayload) {
  await apiClient.post('/api/targets', payload);
}

export async function fetchTargetDetails(targetId: string) {
  const response = await apiClient.get(`/api/counsellor/target/${targetId}`);
  return TargetDetailsSchema.parse(response.data);
}

export async function fetchDashboardStats() {
  const response = await apiClient.get('/api/counsellor/dashboard/stats');
  return DashboardStatsSchema.parse(response.data);
}

export async function fetchLiveCalls() {
  const response = await apiClient.get('/api/counsellor/live-calls');
  return z.array(LiveCallSchema).parse(response.data);
}

export async function fetchFlaggedTargetsCounsellor() {
  const response = await apiClient.get('/api/counsellor/flagged-targets');
  return z.array(FlaggedCounsellorTargetSchema).parse(response.data);
}

export async function fetchPotentialCasesExport(params: { range?: string } = {}) {
  const response = await apiClient.get('/api/counsellor/potential-cases/export', { params });
  return z.array(PotentialCaseExportRowSchema).parse(response.data);
}

export async function triggerCallSchedule() {
  await apiClient.post('/api/schedule_calls');
}

export async function bulkImportTargets(rows: Array<Record<string, unknown>>) {
  await apiClient.post('/api/targets/bulk', rows);
}

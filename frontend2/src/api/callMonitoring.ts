import { z } from 'zod';
import apiClient from './client';

const CallStatsSchema = z.object({
  scheduled_overall: z.number(),
  scheduled_today: z.number(),
  awaiting_overall: z.number(),
  awaiting_today: z.number(),
  not_conveyed_overall: z.number(),
  processed_not_conveyed: z.number(),
  processed_overall: z.number(),
  failed_overall: z.number(),
});

const CallHistoryEntrySchema = z
  .object({
    Call_Id: z.string(),
    Target_Name: z.string().nullable().optional(),
    Batch: z.number().nullable().optional(),
    Department_Name: z.string().nullable().optional(),
    Status: z.string().nullable().optional(),
    Scheduled_Time: z.string().nullable().optional(),
    Started_Time: z.string().nullable().optional(),
    End_Time: z.string().nullable().optional(),
    Duration: z.number().nullable().optional(),
    Recording_Url: z.string().nullable().optional(),
  })
  .passthrough();

const CallHistoryListSchema = z.array(CallHistoryEntrySchema);

export type CallStats = z.infer<typeof CallStatsSchema>;
export type CallHistoryEntry = z.infer<typeof CallHistoryEntrySchema>;

export interface CallHistoryFilters {
  batch?: string | null;
  department?: string | null;
  status?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

export async function fetchCallStats(): Promise<CallStats> {
  const response = await apiClient.get('/api/monitor/stats');
  return CallStatsSchema.parse(response.data);
}

export async function fetchCallHistory(filters: CallHistoryFilters = {}): Promise<CallHistoryEntry[]> {
  const params = new URLSearchParams();
  if (filters.batch && filters.batch !== 'All') params.append('batch', filters.batch);
  if (filters.department && filters.department !== 'All') params.append('department', filters.department);
  if (filters.status && filters.status !== 'All') params.append('status', filters.status);
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);

  const response = await apiClient.get('/api/monitor/calls', { params });
  return CallHistoryListSchema.parse(response.data);
}

export async function exportCallsCsv(): Promise<string> {
  const response = await apiClient.get('/api/monitor/export_csv');
  const parsed = z.object({ csv_data: z.string() }).parse(response.data);
  return parsed.csv_data;
}

export async function triggerManualSchedule(): Promise<void> {
  await apiClient.post('/api/schedule_calls');
}

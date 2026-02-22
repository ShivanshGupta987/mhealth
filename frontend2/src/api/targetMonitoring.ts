import { z } from 'zod';
import apiClient from './client';

const TargetStatsSchema = z.object({
  total_screened: z.number(),
  total_flagged: z.number(),
  new_flagged_24h: z.number(),
});

const FlaggedTargetSchema = z
  .object({
    Flag_Id: z.string(),
    Target_Id: z.string(),
    Name: z.string().nullable().optional(),
    Batch: z.union([z.string(), z.number()]).nullable().optional(),
    Department_Name: z.string().nullable().optional(),
    Phone_No: z.string().nullable().optional(),
    Call_Scheduled_DateTime: z.string().nullable().optional(),
  })
  .passthrough();

const TrendPointSchema = z.object({
  date: z.string(),
  negative_percentage: z.number(),
});

const TrendsResponseSchema = z.object({
  month: z.number().nullable().optional(),
  month_name: z.string().nullable().optional(),
  year: z.number().nullable().optional(),
  range_days: z.number().nullable().optional(),
  data: z.array(TrendPointSchema),
});

export type TargetStats = z.infer<typeof TargetStatsSchema>;
export type FlaggedTarget = z.infer<typeof FlaggedTargetSchema>;
export type TrendsResponse = z.infer<typeof TrendsResponseSchema>;

export interface TrendFilters {
  range_days?: number;
  month?: number;
  year?: number;
}

export async function fetchTargetStats(): Promise<TargetStats> {
  const response = await apiClient.get('/api/target_monitoring/stats');
  return TargetStatsSchema.parse(response.data);
}

export async function fetchFlaggedTargets(): Promise<FlaggedTarget[]> {
  const response = await apiClient.get('/api/target_monitoring/flagged_targets');
  return z.array(FlaggedTargetSchema).parse(response.data);
}

export async function fetchEmotionTrends(filters: TrendFilters = {}): Promise<TrendsResponse> {
  const params = new URLSearchParams();
  if (filters.range_days) params.append('range_days', String(filters.range_days));
  if (filters.month) params.append('month', String(filters.month));
  if (filters.year) params.append('year', String(filters.year));

  const response = await apiClient.get('/api/target_monitoring/trends', { params });
  return TrendsResponseSchema.parse(response.data);
}

export async function unflagTarget(targetId: string): Promise<void> {
  await apiClient.delete(`/api/target_monitoring/unflag/${targetId}`);
}

export async function triggerAutoFlag(): Promise<void> {
  await apiClient.post('/api/target_monitoring/check_and_flag');
}

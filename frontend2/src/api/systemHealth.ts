import { z } from 'zod';
import apiClient from './client';

const RootInfoSchema = z
  .object({
    status: z.string().optional(),
  })
  .passthrough();

const ConfigCheckSchema = z
  .object({
    minio_connected: z.boolean().optional(),
    twilio_account_sid: z.string().nullable().optional(),
    webhook_urls: z.record(z.string(), z.string()).optional(),
  })
  .passthrough();

export type RootInfo = z.infer<typeof RootInfoSchema>;
export type ConfigCheck = z.infer<typeof ConfigCheckSchema>;

export async function fetchRootInfo() {
  const response = await apiClient.get('/');
  return RootInfoSchema.parse(response.data);
}

export async function fetchConfigInfo() {
  const response = await apiClient.get('/config-check');
  return ConfigCheckSchema.parse(response.data);
}

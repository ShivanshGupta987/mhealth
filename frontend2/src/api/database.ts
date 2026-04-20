import { z } from 'zod';
import apiClient from './client';

const GenericRecordSchema = z.record(z.string(), z.any());

const TargetRecordSchema = z
  .object({
    Target_Id: z.string(),
    Name: z.string().nullable().optional(),
    Phone_No: z.string().nullable().optional(),
    Batch: z.number().nullable().optional(),
    Department_Name: z.string().nullable().optional(),
    Program: z.string().nullable().optional(),
    Semester: z.number().nullable().optional(),
    Street: z.string().nullable().optional(),
    City: z.string().nullable().optional(),
    State: z.string().nullable().optional(),
    Zip_Code: z.string().nullable().optional(),
    Address: z.string().nullable().optional(),
  })
  .passthrough();

const ModelRecordSchema = z
  .object({
    Model_Id: z.string(),
    Model_Name: z.string().nullable().optional(),
    Model_Version: z.string().nullable().optional(),
    Model_Details: z.string().nullable().optional(),
  })
  .passthrough();

const EmotionRecordSchema = z
  .object({
    Emotion_Id: z.string(),
    Emotion: z.string().nullable().optional(),
  })
  .passthrough();

const AdminRecordSchema = z
  .object({
    Admin_Id: z.string(),
    Email: z.string().nullable().optional(),
    Password: z.string().nullable().optional(),
  })
  .passthrough();

const CallAttemptRecordSchema = z
  .object({
    Attempt_Id: z.string(),
    Call_Id: z.string().nullable().optional(),
    Call_Sid: z.string().nullable().optional(),
    Attempt_Number: z.number().nullable().optional(),
    Scheduled_Time: z.string().nullable().optional(),
    Started_Time: z.string().nullable().optional(),
    End_Time: z.string().nullable().optional(),
    Duration: z.number().nullable().optional(),
    Status: z.string().nullable().optional(),
    Recording_Url: z.string().nullable().optional(),
  })
  .passthrough();

const CallRecordSchema = z
  .object({
    Call_Id: z.string(),
    Call_Sid: z.string().nullable().optional(),
    Target_Id: z.string().nullable().optional(),
    Model_Id: z.string().nullable().optional(),
    Emotion_Id: z.string().nullable().optional(),
    Scheduled_Time: z.string().nullable().optional(),
    Started_Time: z.string().nullable().optional(),
    Status: z.string().nullable().optional(),
    Duration: z.number().nullable().optional(),
    Recording_Url: z.string().nullable().optional(),
    Analysis_Score: z.number().nullable().optional(),
  })
  .passthrough();

const FlaggedTargetRecordSchema = z
  .object({
    Flag_Id: z.string(),
    Target_Id: z.string(),
    Call_Scheduled_DateTime: z.string().nullable().optional(),
  })
  .passthrough();

export type TargetRecord = z.infer<typeof TargetRecordSchema>;
export type ModelRecord = z.infer<typeof ModelRecordSchema>;
export type EmotionRecord = z.infer<typeof EmotionRecordSchema>;
export type AdminRecord = z.infer<typeof AdminRecordSchema>;
export type CallAttemptRecord = z.infer<typeof CallAttemptRecordSchema>;
export type CallRecord = z.infer<typeof CallRecordSchema>;
export type FlaggedTargetRecord = z.infer<typeof FlaggedTargetRecordSchema>;
export type GenericRecord = z.infer<typeof GenericRecordSchema>;

async function listRecords<T>(path: string, schema: z.ZodType<T>): Promise<T[]> {
  const response = await apiClient.get(path);
  return z.array(schema).parse(response.data);
}

async function createRecord<T>(path: string, payload: unknown, schema: z.ZodType<T>): Promise<T> {
  const response = await apiClient.post(path, payload);
  return schema.parse(response.data);
}

async function patchRecord<T>(path: string, payload: unknown, schema: z.ZodType<T>): Promise<T> {
  const response = await apiClient.patch(path, payload);
  return schema.parse(response.data);
}

async function deleteRecord(path: string): Promise<void> {
  await apiClient.delete(path);
}

export function listTargets() {
  return listRecords('/api/targets', TargetRecordSchema);
}

export function createTarget(payload: Partial<TargetRecord>) {
  return createRecord('/api/targets', payload, TargetRecordSchema);
}

export function updateTarget(targetId: string, payload: Partial<TargetRecord>) {
  return patchRecord(`/api/targets/${targetId}`, payload, TargetRecordSchema);
}

export function deleteTarget(targetId: string) {
  return deleteRecord(`/api/targets/${targetId}`);
}

export function importTargets(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.post('/api/targets/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

export function bulkImportTargets(rows: Array<Record<string, unknown>>) {
  return apiClient.post('/api/targets/bulk', rows);
}

export function listModels() {
  return listRecords('/api/models', ModelRecordSchema);
}

export function createModel(payload: Partial<ModelRecord>) {
  return createRecord('/api/models', payload, ModelRecordSchema);
}

export function updateModel(modelId: string, payload: Partial<ModelRecord>) {
  return patchRecord(`/api/models/${modelId}`, payload, ModelRecordSchema);
}

export function deleteModel(modelId: string) {
  return deleteRecord(`/api/models/${modelId}`);
}

export function listEmotions() {
  return listRecords('/api/emotions', EmotionRecordSchema);
}

export function createEmotion(payload: Partial<EmotionRecord>) {
  return createRecord('/api/emotions', payload, EmotionRecordSchema);
}

export function updateEmotion(emotionId: string, payload: Partial<EmotionRecord>) {
  return patchRecord(`/api/emotions/${emotionId}`, payload, EmotionRecordSchema);
}

export function deleteEmotion(emotionId: string) {
  return deleteRecord(`/api/emotions/${emotionId}`);
}

export function listAdmins() {
  return listRecords('/api/admins', AdminRecordSchema);
}

export function createAdmin(payload: Partial<AdminRecord>) {
  return createRecord('/api/admins', payload, AdminRecordSchema);
}

export function updateAdmin(adminId: string, payload: Partial<AdminRecord>) {
  return patchRecord(`/api/admins/${adminId}`, payload, AdminRecordSchema);
}

export function deleteAdmin(adminId: string) {
  return deleteRecord(`/api/admins/${adminId}`);
}

export function listCallAttempts() {
  return listRecords('/api/call_attempts', CallAttemptRecordSchema);
}

export function createCallAttempt(payload: Partial<CallAttemptRecord>) {
  return createRecord('/api/call_attempts', payload, CallAttemptRecordSchema);
}

export function updateCallAttempt(attemptId: string, payload: Partial<CallAttemptRecord>) {
  return patchRecord(`/api/call_attempts/${attemptId}`, payload, CallAttemptRecordSchema);
}

export function deleteCallAttempt(attemptId: string) {
  return deleteRecord(`/api/call_attempts/${attemptId}`);
}

export function listCalls() {
  return listRecords('/api/calls', CallRecordSchema);
}

export function createCall(payload: Partial<CallRecord>) {
  return createRecord('/api/calls', payload, CallRecordSchema);
}

export function updateCall(callId: string, payload: Partial<CallRecord>) {
  return patchRecord(`/api/calls/${callId}`, payload, CallRecordSchema);
}

export function deleteCall(callId: string) {
  return deleteRecord(`/api/calls/${callId}`);
}

export function listFlaggedTargetsRaw() {
  return listRecords('/api/flagged_targets', FlaggedTargetRecordSchema);
}

export function createFlaggedTarget(payload: { Target_Id: string }) {
  return createRecord('/api/flagged_targets', payload, FlaggedTargetRecordSchema);
}

export function updateFlaggedTarget(flagId: string, payload: Partial<FlaggedTargetRecord>) {
  return patchRecord(`/api/flagged_targets/${flagId}`, payload, FlaggedTargetRecordSchema);
}

export function deleteFlaggedTarget(flagId: string) {
  return deleteRecord(`/api/flagged_targets/${flagId}`);
}

export function downloadCsv(path: string) {
  return apiClient.get(path, { responseType: 'blob' });
}

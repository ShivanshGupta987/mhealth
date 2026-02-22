import { z } from 'zod';
import apiClient from './client';

const LoginResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
  admin_id: z.string(),
});

const SignupResponseSchema = z.object({
  ok: z.boolean(),
  admin_id: z.string(),
});

export type LoginResponse = z.infer<typeof LoginResponseSchema>;
export type SignupResponse = z.infer<typeof SignupResponseSchema>;

export interface LoginPayload {
  email: string;
  password: string;
}

export interface SignupPayload {
  email: string;
  password: string;
}

export interface ChangePasswordPayload {
  email: string;
  current_password: string;
  new_password: string;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  new_password: string;
}

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  const response = await apiClient.post('/api/auth/login', payload);
  return LoginResponseSchema.parse(response.data);
}

export async function signup(payload: SignupPayload): Promise<SignupResponse> {
  const response = await apiClient.post('/api/auth/signup', payload);
  return SignupResponseSchema.parse(response.data);
}

export async function changePassword(payload: ChangePasswordPayload): Promise<{ ok: boolean; message: string }> {
  const response = await apiClient.post('/api/auth/change-password', payload);
  return response.data;
}

export async function forgotPassword(payload: ForgotPasswordPayload): Promise<{ ok: boolean; message: string }> {
  const response = await apiClient.post('/api/auth/forgot-password', payload);
  return response.data;
}

export async function resetPassword(payload: ResetPasswordPayload): Promise<{ ok: boolean; message: string }> {
  const response = await apiClient.post('/api/auth/reset-password', payload);
  return response.data;
}

export async function verifyResetToken(token: string): Promise<{ valid: boolean; email?: string; message?: string }> {
  const response = await apiClient.get(`/api/auth/verify-reset-token/${token}`);
  return response.data;
}

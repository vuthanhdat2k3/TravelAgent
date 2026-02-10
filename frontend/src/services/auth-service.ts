import { apiClient } from "@/lib/api-client";
import type { User } from "@/types/user";
import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Email không hợp lệ"),
  password: z.string().min(8, "Mật khẩu tối thiểu 8 ký tự"),
});

export type LoginInput = z.infer<typeof loginSchema>;

export const registerSchema = loginSchema.extend({
  full_name: z.string().min(1, "Vui lòng nhập họ tên"),
  phone: z.string().optional(),
});

export type RegisterInput = z.infer<typeof registerSchema>;

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in?: number | null;
  user: User;
};

export type RefreshTokenResponse = {
  access_token: string;
  refresh_token?: string | null;
  token_type: string;
  expires_in?: number | null;
};

export async function login(input: LoginInput): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", input);
  return data;
}

export async function register(input: RegisterInput): Promise<User> {
  const { data } = await apiClient.post<User>("/auth/register", input);
  return data;
}

export async function refreshToken(
  refresh_token: string,
): Promise<RefreshTokenResponse> {
  const { data } = await apiClient.post<RefreshTokenResponse>("/auth/refresh", {
    refresh_token,
  });
  return data;
}

export async function logout(): Promise<void> {
  await apiClient.post("/auth/logout");
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}


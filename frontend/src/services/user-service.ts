import { apiClient } from "@/lib/api-client";
import type { User } from "@/types/user";

export async function getMe(): Promise<User> {
  const { data } = await apiClient.get<User>("/users/me");
  return data;
}

export async function updateMe(
  payload: Partial<Pick<User, "full_name" | "phone" | "avatar_url">>,
): Promise<User> {
  const { data } = await apiClient.patch<User>("/users/me", payload);
  return data;
}

type AdminUserListResponse = {
  items: User[];
  total: number;
};

export async function adminListUsers(params?: {
  skip?: number;
  limit?: number;
  is_active?: boolean;
  q?: string;
}): Promise<AdminUserListResponse> {
  const { data } = await apiClient.get<AdminUserListResponse>("/admin/users", {
    params,
  });
  return data;
}

export async function adminGetUser(userId: string): Promise<User> {
  const { data } = await apiClient.get<User>(`/admin/users/${userId}`);
  return data;
}

export async function adminUpdateUser(
  userId: string,
  payload: Partial<Pick<User, "full_name" | "phone" | "avatar_url" | "is_active">>,
): Promise<User> {
  const { data } = await apiClient.patch<User>(
    `/admin/users/${userId}`,
    payload,
  );
  return data;
}


import { apiClient } from "@/lib/api-client";
import type { UserPreference } from "@/types/preferences";

export async function getMyPreferences(): Promise<UserPreference> {
  const { data } = await apiClient.get<UserPreference>("/users/me/preferences");
  return data;
}

export async function upsertPreferences(
  payload: Omit<UserPreference, "id" | "user_id" | "created_at" | "updated_at">,
): Promise<UserPreference> {
  const { data } = await apiClient.patch<UserPreference>(
    "/users/me/preferences",
    payload,
  );
  return data;
}

export async function patchPreferences(
  payload: Partial<
    Omit<UserPreference, "id" | "user_id" | "created_at" | "updated_at">
  >,
): Promise<UserPreference> {
  const { data } = await apiClient.patch<UserPreference>(
    "/users/me/preferences",
    payload,
  );
  return data;
}


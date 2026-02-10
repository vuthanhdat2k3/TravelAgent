import { apiClient } from "@/lib/api-client";
import type { NotificationLog } from "@/types/notification";

export async function listMyNotifications(params?: {
  skip?: number;
  limit?: number;
  type?: string;
}): Promise<NotificationLog[]> {
  const { data } = await apiClient.get<NotificationLog[]>(
    "/users/me/notifications",
    { params },
  );
  return data;
}


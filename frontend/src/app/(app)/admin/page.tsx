import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";

import { getQueryClient } from "@/lib/get-query-client";
import { serverFetch } from "@/lib/server-api";
import AdminContent from "./admin-content";

export const metadata: Metadata = {
  title: "Admin | Travel Agent",
  description: "Quản lý người dùng hệ thống.",
};

type AdminUserListResponse = {
  items: Array<{
    id: string;
    email: string;
    full_name?: string | null;
    is_active: boolean;
  }>;
  total: number;
};

export default async function AdminPage() {
  const queryClient = getQueryClient();

  await queryClient.prefetchQuery({
    queryKey: ["admin", "users"],
    queryFn: () =>
      serverFetch<AdminUserListResponse>("/admin/users", {
        params: { limit: "50" },
      }),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <AdminContent />
    </HydrationBoundary>
  );
}


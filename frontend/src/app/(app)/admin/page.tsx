"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";

import { AppShell } from "@/components/layout/app-shell";
import { adminListUsers } from "@/services/user-service";
import { useRequireAuth } from "@/hooks/use-auth";

export default function AdminPage() {
  useRequireAuth();

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin", "users"],
    queryFn: () => adminListUsers({ limit: 50 }),
  });

  return (
    <AppShell>
      <div className="space-y-6">
        <header className="space-y-1">
          <h1 className="text-lg font-semibold text-neutral-900">Admin</h1>
          <p className="text-xs text-neutral-600">
            Quản lý người dùng (chỉ dành cho tài khoản admin).
          </p>
        </header>

        {error ? (
          <div className="rounded-md border border-destructive/20 bg-destructive/5 px-3 py-2 text-xs text-destructive">
            Bạn không có quyền truy cập trang này hoặc đã xảy ra lỗi.
          </div>
        ) : null}

        <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white/80 shadow-sm">
          <div className="grid grid-cols-[2fr_2fr_1fr] gap-4 border-b border-neutral-100 px-4 py-2 text-xs font-medium text-neutral-500">
            <span>Email</span>
            <span>Họ tên</span>
            <span className="text-right">Trạng thái</span>
          </div>
          <div className="divide-y divide-neutral-100 text-sm">
            {isLoading
              ? Array.from({ length: 5 }).map((_, idx) => (
                  <div
                    key={idx}
                    className="flex animate-pulse items-center gap-4 px-4 py-3"
                  >
                    <div className="h-3 w-40 rounded bg-neutral-200" />
                    <div className="h-3 w-32 rounded bg-neutral-100" />
                    <div className="ml-auto h-3 w-10 rounded bg-neutral-100" />
                  </div>
                ))
              : data?.items?.map((u) => (
                  <motion.div
                    key={u.id}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="grid grid-cols-[2fr_2fr_1fr] gap-4 px-4 py-3 text-xs text-neutral-800"
                  >
                    <span>{u.email}</span>
                    <span>{u.full_name ?? "—"}</span>
                    <span className="text-right">
                      {u.is_active ? "Active" : "Locked"}
                    </span>
                  </motion.div>
                ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}


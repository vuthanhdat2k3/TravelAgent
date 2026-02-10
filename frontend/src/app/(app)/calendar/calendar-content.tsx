"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { CalendarDaysIcon, ClockIcon, MapPinIcon } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { listMyCalendarEvents } from "@/services/calendar-service";
import { useRequireAuth } from "@/hooks/use-auth";

export default function CalendarContent() {
  useRequireAuth();

  const { data, isLoading } = useQuery({
    queryKey: ["calendar-events", "me"],
    queryFn: listMyCalendarEvents,
  });

  return (
    <AppShell>
      <div className="space-y-6">
        <header className="space-y-1">
          <h1 className="text-lg font-semibold text-neutral-900">
            Lịch chuyến bay
          </h1>
          <p className="text-xs text-neutral-600">
            Các sự kiện đã được đồng bộ với Google Calendar.
          </p>
        </header>

        <div className="space-y-3">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, idx) => (
              <div
                key={idx}
                className="flex animate-pulse items-center justify-between rounded-xl border border-neutral-200 bg-white/80 p-4 shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <span className="h-9 w-9 rounded-full bg-neutral-200" />
                  <div className="space-y-2">
                    <div className="h-3 w-40 rounded bg-neutral-200" />
                    <div className="h-3 w-24 rounded bg-neutral-100" />
                  </div>
                </div>
              </div>
            ))
          ) : data && data.length > 0 ? (
            data.map((e) => (
              <motion.article
                key={e.id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white/80 p-4 shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-500/10 text-primary-600">
                    <CalendarDaysIcon className="h-4 w-4" />
                  </span>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-neutral-900">
                      Booking #{e.booking_id.slice(0, 8)}
                    </p>
                    <p className="flex items-center gap-2 text-xs text-neutral-500">
                      <ClockIcon className="h-3 w-3" />
                      {new Date(e.synced_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <p className="flex items-center gap-1 text-xs text-neutral-500">
                  <MapPinIcon className="h-3 w-3" />
                  {e.calendar_id ?? "primary"}
                </p>
              </motion.article>
            ))
          ) : (
            <div className="rounded-xl border border-dashed border-neutral-200 bg-white/60 p-6 text-center text-sm text-neutral-500">
              Chưa có sự kiện lịch nào. Bạn có thể thêm từ chi tiết booking.
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

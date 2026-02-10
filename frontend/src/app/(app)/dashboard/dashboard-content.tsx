"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { CalendarDaysIcon, PlaneIcon, CreditCardIcon } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { fetchMyBookings } from "@/services/booking-service";
import { useRequireAuth } from "@/hooks/use-auth";

export default function DashboardContent() {
  useRequireAuth();

  const { data, isLoading } = useQuery({
    queryKey: ["bookings", "me"],
    queryFn: fetchMyBookings,
  });

  return (
    <AppShell>
      <div className="space-y-8">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight text-neutral-900">
            Bảng điều khiển
          </h1>
          <p className="text-sm text-neutral-600">
            Xem nhanh các chuyến sắp tới, bookings gần đây và thanh toán của bạn.
          </p>
        </header>

        <section className="grid gap-4 md:grid-cols-3">
          <DashboardStatCard
            icon={PlaneIcon}
            label="Chuyến bay sắp tới"
            value={data?.length ?? 0}
          />
          <DashboardStatCard
            icon={CalendarDaysIcon}
            label="Bookings trong 30 ngày"
            value={data?.length ?? 0}
          />
          <DashboardStatCard
            icon={CreditCardIcon}
            label="Thanh toán đang xử lý"
            value={0}
          />
        </section>

        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-neutral-900">
              Bookings gần đây
            </h2>
          </div>

          <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white/80 shadow-sm">
            {isLoading ? (
              <div className="divide-y divide-neutral-100">
                {Array.from({ length: 3 }).map((_, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between px-4 py-4 animate-pulse"
                  >
                    <div className="space-y-2">
                      <div className="h-3 w-32 rounded bg-neutral-200" />
                      <div className="h-3 w-48 rounded bg-neutral-100" />
                    </div>
                    <div className="h-6 w-16 rounded-full bg-neutral-200" />
                  </div>
                ))}
              </div>
            ) : data && data.length > 0 ? (
              <div className="divide-y divide-neutral-100">
                {data.slice(0, 5).map((booking) => {
                  const firstLeg = booking.flights[0];
                  const route = firstLeg
                    ? `${firstLeg.origin} → ${firstLeg.destination}`
                    : "Chuyến bay";

                  return (
                    <motion.div
                      key={booking.id}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2 }}
                      className="flex items-center justify-between px-4 py-4"
                    >
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-neutral-900">
                            {route}
                          </span>
                          {booking.booking_reference ? (
                            <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs text-neutral-600">
                              {booking.booking_reference}
                            </span>
                          ) : null}
                        </div>
                        <p className="text-xs text-neutral-500">
                          {booking.status} •{" "}
                          {new Date(booking.created_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-neutral-900">
                          {booking.total_price
                            ? `${booking.total_price.toLocaleString("vi-VN")} ${
                                booking.currency ?? "VND"
                              }`
                            : "—"}
                        </p>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            ) : (
              <div className="px-4 py-8 text-center text-sm text-neutral-500">
                Bạn chưa có booking nào. Hãy bắt đầu bằng việc tìm chuyến bay.
              </div>
            )}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

type StatCardProps = {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  label: string;
  value: number;
};

function DashboardStatCard({ icon: Icon, label, value }: StatCardProps) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
      className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white/80 px-4 py-3 shadow-sm"
    >
      <div className="space-y-0.5">
        <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">
          {label}
        </p>
        <p className="text-xl font-semibold text-neutral-900">{value}</p>
      </div>
      <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-500/10 text-primary-600">
        <Icon className="h-4 w-4" />
      </span>
    </motion.article>
  );
}

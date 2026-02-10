"use client";

import { motion } from "framer-motion";
import { CheckCircle2Icon, PlaneIcon } from "lucide-react";
import type { SuggestedActionData } from "./suggested-actions";

export type BookingSuccessData = {
  booking_id: string;
  booking_reference: string;
  status: string;
  flights?: {
    origin: string;
    destination: string;
    departure_time: string;
    airline_code: string;
    flight_number: string;
  }[];
};

export function BookingSuccessCard({
  booking,
  onAction,
  disabled,
}: {
  booking: BookingSuccessData;
  onAction: (action: SuggestedActionData) => void;
  disabled?: boolean;
}) {
  const flight = booking.flights?.[0];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="my-1 w-full max-w-[320px] overflow-hidden rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white shadow-sm"
    >
      {/* Header */}
      <div className="flex items-center gap-2 bg-emerald-500 px-3 py-2 text-white">
        <CheckCircle2Icon className="h-4 w-4" />
        <span className="text-xs font-semibold">Đặt vé thành công!</span>
      </div>

      {/* Body */}
      <div className="space-y-2 p-3">
        <div className="flex items-center justify-between text-xs">
          <span className="text-neutral-500">Mã đặt chỗ</span>
          <span className="font-mono font-bold text-emerald-700">
            {booking.booking_reference ?? "N/A"}
          </span>
        </div>

        {flight && (
          <div className="flex items-center gap-2 rounded-lg bg-neutral-50 px-3 py-2">
            <PlaneIcon className="h-3.5 w-3.5 text-primary-500" />
            <div className="text-xs">
              <span className="font-semibold text-neutral-900">
                {flight.airline_code}{flight.flight_number}
              </span>
              <span className="mx-1 text-neutral-400">·</span>
              <span className="text-neutral-600">
                {flight.origin} → {flight.destination}
              </span>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between text-[10px] text-neutral-400">
          <span>ID: {booking.booking_id.slice(0, 8)}...</span>
          <span className="rounded-full bg-emerald-100 px-2 py-0.5 font-medium text-emerald-700">
            {booking.status}
          </span>
        </div>

      </div>
    </motion.div>
  );
}

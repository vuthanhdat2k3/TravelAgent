"use client";

import { motion } from "framer-motion";
import {
  PlaneIcon,
  ClockIcon,
  ArrowRightIcon,
  CircleDotIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type FlightSegment = {
  origin: string;
  destination: string;
  departure_time: string;
  arrival_time: string;
  airline_code: string;
  flight_number: string;
};

export type FlightOffer = {
  offer_id: string;
  index: number;
  total_price: number;
  currency: string;
  duration_minutes: number;
  stops: number;
  segments: FlightSegment[];
};

function formatTime(dateStr: string) {
  try {
    const d = new Date(dateStr);
    return d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return dateStr?.slice(11, 16) ?? "--:--";
  }
}

function formatDuration(minutes: number) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}p`;
  if (m === 0) return `${h}h`;
  return `${h}h${m}p`;
}

function formatPrice(price: number, currency: string) {
  if (currency === "VND") {
    return new Intl.NumberFormat("vi-VN").format(price) + "₫";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(price);
}

// Airline name mapping
const AIRLINE_NAMES: Record<string, string> = {
  VJ: "VietJet Air",
  VN: "Vietnam Airlines",
  QH: "Bamboo Airways",
  VU: "Vietravel Airlines",
  BL: "Pacific Airlines",
  SQ: "Singapore Airlines",
  TG: "Thai Airways",
  CX: "Cathay Pacific",
  JL: "Japan Airlines",
  NH: "ANA",
  KE: "Korean Air",
  OZ: "Asiana Airlines",
};

function getAirlineName(code: string) {
  return AIRLINE_NAMES[code] ?? code;
}

// Airline brand colors
const AIRLINE_COLORS: Record<string, string> = {
  VJ: "from-red-500 to-yellow-500",
  VN: "from-blue-600 to-cyan-500",
  QH: "from-emerald-500 to-teal-400",
  VU: "from-orange-500 to-amber-400",
  BL: "from-yellow-500 to-orange-400",
};

function getAirlineGradient(code: string) {
  return AIRLINE_COLORS[code] ?? "from-slate-500 to-slate-400";
}

export function FlightCard({
  offer,
  onSelect,
  disabled,
}: {
  offer: FlightOffer;
  onSelect: (offer: FlightOffer) => void;
  disabled?: boolean;
}) {
  const firstSeg = offer.segments[0];
  const lastSeg = offer.segments[offer.segments.length - 1];
  const airlineCode = firstSeg?.airline_code ?? "";
  const flightCode = `${airlineCode}${firstSeg?.flight_number ?? ""}`;

  return (
    <motion.button
      whileHover={disabled ? {} : { scale: 1.02, y: -2 }}
      whileTap={disabled ? {} : { scale: 0.98 }}
      onClick={() => !disabled && onSelect(offer)}
      disabled={disabled}
      className={cn(
        "group relative w-full rounded-xl border bg-white p-3 text-left shadow-sm transition-all",
        "hover:border-primary-300 hover:shadow-md",
        disabled && "pointer-events-none opacity-50",
      )}
    >
      {/* Airline badge */}
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br text-[10px] font-bold text-white",
              getAirlineGradient(airlineCode),
            )}
          >
            {airlineCode}
          </div>
          <div>
            <p className="text-xs font-semibold text-neutral-900">
              {flightCode}
            </p>
            <p className="text-[10px] text-neutral-500">
              {getAirlineName(airlineCode)}
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm font-bold text-primary-600">
            {formatPrice(offer.total_price, offer.currency)}
          </p>
        </div>
      </div>

      {/* Route */}
      <div className="flex items-center gap-2">
        {/* Departure */}
        <div className="flex-1 text-center">
          <p className="text-base font-bold text-neutral-900">
            {formatTime(firstSeg?.departure_time)}
          </p>
          <p className="text-xs font-medium text-neutral-600">
            {firstSeg?.origin}
          </p>
        </div>

        {/* Timeline */}
        <div className="flex flex-1 flex-col items-center gap-0.5">
          <p className="text-[10px] text-neutral-400">
            {formatDuration(offer.duration_minutes)}
          </p>
          <div className="flex w-full items-center gap-0.5">
            <div className="h-px flex-1 bg-neutral-300" />
            <PlaneIcon className="h-3 w-3 text-primary-500" />
            <div className="h-px flex-1 bg-neutral-300" />
          </div>
          <p className="text-[10px] text-neutral-400">
            {offer.stops === 0 ? (
              <span className="text-emerald-600 font-medium">Bay thẳng</span>
            ) : (
              <span className="flex items-center gap-0.5">
                <CircleDotIcon className="h-2.5 w-2.5" />
                {offer.stops} điểm dừng
              </span>
            )}
          </p>
        </div>

        {/* Arrival */}
        <div className="flex-1 text-center">
          <p className="text-base font-bold text-neutral-900">
            {formatTime(lastSeg?.arrival_time)}
          </p>
          <p className="text-xs font-medium text-neutral-600">
            {lastSeg?.destination}
          </p>
        </div>
      </div>

      {/* Hover indicator */}
      <div className="mt-2 flex items-center justify-center gap-1 rounded-md bg-primary-50 py-1 text-[10px] font-medium text-primary-600 opacity-0 transition-opacity group-hover:opacity-100">
        <ArrowRightIcon className="h-3 w-3" />
        Chọn chuyến này
      </div>
    </motion.button>
  );
}

export function FlightCardList({
  offers,
  onSelect,
  disabled,
}: {
  offers: FlightOffer[];
  onSelect: (offer: FlightOffer) => void;
  disabled?: boolean;
}) {
  return (
    <div className="my-1 flex gap-2 overflow-x-auto pb-1">
      {offers.map((offer, i) => (
        <motion.div
          key={offer.offer_id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
          className="w-[240px] flex-shrink-0"
        >
          <FlightCard offer={offer} onSelect={onSelect} disabled={disabled} />
        </motion.div>
      ))}
    </div>
  );
}

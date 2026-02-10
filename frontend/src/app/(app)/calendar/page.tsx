import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";

import { getQueryClient } from "@/lib/get-query-client";
import { serverFetch } from "@/lib/server-api";
import type { CalendarEvent } from "@/types/calendar";
import CalendarContent from "./calendar-content";

export const metadata: Metadata = {
  title: "Lịch chuyến bay | Travel Agent",
  description: "Các sự kiện chuyến bay đã được đồng bộ với Google Calendar.",
};

export default async function CalendarPage() {
  const queryClient = getQueryClient();

  await queryClient.prefetchQuery({
    queryKey: ["calendar-events", "me"],
    queryFn: () =>
      serverFetch<CalendarEvent[]>("/users/me/calendar-events"),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <CalendarContent />
    </HydrationBoundary>
  );
}


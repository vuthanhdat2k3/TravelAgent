import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";

import { getQueryClient } from "@/lib/get-query-client";
import { serverFetch } from "@/lib/server-api";
import type { BookingListItem } from "@/types/booking";
import DashboardContent from "./dashboard-content";

export const metadata: Metadata = {
  title: "Bảng điều khiển | Travel Agent",
  description:
    "Xem nhanh các chuyến sắp tới, bookings gần đây và thanh toán của bạn.",
};

export default async function DashboardPage() {
  const queryClient = getQueryClient();

  await queryClient.prefetchQuery({
    queryKey: ["bookings", "me"],
    queryFn: () => serverFetch<BookingListItem[]>("/bookings"),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <DashboardContent />
    </HydrationBoundary>
  );
}


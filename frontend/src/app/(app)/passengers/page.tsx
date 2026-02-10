import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";

import { getQueryClient } from "@/lib/get-query-client";
import { serverFetch } from "@/lib/server-api";
import type { Passenger } from "@/types/passenger";
import PassengersContent from "./passengers-content";

export const metadata: Metadata = {
  title: "Hành khách | Travel Agent",
  description: "Quản lý thông tin hành khách để đặt vé nhanh hơn.",
};

export default async function PassengersPage() {
  const queryClient = getQueryClient();

  await queryClient.prefetchQuery({
    queryKey: ["passengers"],
    queryFn: () => serverFetch<Passenger[]>("/users/me/passengers"),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <PassengersContent />
    </HydrationBoundary>
  );
}


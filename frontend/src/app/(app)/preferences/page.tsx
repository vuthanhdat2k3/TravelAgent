import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";

import { getQueryClient } from "@/lib/get-query-client";
import { serverFetch } from "@/lib/server-api";
import type { UserPreference } from "@/types/preferences";
import PreferencesContent from "./preferences-content";

export const metadata: Metadata = {
  title: "Sở thích chuyến bay | Travel Agent",
  description: "Tối ưu gợi ý chuyến bay dựa trên thói quen của bạn.",
};

export default async function PreferencesPage() {
  const queryClient = getQueryClient();

  await queryClient.prefetchQuery({
    queryKey: ["preferences"],
    queryFn: () => serverFetch<UserPreference>("/users/me/preferences"),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <PreferencesContent />
    </HydrationBoundary>
  );
}


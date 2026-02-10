import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";

import { getQueryClient } from "@/lib/get-query-client";
import { serverFetch } from "@/lib/server-api";
import type {
  AvailableModelsResponse,
  LLMConfigResponse,
  LLMUsageStats,
} from "@/services/llm-service";
import SettingsContent from "./settings-content";

export const metadata: Metadata = {
  title: "Cài đặt AI | Travel Agent",
  description: "Chọn nhà cung cấp và mô hình AI để trả lời trong chat.",
};

export default async function SettingsPage() {
  const queryClient = getQueryClient();

  await Promise.all([
    queryClient.prefetchQuery({
      queryKey: ["llm", "models"],
      queryFn: () => serverFetch<AvailableModelsResponse>("/llm/models"),
    }),
    queryClient.prefetchQuery({
      queryKey: ["llm", "config"],
      queryFn: () => serverFetch<LLMConfigResponse>("/llm/config"),
    }),
    queryClient.prefetchQuery({
      queryKey: ["llm", "usage"],
      queryFn: () => serverFetch<LLMUsageStats>("/llm/usage"),
    }),
  ]);

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <SettingsContent />
    </HydrationBoundary>
  );
}

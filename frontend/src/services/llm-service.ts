import { apiClient } from "@/lib/api-client";

// ── Types ──────────────────────────────────────────────────────────────────

export type LLMProvider = "gemini" | "ollama" | "nvidia";

export type LLMConfigResponse = {
  id: string;
  user_id: string;
  provider: string;
  model_name: string;
  api_key_set: boolean;
  base_url: string | null;
  temperature: number;
  max_tokens: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type LLMConfigPayload = {
  provider: LLMProvider;
  model_name: string;
  api_key?: string | null;
  base_url?: string | null;
  temperature?: number;
  max_tokens?: number | null;
};

export type AvailableModel = {
  provider: string;
  model_name: string;
  display_name: string;
  description: string;
};

export type AvailableModelsResponse = {
  models: AvailableModel[];
};

export type LLMUsageStats = {
  requests_last_minute: number;
  requests_last_hour: number;
  requests_last_day: number;
  limits: {
    per_minute: number;
    per_hour: number;
    per_day: number;
  };
};

// ── API calls ──────────────────────────────────────────────────────────────

export async function getAvailableModels(): Promise<AvailableModelsResponse> {
  const { data } = await apiClient.get<AvailableModelsResponse>("/llm/models");
  return data;
}

export async function getLLMConfig(): Promise<LLMConfigResponse | null> {
  const { data } = await apiClient.get<LLMConfigResponse | null>("/llm/config");
  return data;
}

export async function saveLLMConfig(
  payload: LLMConfigPayload,
): Promise<LLMConfigResponse> {
  const { data } = await apiClient.put<LLMConfigResponse>(
    "/llm/config",
    payload,
  );
  return data;
}

export async function deleteLLMConfig(): Promise<void> {
  await apiClient.delete("/llm/config");
}

export async function getLLMUsage(): Promise<LLMUsageStats> {
  const { data } = await apiClient.get<LLMUsageStats>("/llm/usage");
  return data;
}

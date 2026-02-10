"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { motion } from "framer-motion";
import {
  BotIcon,
  CheckCircleIcon,
  Loader2Icon,
  RotateCcwIcon,
  ActivityIcon,
} from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  getAvailableModels,
  getLLMConfig,
  saveLLMConfig,
  deleteLLMConfig,
  getLLMUsage,
} from "@/services/llm-service";
import type { AvailableModel } from "@/services/llm-service";
import { useRequireAuth } from "@/hooks/use-auth";

// ── Schema ─────────────────────────────────────────────────────────────────

const llmSettingsSchema = z.object({
  provider: z.enum(["gemini", "ollama", "nvidia"]),
  model_name: z.string().min(1, "Vui lòng chọn model"),
  api_key: z.string().optional(),
  base_url: z.string().optional(),
  temperature: z
    .number()
    .min(0, "Tối thiểu 0")
    .max(2, "Tối đa 2"),
  max_tokens: z
    .number()
    .min(1, "Tối thiểu 1")
    .optional(),
});

type LLMSettingsValues = z.infer<typeof llmSettingsSchema>;

// ── Page ───────────────────────────────────────────────────────────────────

export default function SettingsContent() {
  useRequireAuth();
  const queryClient = useQueryClient();
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Fetch available models
  const modelsQuery = useQuery({
    queryKey: ["llm", "models"],
    queryFn: getAvailableModels,
  });

  // Fetch current config
  const configQuery = useQuery({
    queryKey: ["llm", "config"],
    queryFn: getLLMConfig,
    retry: 0,
  });

  // Fetch usage stats
  const usageQuery = useQuery({
    queryKey: ["llm", "usage"],
    queryFn: getLLMUsage,
    refetchInterval: 30000,
  });

  const form = useForm<LLMSettingsValues>({
    resolver: zodResolver(llmSettingsSchema),
    defaultValues: {
      provider: "gemini",
      model_name: "gemini-2.0-flash",
      api_key: "",
      base_url: "http://localhost:11434",
      temperature: 0.7,
      max_tokens: 2048,
    },
  });

  // Sync form when config loads
  useEffect(() => {
    if (configQuery.data) {
      const c = configQuery.data;
      form.reset({
        provider: c.provider as "gemini" | "ollama",
        model_name: c.model_name,
        api_key: "", // Backend doesn't return the key
        base_url: c.base_url ?? "http://localhost:11434",
        temperature: c.temperature,
        max_tokens: c.max_tokens ?? 2048,
      });
    }
  }, [configQuery.data, form]);

  const watchProvider = form.watch("provider");

  // Filter models by selected provider
  const filteredModels = useMemo(() => {
    if (!modelsQuery.data?.models) return [];
    return modelsQuery.data.models.filter(
      (m: AvailableModel) => m.provider === watchProvider,
    );
  }, [modelsQuery.data, watchProvider]);

  // When provider changes, set first matching model
  useEffect(() => {
    if (filteredModels.length > 0) {
      const current = form.getValues("model_name");
      const match = filteredModels.find(
        (m: AvailableModel) => m.model_name === current,
      );
      if (!match) {
        form.setValue("model_name", filteredModels[0].model_name);
      }
    }
  }, [watchProvider, filteredModels, form]);

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: (values: LLMSettingsValues) =>
      saveLLMConfig({
        provider: values.provider,
        model_name: values.model_name,
        api_key: values.api_key || null,
        base_url: values.provider === "ollama" ? values.base_url : null,
        temperature: values.temperature,
        max_tokens: values.max_tokens ?? null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["llm", "config"] });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
  });

  // Reset (delete config)
  const deleteMutation = useMutation({
    mutationFn: deleteLLMConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["llm", "config"] });
      form.reset({
        provider: "gemini",
        model_name: "gemini-2.0-flash",
        api_key: "",
        base_url: "http://localhost:11434",
        temperature: 0.7,
        max_tokens: 2048,
      });
    },
  });

  const isLoading = configQuery.isLoading || modelsQuery.isLoading;

  return (
    <AppShell>
      <div className="space-y-6">
        {/* ── Page header ── */}
        <header className="space-y-1">
          <h1 className="text-lg font-semibold text-neutral-900">
            Cài đặt AI Model
          </h1>
          <p className="text-xs text-neutral-600">
            Chọn nhà cung cấp và mô hình AI để trả lời trong chat.
          </p>
        </header>

        {/* ── Settings form card ── */}
        <Form {...form}>
          <motion.form
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4 rounded-xl border border-neutral-200 bg-white/80 p-5 shadow-sm"
            onSubmit={form.handleSubmit((values) =>
              saveMutation.mutate(values),
            )}
          >
            {/* Provider + Model row */}
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="provider"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Nhà cung cấp</FormLabel>
                    <FormControl>
                      <select
                        {...field}
                        className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                      >
                        <option value="gemini">Google Gemini</option>
                        <option value="nvidia">NVIDIA NIM</option>
                        <option value="ollama">Ollama (Local)</option>
                      </select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="model_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mô hình</FormLabel>
                    <FormControl>
                      <select
                        {...field}
                        className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                      >
                        {filteredModels.map((m: AvailableModel) => (
                          <option key={m.model_name} value={m.model_name}>
                            {m.display_name}
                          </option>
                        ))}
                      </select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Model description */}
            {filteredModels.length > 0 && (
              <p className="flex items-start gap-1.5 text-xs text-neutral-500">
                <BotIcon className="mt-0.5 h-3 w-3 shrink-0" />
                {
                  filteredModels.find(
                    (m: AvailableModel) =>
                      m.model_name === form.watch("model_name"),
                  )?.description ?? ""
                }
              </p>
            )}

            {/* Provider-specific fields */}
            {(watchProvider === "gemini" || watchProvider === "nvidia") && (
              <FormField
                control={form.control}
                name="api_key"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      API Key
                      {configQuery.data?.api_key_set && (
                        <span className="ml-2 text-[11px] font-normal text-success-500">
                          ✓ Đã cấu hình
                        </span>
                      )}
                    </FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        type="password"
                        placeholder={
                          configQuery.data?.api_key_set
                            ? "Để trống nếu không thay đổi"
                            : watchProvider === "nvidia"
                              ? "Nhập NVIDIA API key"
                              : "Nhập Google Gemini API key"
                        }
                      />
                    </FormControl>
                    <p className="text-[11px] text-neutral-400">
                      {watchProvider === "nvidia" ? (
                        <>
                          Lấy key tại{" "}
                          <a
                            href="https://build.nvidia.com/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-600 underline"
                          >
                            NVIDIA Build
                          </a>
                          . Để trống sẽ dùng key hệ thống (nếu có).
                        </>
                      ) : (
                        <>
                          Lấy key tại{" "}
                          <a
                            href="https://aistudio.google.com/apikey"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-600 underline"
                          >
                            Google AI Studio
                          </a>
                          . Để trống sẽ dùng key hệ thống (nếu có).
                        </>
                      )}
                    </p>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            {watchProvider === "ollama" && (
              <FormField
                control={form.control}
                name="base_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Ollama URL</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        placeholder="http://localhost:11434"
                      />
                    </FormControl>
                    <p className="text-[11px] text-neutral-400">
                      Địa chỉ Ollama server đang chạy. Mặc định: http://localhost:11434
                    </p>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            {/* Temperature + Max tokens */}
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="temperature"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Temperature{" "}
                      <span className="font-normal text-neutral-400">
                        ({field.value})
                      </span>
                    </FormLabel>
                    <FormControl>
                      <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={field.value}
                        onChange={(e) => field.onChange(parseFloat(e.target.value))}
                        className="h-2 w-full cursor-pointer appearance-none rounded-full bg-neutral-200 accent-primary-600"
                      />
                    </FormControl>
                    <p className="text-[11px] text-neutral-400">
                      Thấp = chính xác hơn, Cao = sáng tạo hơn
                    </p>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="max_tokens"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Max tokens</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
                        placeholder="2048"
                        value={field.value ?? ""}
                        onChange={(e) => {
                          const v = e.target.value;
                          field.onChange(v === "" ? undefined : Number(v));
                        }}
                      />
                    </FormControl>
                    <p className="text-[11px] text-neutral-400">
                      Giới hạn độ dài phản hồi của AI
                    </p>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between border-t border-neutral-100 pt-4">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => deleteMutation.mutate()}
                disabled={
                  deleteMutation.isPending || !configQuery.data
                }
                className="gap-1.5 text-xs"
              >
                <RotateCcwIcon className="h-3 w-3" />
                Đặt lại mặc định
              </Button>

              <div className="flex items-center gap-2">
                {saveSuccess && (
                  <motion.span
                    initial={{ opacity: 0, x: 8 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-1 text-xs text-success-500"
                  >
                    <CheckCircleIcon className="h-3.5 w-3.5" />
                    Đã lưu
                  </motion.span>
                )}
                <Button
                  type="submit"
                  disabled={saveMutation.isPending || isLoading}
                >
                  {saveMutation.isPending ? (
                    <>
                      <Loader2Icon className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                      Đang lưu...
                    </>
                  ) : (
                    "Lưu cài đặt"
                  )}
                </Button>
              </div>
            </div>
          </motion.form>
        </Form>

        {/* ── Usage stats card ── */}
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="rounded-xl border border-neutral-200 bg-white/80 p-5 shadow-sm"
        >
          <div className="mb-3 flex items-center gap-2">
            <ActivityIcon className="h-4 w-4 text-primary-600" />
            <h2 className="text-sm font-medium text-neutral-900">
              Thống kê sử dụng
            </h2>
          </div>

          {usageQuery.isLoading ? (
            <div className="grid grid-cols-3 gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-16 animate-pulse rounded-lg bg-neutral-100" />
              ))}
            </div>
          ) : usageQuery.data ? (
            <div className="grid grid-cols-3 gap-4">
              <UsageStat
                label="Phút qua"
                value={usageQuery.data.requests_last_minute}
                max={usageQuery.data.limits.per_minute}
              />
              <UsageStat
                label="Giờ qua"
                value={usageQuery.data.requests_last_hour}
                max={usageQuery.data.limits.per_hour}
              />
              <UsageStat
                label="Ngày qua"
                value={usageQuery.data.requests_last_day}
                max={usageQuery.data.limits.per_day}
              />
            </div>
          ) : (
            <p className="text-xs text-neutral-400">
              Chưa có dữ liệu sử dụng.
            </p>
          )}
        </motion.div>
      </div>
    </AppShell>
  );
}

// ── Usage stat component ───────────────────────────────────────────────────

function UsageStat({
  label,
  value,
  max,
}: {
  label: string;
  value: number;
  max: number;
}) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  const color =
    pct >= 90
      ? "bg-error-500"
      : pct >= 60
        ? "bg-warning-500"
        : "bg-primary-500";

  return (
    <div className="rounded-lg border border-neutral-100 p-3">
      <p className="mb-1 text-[11px] text-neutral-500">{label}</p>
      <p className="text-sm font-semibold text-neutral-900">
        {value}{" "}
        <span className="text-xs font-normal text-neutral-400">/ {max}</span>
      </p>
      <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-neutral-100">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

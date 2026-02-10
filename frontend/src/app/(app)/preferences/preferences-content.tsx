"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { motion } from "framer-motion";

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
  getMyPreferences,
  upsertPreferences,
} from "@/services/preference-service";
import { useRequireAuth } from "@/hooks/use-auth";

const preferencesSchema = z.object({
  cabin_class: z.string().optional(),
  preferred_airlines: z.string().optional(),
  seat_preference: z.string().optional(),
});

type PreferencesFormValues = z.infer<typeof preferencesSchema>;

export default function PreferencesContent() {
  useRequireAuth();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["preferences"],
    queryFn: getMyPreferences,
    retry: 0,
  });

  const form = useForm<PreferencesFormValues>({
    resolver: zodResolver(preferencesSchema),
    defaultValues: {
      cabin_class: data?.cabin_class ?? "ECONOMY",
      preferred_airlines: data?.preferred_airlines?.join(",") ?? "",
      seat_preference: data?.seat_preference ?? "",
    },
    values: data
      ? {
          cabin_class: data.cabin_class ?? "ECONOMY",
          preferred_airlines: data.preferred_airlines?.join(",") ?? "",
          seat_preference: data.seat_preference ?? "",
        }
      : undefined,
  });

  const mutation = useMutation({
    mutationFn: (values: PreferencesFormValues) =>
      upsertPreferences({
        cabin_class: values.cabin_class || "ECONOMY",
        preferred_airlines: values.preferred_airlines
          ? values.preferred_airlines.split(",").map((s) => s.trim())
          : [],
        seat_preference: values.seat_preference || null,
        default_passenger_id: data?.default_passenger_id ?? null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preferences"] });
    },
  });

  return (
    <AppShell>
      <div className="space-y-6">
        <header className="space-y-1">
          <h1 className="text-lg font-semibold text-neutral-900">
            Sở thích chuyến bay
          </h1>
          <p className="text-xs text-neutral-600">
            Tối ưu gợi ý chuyến bay dựa trên thói quen của bạn.
          </p>
        </header>

        <Form {...form}>
          <motion.form
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4 rounded-xl border border-neutral-200 bg-white/80 p-5 shadow-sm"
            onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
          >
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="cabin_class"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Hạng ghế ưa thích</FormLabel>
                    <FormControl>
                      <select
                        {...field}
                        className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                      >
                        <option value="ECONOMY">Phổ thông</option>
                        <option value="BUSINESS">Thương gia</option>
                      </select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="seat_preference"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Vị trí ghế</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="window / aisle" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="preferred_airlines"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Hãng bay ưa thích</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      placeholder="VD: VN,VJ,QH"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={mutation.isPending || isLoading}
              >
                {mutation.isPending ? "Đang lưu..." : "Lưu thay đổi"}
              </Button>
            </div>
          </motion.form>
        </Form>
      </div>
    </AppShell>
  );
}

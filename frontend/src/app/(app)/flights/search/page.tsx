"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { motion, AnimatePresence } from "framer-motion";
import { PlaneTakeoffIcon, PlaneLandingIcon, CalendarIcon, SearchIcon } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { AuthCard } from "@/components/auth/auth-card";
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
import { searchFlights } from "@/services/flight-service";
import type { FlightOffer } from "@/types/flight";

const searchSchema = z.object({
  origin: z.string().length(3, "Mã sân bay 3 ký tự (IATA)"),
  destination: z.string().length(3, "Mã sân bay 3 ký tự (IATA)"),
  depart_date: z.string().min(1, "Vui lòng chọn ngày đi"),
  return_date: z.string().optional(),
  adults: z.coerce.number().min(1).max(9),
  travel_class: z.enum(["ECONOMY", "BUSINESS"]).default("ECONOMY"),
});

type FormValues = z.infer<typeof searchSchema>;

export default function FlightSearchPage() {
  const form = useForm<FormValues>({
    resolver: zodResolver(searchSchema) as any,
    defaultValues: {
      origin: "",
      destination: "",
      depart_date: "",
      return_date: "",
      adults: 1,
      travel_class: "ECONOMY",
    },
  });

  const [offers, setOffers] = useState<FlightOffer[]>([]);

  const { mutate, isPending } = useMutation({
    mutationFn: searchFlights,
    onSuccess: (result) => {
      setOffers(result.offers);
    },
  });

  const onSubmit = (values: FormValues) => {
    setOffers([]);
    mutate({
      ...values,
      currency: "VND",
    });
  };

  return (
    <AppShell>
      <div className="grid gap-8 lg:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
        <AuthCard
          title="Tìm chuyến bay"
          subtitle="Nhập chặng bay và ngày để bắt đầu tìm kiếm."
        >
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4"
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="origin"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Đi từ</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground">
                            <PlaneTakeoffIcon className="h-4 w-4" />
                          </span>
                          <Input
                            {...field}
                            className="pl-9 uppercase"
                            maxLength={3}
                            placeholder="HAN"
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="destination"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Đến</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground">
                            <PlaneLandingIcon className="h-4 w-4" />
                          </span>
                          <Input
                            {...field}
                            className="pl-9 uppercase"
                            maxLength={3}
                            placeholder="SGN"
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="depart_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Ngày đi</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground">
                            <CalendarIcon className="h-4 w-4" />
                          </span>
                          <Input
                            {...field}
                            type="date"
                            className="pl-9"
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="return_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Ngày về (tuỳ chọn)</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground">
                            <CalendarIcon className="h-4 w-4" />
                          </span>
                          <Input
                            {...field}
                            type="date"
                            className="pl-9"
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="adults"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Hành khách</FormLabel>
                      <FormControl>
                        <Input
                          {...field}
                          type="number"
                          min={1}
                          max={9}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="travel_class"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Hạng vé</FormLabel>
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
              </div>

              <Button
                type="submit"
                disabled={isPending}
                className="inline-flex w-full items-center justify-center gap-2"
              >
                <SearchIcon className="h-4 w-4" />
                {isPending ? "Đang tìm chuyến bay..." : "Tìm chuyến bay"}
              </Button>
            </form>
          </Form>
        </AuthCard>

        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-neutral-900">
              Kết quả chuyến bay
            </h2>
          </div>
          <div className="space-y-3">
            <AnimatePresence>
              {isPending &&
                !offers.length &&
                Array.from({ length: 3 }).map((_, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="animate-pulse rounded-xl border border-neutral-200 bg-white/80 p-4 shadow-sm"
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <div className="h-3 w-32 rounded bg-neutral-200" />
                      <div className="h-3 w-16 rounded bg-neutral-200" />
                    </div>
                    <div className="flex gap-2">
                      <div className="h-2 w-20 rounded bg-neutral-100" />
                      <div className="h-2 w-24 rounded bg-neutral-100" />
                    </div>
                  </motion.div>
                ))}

              {!isPending &&
                offers.map((offer) => (
                  <motion.article
                    key={offer.offer_id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                    className="group rounded-xl border border-neutral-200 bg-white/80 p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm font-medium text-neutral-900">
                        {offer.segments[0]?.origin} →{" "}
                        {offer.segments[offer.segments.length - 1]?.destination}
                      </div>
                      <p className="text-sm font-semibold text-primary-600">
                        {offer.total_price.toLocaleString("vi-VN")}{" "}
                        {offer.currency}
                      </p>
                    </div>
                    <p className="text-xs text-neutral-500">
                      {offer.stops === 0
                        ? "Bay thẳng"
                        : `${offer.stops} điểm dừng`}{" "}
                      • ~{Math.round(offer.duration_minutes / 60)} giờ
                    </p>
                  </motion.article>
                ))}

              {!isPending && !offers.length && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="rounded-xl border border-dashed border-neutral-200 bg-white/60 p-6 text-center text-sm text-neutral-500"
                >
                  Nhập thông tin bên trái và bấm &quot;Tìm chuyến bay&quot; để xem gợi ý.
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </section>
      </div>
    </AppShell>
  );
}


"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { motion } from "framer-motion";
import { UserIcon, Trash2Icon } from "lucide-react";

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
  listPassengers,
  createPassenger,
  deletePassenger,
} from "@/services/passenger-service";
import { useRequireAuth } from "@/hooks/use-auth";
import { useAuthStore } from "@/store/auth-store";

const passengerSchema = z.object({
  first_name: z.string().min(1, "Vui lòng nhập tên"),
  last_name: z.string().min(1, "Vui lòng nhập họ"),
  nationality: z.string().optional(),
});

type PassengerFormValues = z.infer<typeof passengerSchema>;

export default function PassengersPage() {
  useRequireAuth();
  const queryClient = useQueryClient();
  const authUser = useAuthStore((s) => s.user);

  const { data, isLoading } = useQuery({
    queryKey: ["passengers"],
    queryFn: listPassengers,
  });

  const form = useForm<PassengerFormValues>({
    resolver: zodResolver(passengerSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      nationality: "",
    },
  });

  const createMutation = useMutation({
    mutationFn: (values: PassengerFormValues) => {
      if (!authUser) {
        throw new Error("Bạn cần đăng nhập để thêm hành khách.");
      }
      return createPassenger({
        user_id: authUser.id,
        ...values,
        gender: null,
        dob: null,
        passport_number: null,
        passport_expiry: null,
      });
    },
    onSuccess: () => {
      form.reset();
      queryClient.invalidateQueries({ queryKey: ["passengers"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deletePassenger(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["passengers"] });
    },
  });

  return (
    <AppShell>
      <div className="grid gap-8 md:grid-cols-[minmax(0,320px)_minmax(0,1fr)]">
        <section className="space-y-4">
          <header className="space-y-1">
            <h1 className="text-lg font-semibold text-neutral-900">
              Hành khách của bạn
            </h1>
            <p className="text-xs text-neutral-600">
              Lưu thông tin hành khách để đặt vé nhanh hơn.
            </p>
          </header>

          <Form {...form}>
            <form
              onSubmit={form.handleSubmit((values) =>
                createMutation.mutate(values),
              )}
              className="space-y-3 rounded-xl border border-neutral-200 bg-white/80 p-4 shadow-sm"
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="first_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tên</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="Ngọc" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="last_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Họ</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="Trần" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="nationality"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Quốc tịch (tùy chọn)</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="VNM" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button
                type="submit"
                disabled={createMutation.isPending}
                className="w-full"
              >
                {createMutation.isPending
                  ? "Đang lưu hành khách..."
                  : "Thêm hành khách"}
              </Button>
            </form>
          </Form>
        </section>

        <section className="space-y-3">
          <h2 className="text-sm font-medium text-neutral-900">
            Danh sách hành khách
          </h2>
          <div className="space-y-3">
            {isLoading ? (
              Array.from({ length: 3 }).map((_, idx) => (
                <div
                  key={idx}
                  className="flex animate-pulse items-center justify-between rounded-xl border border-neutral-200 bg-white/80 p-4 shadow-sm"
                >
                  <div className="flex items-center gap-3">
                    <span className="h-9 w-9 rounded-full bg-neutral-200" />
                    <div className="space-y-2">
                      <div className="h-3 w-32 rounded bg-neutral-200" />
                      <div className="h-3 w-20 rounded bg-neutral-100" />
                    </div>
                  </div>
                </div>
              ))
            ) : data && data.length > 0 ? (
              data.map((p) => (
                <motion.article
                  key={p.id}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white/80 p-4 shadow-sm"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-500/10 text-primary-600">
                      <UserIcon className="h-4 w-4" />
                    </span>
                    <div className="space-y-0.5">
                      <p className="text-sm font-medium text-neutral-900">
                        {p.last_name} {p.first_name}
                      </p>
                      <p className="text-xs text-neutral-500">
                        {p.nationality ?? "Chưa cập nhật"}
                      </p>
                    </div>
                  </div>
                  <Button
                    size="icon-sm"
                    variant="ghost"
                    className="text-neutral-400 hover:text-red-500"
                    onClick={() => deleteMutation.mutate(p.id)}
                  >
                    <Trash2Icon className="h-4 w-4" />
                  </Button>
                </motion.article>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-neutral-200 bg-white/60 p-6 text-center text-sm text-neutral-500">
                Chưa có hành khách nào. Thêm ít nhất một người để đặt vé nhanh
                hơn.
              </div>
            )}
          </div>
        </section>
      </div>
    </AppShell>
  );
}


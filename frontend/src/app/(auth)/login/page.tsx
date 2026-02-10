"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { z } from "zod";
import { motion } from "framer-motion";
import { Loader2Icon, MailIcon, LockIcon } from "lucide-react";

import { AuthCard } from "@/components/auth/auth-card";
import {
  LoginInput,
  loginSchema,
  login as loginRequest,
} from "@/services/auth-service";
import { useAuthStore } from "@/store/auth-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { getApiErrorMessage } from "@/lib/api-error";

type FormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const form = useForm<FormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });
  const setSession = useAuthStore((s) => s.setSession);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const onSubmit = async (values: LoginInput) => {
    setFormError(null);
    setIsSubmitting(true);
    try {
      const res = await loginRequest(values);
      setSession({
        accessToken: res.access_token,
        refreshToken: res.refresh_token,
        user: {
          id: res.user.id,
          email: res.user.email,
          full_name: res.user.full_name,
          avatar_url: res.user.avatar_url,
        },
      });
      router.push("/dashboard");
    } catch (error: unknown) {
      setFormError(
        getApiErrorMessage(
          error,
          "Đăng nhập không thành công. Vui lòng kiểm tra lại thông tin.",
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-neutral-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="flex w-full max-w-md items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.24, ease: [0.16, 1, 0.3, 1] }}
          className="w-full"
        >
          <AuthCard
            title="Chào mừng trở lại"
            subtitle="Đăng nhập để quản lý bookings, hành khách và lịch trình của bạn."
            footer={
              <>
                Chưa có tài khoản?{" "}
                <Link
                  href="/register"
                  className="font-medium text-primary-600 hover:text-primary-700"
                >
                  Đăng ký
                </Link>
              </>
            }
          >
            <Form {...form}>
              <form
                className="space-y-4"
                onSubmit={form.handleSubmit(onSubmit)}
              >
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground">
                            <MailIcon className="h-4 w-4" />
                          </span>
                          <Input
                            {...field}
                            type="email"
                            autoComplete="email"
                            className="pl-9"
                            placeholder="you@example.com"
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Mật khẩu</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground">
                            <LockIcon className="h-4 w-4" />
                          </span>
                          <Input
                            {...field}
                            type="password"
                            autoComplete="current-password"
                            className="pl-9"
                            placeholder="Nhập mật khẩu"
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {formError ? (
                  <motion.div
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-md border border-destructive/20 bg-destructive/5 px-3 py-2 text-xs text-destructive"
                  >
                    {formError}
                  </motion.div>
                ) : null}

                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="h-10 w-full"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                      Đang đăng nhập...
                    </>
                  ) : (
                    "Đăng nhập"
                  )}
                </Button>
              </form>
            </Form>
          </AuthCard>
        </motion.div>
      </div>
    </div>
  );
}


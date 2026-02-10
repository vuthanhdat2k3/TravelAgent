"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { motion } from "framer-motion";
import { Loader2Icon, MailIcon, LockIcon, UserIcon, PhoneIcon } from "lucide-react";

import { AuthCard } from "@/components/auth/auth-card";
import {
  register as registerRequest,
  registerSchema,
  RegisterInput,
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

type FormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const form = useForm<FormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      phone: "",
      password: "",
    },
  });
  const setSession = useAuthStore((s) => s.setSession);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const onSubmit = async (values: RegisterInput) => {
    setFormError(null);
    setIsSubmitting(true);
    try {
      await registerRequest(values);
      const loginRes = await loginRequest({
        email: values.email,
        password: values.password,
      });
      setSession({
        accessToken: loginRes.access_token,
        refreshToken: loginRes.refresh_token,
        user: {
          id: loginRes.user.id,
          email: loginRes.user.email,
          full_name: loginRes.user.full_name,
          avatar_url: loginRes.user.avatar_url,
        },
      });
      router.push("/dashboard");
    } catch (error: unknown) {
      setFormError(
        getApiErrorMessage(error, "Đăng ký không thành công. Vui lòng thử lại."),
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
            title="Tạo tài khoản Travel Agent"
            subtitle="Lưu thông tin hành khách, lịch sử tìm kiếm và quản lý bookings của bạn."
            footer={
              <>
                Đã có tài khoản?{" "}
                <Link
                  href="/login"
                  className="font-medium text-primary hover:text-primary/90"
                >
                  Đăng nhập
                </Link>
              </>
            }
          >
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="full_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Họ tên</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground">
                            <UserIcon className="h-4 w-4" />
                          </span>
                          <Input
                            {...field}
                            autoComplete="name"
                            className="pl-9"
                            placeholder="Nguyễn Văn A"
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

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
                  name="phone"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Số điện thoại</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted-foreground">
                            <PhoneIcon className="h-4 w-4" />
                          </span>
                          <Input
                            {...field}
                            autoComplete="tel"
                            className="pl-9"
                            placeholder="+84..."
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
                            autoComplete="new-password"
                            className="pl-9"
                            placeholder="Tối thiểu 6 ký tự"
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
                      Đang tạo tài khoản...
                    </>
                  ) : (
                    "Đăng ký"
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


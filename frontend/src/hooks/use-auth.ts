"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/auth-store";

export function useRequireAuth() {
  const setSession = useAuthStore((s) => s.setSession);
  const clearSession = useAuthStore((s) => s.clearSession);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const accessToken = window.localStorage.getItem("ta_access_token");
    const refreshToken = window.localStorage.getItem("ta_refresh_token");
    const userRaw = window.localStorage.getItem("ta_user");

    // If any auth data is missing, redirect immediately
    if (!accessToken || !refreshToken || !userRaw) {
      clearSession();
      // Use window.location for hard redirect or use router from next/navigation
      window.location.href = "/login";
      return;
    }

    try {
      const user = JSON.parse(userRaw);
      // setSession also syncs the cookie for SSR prefetching
      setSession({ accessToken, refreshToken, user });
    } catch {
      clearSession();
      window.location.href = "/login";
    }
  }, [setSession, clearSession]);
}


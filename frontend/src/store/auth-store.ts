import { create } from "zustand";

type AuthUser = {
  id: string;
  email: string;
  full_name?: string | null;
  avatar_url?: string | null;
};

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  setSession: (payload: {
    accessToken: string;
    refreshToken: string;
    user: AuthUser;
  }) => void;
  clearSession: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  setSession: ({ accessToken, refreshToken, user }) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("ta_access_token", accessToken);
      window.localStorage.setItem("ta_refresh_token", refreshToken);
      window.localStorage.setItem("ta_user", JSON.stringify(user));
    }
    set({ accessToken, refreshToken, user });
  },
  clearSession: () => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("ta_access_token");
      window.localStorage.removeItem("ta_refresh_token");
      window.localStorage.removeItem("ta_user");
    }
    set({ accessToken: null, refreshToken: null, user: null });
  },
}));


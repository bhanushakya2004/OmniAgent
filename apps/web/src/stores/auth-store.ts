import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "user" | "merchant";
  preferred_language: string;
  is_active: boolean;
  created_at: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
  logout: () => void;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isLoading: false,
      setAuth: (user, token) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("omni_access_token", token);
          // Set role cookie for Next.js middleware routing
          document.cookie = `omni_role=${user.role}; path=/; max-age=1209600; SameSite=Lax`;
          document.cookie = `omni_logged_in=true; path=/; max-age=1209600; SameSite=Lax`;
        }
        set({ user, accessToken: token });
      },
      clearAuth: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("omni_access_token");
          document.cookie = "omni_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
          document.cookie = "omni_logged_in=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        }
        set({ user: null, accessToken: null });
      },
      logout: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("omni_access_token");
          document.cookie = "omni_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
          document.cookie = "omni_logged_in=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        }
        set({ user: null, accessToken: null });
      },
      setUser: (user) => set({ user }),
    }),
    {
      name: "omni-auth-storage",
      partialize: (state) => ({ user: state.user, accessToken: state.accessToken }),
    }
  )
);

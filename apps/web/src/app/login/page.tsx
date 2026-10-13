"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { ArrowRight, ShoppingBag, Store, Sparkles, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { useAuthStore, type User } from "@/stores/auth-store";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectUrl = searchParams.get("redirect");
  const setAuth = useAuthStore((state) => state.setAuth);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (values: LoginFormValues) => {
    setIsLoading(true);
    try {
      const data = await apiClient<LoginResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(values),
      });

      setAuth(data.user, data.access_token);
      toast.success(`Welcome back, ${data.user.full_name}!`);

      if (redirectUrl) {
        router.push(redirectUrl);
      } else if (data.user.role === "merchant") {
        router.push("/merchant");
      } else {
        router.push("/app");
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Invalid credentials";
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const fillCredentials = (email: string, pass: string) => {
    setValue("email", email);
    setValue("password", pass);
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 py-12 dark:bg-slate-950 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-slate-200 bg-white p-8 shadow-xl dark:border-slate-800 dark:bg-slate-900">
        <div className="text-center">
          <Link href="/" className="inline-flex items-center gap-2">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-600 text-white shadow-md shadow-orange-500/20">
              <ShoppingBag className="h-5 w-5" />
            </span>
            <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              OmniMission <span className="text-orange-600">AI</span>
            </span>
          </Link>
          <h2 className="mt-4 text-xl font-semibold text-slate-800 dark:text-slate-100">
            Sign in to your account
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Or{" "}
            <Link href="/register" className="font-medium text-orange-600 hover:underline">
              create a new account
            </Link>
          </p>
        </div>

        {/* Demo Account Quick-Fill Buttons */}
        <div className="rounded-xl border border-orange-200 bg-orange-50/50 p-3 dark:border-orange-950/50 dark:bg-orange-950/20">
          <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-orange-700 dark:text-orange-400">
            <Sparkles className="h-3.5 w-3.5" /> Demo Credentials
          </div>
          <div className="mt-2 grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => fillCredentials("shopper@omnimission.ai", "Shopper123!")}
              className="flex items-center justify-center gap-1.5 rounded-lg border border-orange-200 bg-white px-2 py-1.5 text-xs font-medium text-slate-800 shadow-sm transition hover:bg-orange-100 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              <ShoppingBag className="h-3.5 w-3.5 text-orange-600" /> Shopper Demo
            </button>
            <button
              type="button"
              onClick={() => fillCredentials("merchant@omnimission.ai", "Merchant123!")}
              className="flex items-center justify-center gap-1.5 rounded-lg border border-orange-200 bg-white px-2 py-1.5 text-xs font-medium text-slate-800 shadow-sm transition hover:bg-orange-100 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              <Store className="h-3.5 w-3.5 text-indigo-600" /> Merchant Demo
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-slate-600 dark:text-slate-400">
              Email Address
            </label>
            <input
              {...register("email")}
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              className="mt-1 block w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-500/20 dark:border-slate-700 dark:text-white"
            />
            {errors.email && (
              <p className="mt-1 text-xs text-rose-500">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-slate-600 dark:text-slate-400">
              Password
            </label>
            <input
              {...register("password")}
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              className="mt-1 block w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-500/20 dark:border-slate-700 dark:text-white"
            />
            {errors.password && (
              <p className="mt-1 text-xs text-rose-500">{errors.password.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-orange-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-orange-600/30 transition hover:bg-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                Sign In <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

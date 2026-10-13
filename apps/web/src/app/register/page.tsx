"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { toast } from "sonner";
import { ArrowRight, ShoppingBag, Store, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { useAuthStore, type User } from "@/stores/auth-store";

const registerSchema = z.object({
  full_name: z.string().min(2, "Full name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  role: z.enum(["user", "merchant"]),
  store_name: z.string().optional(),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

interface RegisterResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export default function RegisterPage() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);
  const [selectedRole, setSelectedRole] = useState<"user" | "merchant">("user");
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      role: "user",
      store_name: "",
    },
  });

  const onRoleChange = (role: "user" | "merchant") => {
    setSelectedRole(role);
    setValue("role", role);
  };

  const onSubmit = async (values: RegisterFormValues) => {
    setIsLoading(true);
    try {
      const data = await apiClient<RegisterResponse>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify(values),
      });

      setAuth(data.user, data.access_token);
      toast.success("Account created successfully!");

      if (data.user.role === "merchant") {
        router.push("/merchant");
      } else {
        router.push("/app");
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Registration failed";
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 py-12 dark:bg-slate-950 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-6 rounded-2xl border border-slate-200 bg-white p-8 shadow-xl dark:border-slate-800 dark:bg-slate-900">
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
            Create your account
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-orange-600 hover:underline">
              Sign in
            </Link>
          </p>
        </div>

        {/* Role Selector Tabs */}
        <div>
          <label className="block text-xs font-medium uppercase tracking-wider text-slate-600 dark:text-slate-400">
            Select Your Role
          </label>
          <div className="mt-1.5 grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => onRoleChange("user")}
              className={`flex items-center justify-center gap-2 rounded-xl border p-3 text-sm font-medium transition ${
                selectedRole === "user"
                  ? "border-orange-600 bg-orange-50/50 text-orange-700 dark:bg-orange-950/30 dark:text-orange-400"
                  : "border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-400 dark:hover:bg-slate-800"
              }`}
            >
              <ShoppingBag className="h-4 w-4" /> Shopper
            </button>
            <button
              type="button"
              onClick={() => onRoleChange("merchant")}
              className={`flex items-center justify-center gap-2 rounded-xl border p-3 text-sm font-medium transition ${
                selectedRole === "merchant"
                  ? "border-indigo-600 bg-indigo-50/50 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-400"
                  : "border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-400 dark:hover:bg-slate-800"
              }`}
            >
              <Store className="h-4 w-4" /> Store Merchant
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-slate-600 dark:text-slate-400">
              Full Name
            </label>
            <input
              {...register("full_name")}
              type="text"
              placeholder="e.g. Arjun Patel"
              className="mt-1 block w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-500/20 dark:border-slate-700 dark:text-white"
            />
            {errors.full_name && (
              <p className="mt-1 text-xs text-rose-500">{errors.full_name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-slate-600 dark:text-slate-400">
              Email Address
            </label>
            <input
              {...register("email")}
              type="email"
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
              placeholder="Minimum 8 characters"
              className="mt-1 block w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-500/20 dark:border-slate-700 dark:text-white"
            />
            {errors.password && (
              <p className="mt-1 text-xs text-rose-500">{errors.password.message}</p>
            )}
          </div>

          {selectedRole === "merchant" && (
            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Primary Store Name
              </label>
              <input
                {...register("store_name")}
                type="text"
                placeholder="e.g. FreshMart Indiranagar"
                className="mt-1 block w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 dark:border-slate-700 dark:text-white"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className={`flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white shadow-md transition disabled:opacity-50 ${
              selectedRole === "merchant"
                ? "bg-indigo-600 shadow-indigo-600/30 hover:bg-indigo-500"
                : "bg-orange-600 shadow-orange-600/30 hover:bg-orange-500"
            }`}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                Create Account <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

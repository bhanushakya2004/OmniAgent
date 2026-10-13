"use client";

import React from "react";
import Link from "next/link";
import { Store, ChevronDown, LogOut, ArrowLeft, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/auth-store";
import type { MerchantStore } from "@/lib/merchant-api";

interface StoreHeaderProps {
  stores: MerchantStore[];
  selectedStoreId: string;
  onSelectStore: (storeId: string) => void;
  isLoading?: boolean;
  onRefresh?: () => void;
}

export function StoreHeader({
  stores,
  selectedStoreId,
  onSelectStore,
  isLoading,
  onRefresh,
}: StoreHeaderProps) {
  const { user, logout } = useAuthStore();
  const currentStore = stores.find((s) => s.id === selectedStoreId) || stores[0];

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/95">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        {/* Brand & Store Selector */}
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-md shadow-emerald-500/20">
            <Store className="h-5 w-5" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                Merchant Ops
              </span>
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                Live Store
              </Badge>
            </div>

            {/* Store switcher */}
            <div className="relative mt-0.5">
              <select
                value={selectedStoreId}
                onChange={(e) => onSelectStore(e.target.value)}
                className="cursor-pointer appearance-none bg-transparent pr-7 text-base font-bold text-slate-900 focus:outline-none dark:text-slate-100"
              >
                {stores.map((store) => (
                  <option key={store.id} value={store.id} className="dark:bg-slate-900">
                    {store.name} ({store.city})
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-0 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            </div>
          </div>
        </div>

        {/* Store Metadata & Controls */}
        <div className="flex items-center gap-3">
          {currentStore && (
            <div className="hidden text-right lg:block">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {currentStore.address.slice(0, 45)}...
              </p>
              <p className="text-xs font-medium text-slate-700 dark:text-slate-300">
                {currentStore.total_skus} Grounded SKUs In Store
              </p>
            </div>
          )}

          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={isLoading}
              className="h-9 gap-1.5 text-xs text-slate-600 dark:text-slate-300"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
              <span className="hidden sm:inline">Sync</span>
            </Button>
          )}

          <Link href="/">
            <Button variant="ghost" size="sm" className="h-9 gap-1.5 text-xs text-slate-600 dark:text-slate-300">
              <ArrowLeft className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Landing</span>
            </Button>
          </Link>

          <div className="h-6 w-px bg-slate-200 dark:bg-slate-800" />

          {/* User info & Logout */}
          <div className="flex items-center gap-2">
            <div className="hidden sm:block text-right">
              <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                {user?.full_name || "Store Manager"}
              </p>
              <p className="text-[10px] text-slate-500 capitalize">{user?.role || "merchant"}</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={logout}
              title="Sign Out"
              className="h-9 w-9 p-0 text-slate-500 hover:text-rose-600 dark:text-slate-400 dark:hover:text-rose-400"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}

"use client";

import Link from "next/link";
import { ArrowLeft, ShoppingBag } from "lucide-react";

export default function ShopperHomePlaceholder() {
  return (
    <div className="min-h-screen bg-slate-50 p-6 dark:bg-slate-950">
      <div className="mx-auto max-w-4xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-orange-600 text-white">
              <ShoppingBag className="h-5 w-5" />
            </span>
            <h1 className="text-xl font-bold">Shopper Mission Center</h1>
          </div>
          <Link
            href="/"
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 dark:hover:text-white"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Landing
          </Link>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Shopper Mission workspace initializing for M7 integration.
          </p>
        </div>
      </div>
    </div>
  );
}

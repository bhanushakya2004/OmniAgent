"use client";

import Link from "next/link";
import { ArrowLeft, Store } from "lucide-react";

export default function MerchantHomePlaceholder() {
  return (
    <div className="min-h-screen bg-slate-50 p-6 dark:bg-slate-950">
      <div className="mx-auto max-w-5xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white">
              <Store className="h-5 w-5" />
            </span>
            <h1 className="text-xl font-bold">Merchant Command Portal</h1>
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
            Merchant operations portal initializing for M9 integration.
          </p>
        </div>
      </div>
    </div>
  );
}

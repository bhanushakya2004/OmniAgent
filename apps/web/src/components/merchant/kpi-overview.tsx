"use client";

import React from "react";
import { ShoppingBag, IndianRupee, AlertTriangle, CheckSquare, TrendingUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { StoreOverviewKpis } from "@/lib/merchant-api";

interface KpiOverviewProps {
  kpis: StoreOverviewKpis | null;
  isLoading: boolean;
  onViewTasksTab?: () => void;
  onViewAtRiskSkus?: () => void;
}

export function KpiOverview({
  kpis,
  isLoading,
  onViewTasksTab,
  onViewAtRiskSkus,
}: KpiOverviewProps) {
  if (isLoading || !kpis) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-28 animate-pulse rounded-2xl border border-slate-200 bg-slate-100/60 dark:border-slate-800 dark:bg-slate-900/60"
          />
        ))}
      </div>
    );
  }

  const gmv = Number(kpis.total_grounded_gmv).toLocaleString("en-IN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {/* 1. Missions Telemetry */}
      <Card className="rounded-2xl border-slate-200 bg-white shadow-sm transition-all hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Shopper Missions
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
              <ShoppingBag className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-slate-100">
              {kpis.total_missions}
            </span>
            <span className="flex items-center text-xs font-medium text-emerald-600 dark:text-emerald-400">
              <TrendingUp className="mr-0.5 h-3 w-3" /> Live
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Conversational baskets routed to this store
          </p>
        </CardContent>
      </Card>

      {/* 2. Grounded GMV */}
      <Card className="rounded-2xl border-slate-200 bg-white shadow-sm transition-all hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Grounded GMV
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400">
              <IndianRupee className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-1">
            <span className="text-lg font-bold text-slate-700 dark:text-slate-300">₹</span>
            <span className="text-3xl font-extrabold text-slate-900 dark:text-slate-100">
              {gmv}
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Real in-stock item conversions captured
          </p>
        </CardContent>
      </Card>

      {/* 3. At Risk SKUs */}
      <Card
        onClick={onViewAtRiskSkus}
        className={`cursor-pointer rounded-2xl border-slate-200 bg-white shadow-sm transition-all hover:shadow-md dark:border-slate-800 dark:bg-slate-900 ${
          kpis.at_risk_skus_count > 0 ? "hover:border-amber-300 dark:hover:border-amber-700" : ""
        }`}
      >
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Stockout Risk SKUs
            </span>
            <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${
              kpis.at_risk_skus_count > 0
                ? "bg-amber-100 text-amber-700 dark:bg-amber-950/80 dark:text-amber-300"
                : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
            }`}>
              <AlertTriangle className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={`text-3xl font-extrabold ${
              kpis.at_risk_skus_count > 0
                ? "text-amber-600 dark:text-amber-400"
                : "text-slate-900 dark:text-slate-100"
            }`}>
              {kpis.at_risk_skus_count}
            </span>
            {kpis.at_risk_skus_count > 0 && (
              <Badge variant="outline" className="border-amber-200 bg-amber-50 text-[10px] text-amber-700 dark:border-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
                Action Needed
              </Badge>
            )}
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            SKUs at or below restock threshold (≤5)
          </p>
        </CardContent>
      </Card>

      {/* 4. Open Restock Tasks */}
      <Card
        onClick={onViewTasksTab}
        className="cursor-pointer rounded-2xl border-slate-200 bg-white shadow-sm transition-all hover:border-indigo-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-700"
      >
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Restock Tasks
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-50 text-teal-600 dark:bg-teal-950/60 dark:text-teal-400">
              <CheckSquare className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-slate-100">
              {kpis.open_restock_tasks_count}
            </span>
            <span className="text-xs font-medium text-teal-600 dark:text-teal-400">
              Pending
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Shelf audits awaiting physical replenishment
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

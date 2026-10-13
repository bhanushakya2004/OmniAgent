"use client";

import React from "react";
import { Radar, Zap, ArrowUpRight, Flame, Search, Info } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { DemandSignal } from "@/lib/merchant-api";

interface DemandRadarProps {
  signals: DemandSignal[];
  isLoading: boolean;
}

export function DemandRadar({ signals, isLoading }: DemandRadarProps) {
  if (isLoading) {
    return (
      <Card className="rounded-2xl border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="h-44 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800/60" />
      </Card>
    );
  }

  return (
    <Card className="rounded-2xl border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <CardHeader className="pb-3">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
              <Radar className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-slate-900 dark:text-slate-100">
                Demand Radar & Intent Signals
              </CardTitle>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Real-time neighborhood customer searches & stockout substitution triggers
              </p>
            </div>
          </div>
          <Badge variant="outline" className="w-fit border-indigo-200 bg-indigo-50 text-xs text-indigo-700 dark:border-indigo-800 dark:bg-indigo-950/50 dark:text-indigo-300">
            <Zap className="mr-1 h-3 w-3 fill-indigo-500 text-indigo-500" />
            Live Neighborhood Telemetry
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        {signals.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 p-8 text-center dark:border-slate-800">
            <Info className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-2 text-sm font-medium text-slate-700 dark:text-slate-300">
              No demand signals captured yet
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Shoppers executing missions in this store radius will populate the radar.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
              {signals.map((sig, idx) => {
                const isHighTrend = sig.trending_score >= 1.0;
                return (
                  <div
                    key={`${sig.query}-${idx}`}
                    className="flex flex-col justify-between rounded-xl border border-slate-100 bg-slate-50/70 p-3.5 transition-all hover:border-slate-200 hover:bg-slate-50 hover:shadow-sm dark:border-slate-800/80 dark:bg-slate-800/40 dark:hover:border-slate-700"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-900 dark:text-slate-100">
                        <Search className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                        <span className="line-clamp-1 italic">"{sig.query}"</span>
                      </div>
                      {isHighTrend ? (
                        <span className="flex items-center text-[10px] font-bold text-rose-600 dark:text-rose-400 shrink-0">
                          <Flame className="h-3 w-3 fill-rose-500 text-rose-500 mr-0.5" /> High
                        </span>
                      ) : (
                        <span className="text-[10px] font-medium text-slate-400 shrink-0">
                          Normal
                        </span>
                      )}
                    </div>

                    <div className="mt-2.5 flex items-center justify-between border-t border-slate-200/60 pt-2 text-[11px] dark:border-slate-700/60">
                      <span className="text-slate-500 dark:text-slate-400">
                        Requested: <strong className="text-slate-800 dark:text-slate-200">{sig.mention_count}x</strong>
                      </span>
                      {sig.unmet_count > 0 ? (
                        <span className="font-semibold text-amber-600 dark:text-amber-400">
                          {sig.unmet_count} Substituted
                        </span>
                      ) : (
                        <span className="text-emerald-600 dark:text-emerald-400">
                          100% Grounded
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex items-center gap-2 rounded-xl bg-amber-50/60 p-3 text-xs text-amber-800 dark:bg-amber-950/30 dark:text-amber-300 border border-amber-200/60 dark:border-amber-900/40">
              <Info className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
              <span>
                <strong>Merchandising Recommendation:</strong> Queries with substitutions represent instant lost revenue. Consider stocking more plant protein or premium chocolate to prevent substitution fallbacks.
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

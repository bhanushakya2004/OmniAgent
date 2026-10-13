"use client";

import React, { useState, useMemo } from "react";
import {
  CheckSquare,
  Check,
  MapPin,
  Clock,
  Sparkles,
  ArrowRight,
  RefreshCw,
  XCircle,
  PackageCheck,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { RestockTask } from "@/lib/merchant-api";
import { updateRestockTask } from "@/lib/merchant-api";

interface RestockTasksKanbanProps {
  tasks: RestockTask[];
  isLoading: boolean;
  onRefresh: () => void;
}

export function RestockTasksKanban({
  tasks,
  isLoading,
  onRefresh,
}: RestockTasksKanbanProps) {
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [updatingTaskId, setUpdatingTaskId] = useState<string | null>(null);

  const handleUpdateStatus = async (
    taskId: string,
    newStatus: "pending" | "approved" | "completed" | "dismissed"
  ) => {
    setUpdatingTaskId(taskId);
    try {
      await updateRestockTask(taskId, newStatus);
      onRefresh();
    } catch (err) {
      console.error("Failed to update restock task", err);
    } finally {
      setUpdatingTaskId(null);
    }
  };

  const filteredTasks = useMemo(() => {
    if (statusFilter === "all") return tasks;
    return tasks.filter((t) => t.status === statusFilter);
  }, [tasks, statusFilter]);

  const pendingCount = tasks.filter((t) => t.status === "pending").length;
  const approvedCount = tasks.filter((t) => t.status === "approved").length;
  const completedCount = tasks.filter((t) => t.status === "completed").length;

  return (
    <Card className="rounded-2xl border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <CardHeader className="border-b border-slate-100 pb-4 dark:border-slate-800">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400">
              <CheckSquare className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-slate-900 dark:text-slate-100">
                Replenishment Restock Tasks
              </CardTitle>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Review audit drafts, approve work orders, and auto-increment inventory upon shelf stocking
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto">
            {[
              { id: "all", label: `All (${tasks.length})` },
              { id: "pending", label: `Pending (${pendingCount})` },
              { id: "approved", label: `Approved (${approvedCount})` },
              { id: "completed", label: `Restocked (${completedCount})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`whitespace-nowrap rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                  statusFilter === tab.id
                    ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-6">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-slate-500">
            <RefreshCw className="mx-auto h-6 w-6 animate-spin text-slate-400 mb-2" />
            Loading replenishment tasks...
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500">
            No restock tasks found for this filter.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredTasks.map((task) => {
              const isUpdating = updatingTaskId === task.id;
              const isPending = task.status === "pending";
              const isApproved = task.status === "approved";
              const isCompleted = task.status === "completed";

              return (
                <div
                  key={task.id}
                  className={`flex flex-col justify-between rounded-2xl border p-4 transition-all shadow-sm ${
                    isCompleted
                      ? "border-emerald-200 bg-emerald-50/30 dark:border-emerald-900/40 dark:bg-emerald-950/20"
                      : isApproved
                      ? "border-amber-200 bg-amber-50/40 dark:border-amber-900/40 dark:bg-amber-950/20"
                      : "border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900"
                  }`}
                >
                  <div>
                    {/* Header: Name & Status */}
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                          {task.product_name}
                        </h4>
                        <span className="inline-flex items-center gap-1 font-mono text-[11px] text-slate-500 mt-0.5">
                          <MapPin className="h-3 w-3 text-emerald-600" />
                          Aisle {task.aisle} · Bay {task.bay} · Shelf {task.shelf}
                        </span>
                      </div>

                      <Badge
                        variant="outline"
                        className={
                          isCompleted
                            ? "border-emerald-300 bg-emerald-100/80 text-[10px] text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300"
                            : isApproved
                            ? "border-amber-300 bg-amber-100/80 text-[10px] text-amber-800 dark:bg-amber-900/50 dark:text-amber-300"
                            : "border-slate-300 bg-slate-100 text-[10px] text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                        }
                      >
                        {task.status.toUpperCase()}
                      </Badge>
                    </div>

                    {/* Stock Metrics */}
                    <div className="mt-3 flex items-center justify-between rounded-xl bg-slate-50 p-2.5 text-xs dark:bg-slate-800/60">
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase font-semibold">
                          Current Facing
                        </span>
                        <p className="font-mono font-bold text-slate-700 dark:text-slate-300">
                          {task.current_qty} units
                        </p>
                      </div>

                      <ArrowRight className="h-3.5 w-3.5 text-slate-400" />

                      <div className="text-right">
                        <span className="text-[10px] text-slate-400 uppercase font-semibold">
                          Recommended
                        </span>
                        <p className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                          +{task.recommended_qty} units
                        </p>
                      </div>
                    </div>

                    {/* Reason text */}
                    <p className="mt-2.5 text-[11px] text-slate-600 dark:text-slate-400 italic">
                      "{task.reason}"
                    </p>
                  </div>

                  {/* Action Controls */}
                  <div className="mt-4 border-t border-slate-100 pt-3 dark:border-slate-800">
                    {isPending && (
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          disabled={isUpdating}
                          onClick={() => handleUpdateStatus(task.id, "approved")}
                          className="flex-1 bg-amber-600 hover:bg-amber-700 text-white text-xs gap-1 font-semibold"
                        >
                          <Check className="h-3 w-3" /> Approve Task
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={isUpdating}
                          onClick={() => handleUpdateStatus(task.id, "dismissed")}
                          className="text-xs text-slate-500 hover:text-rose-600"
                        >
                          Dismiss
                        </Button>
                      </div>
                    )}

                    {isApproved && (
                      <Button
                        size="sm"
                        disabled={isUpdating}
                        onClick={() => handleUpdateStatus(task.id, "completed")}
                        className="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-xs gap-1.5 font-semibold"
                      >
                        <PackageCheck className="h-3.5 w-3.5" />
                        Mark Restocked (+{task.recommended_qty} to Stock)
                      </Button>
                    )}

                    {isCompleted && (
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-300">
                        <Check className="h-3.5 w-3.5 text-emerald-600" />
                        Restocked & Inventory Reconciled
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

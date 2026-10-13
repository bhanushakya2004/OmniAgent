"use client";

import React from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ShoppingBag,
  Store as StoreIcon,
  MapPin,
  Plus,
  Minus,
  Trash2,
  RefreshCw,
  TrendingDown,
  CheckCircle,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { formatInr } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export interface BasketItemData {
  id: string;
  mission_id: string;
  product_id?: string | null;
  product_name?: string | null;
  product_brand?: string | null;
  requested_label: string;
  quantity: number;
  unit_price?: number | string | null;
  subtotal?: number | string | null;
  store_id?: string | null;
  store_name?: string | null;
  status: string;
  reason?: string | null;
  aisle?: number | null;
  bay?: number | null;
  shelf?: number | null;
}

export interface MissionDetailData {
  id: string;
  raw_text: string;
  status: string;
  total_cost?: number | string | null;
  constraints?: {
    budget_inr?: number;
    dietary_tags?: string[];
    servings?: number;
    is_travel_size?: boolean;
  } | null;
  items: BasketItemData[];
}

interface BasketViewProps {
  mission: MissionDetailData;
  onRefresh: () => void;
}

export function BasketView({ mission, onRefresh }: BasketViewProps): React.JSX.Element {
  const queryClient = useQueryClient();

  // Mutation to update quantity or delete item
  const updateQtyMutation = useMutation({
    mutationFn: async ({ itemId, quantity }: { itemId: string; quantity: number }) => {
      return await apiClient.patch(`/api/v1/missions/${mission.id}/items/${itemId}`, {
        quantity,
      });
    },
    onSuccess: () => {
      onRefresh();
    },
  });

  // Group items by store
  const itemsByStore: Record<string, BasketItemData[]> = {};
  mission.items.forEach((item) => {
    const sName = item.store_name || "Primary Store";
    if (!itemsByStore[sName]) itemsByStore[sName] = [];
    itemsByStore[sName].push(item);
  });

  const totalCostNum =
    typeof mission.total_cost === "string"
      ? parseFloat(mission.total_cost)
      : (mission.total_cost ?? 0);
  const budgetLimit = mission.constraints?.budget_inr ?? null;
  const isOverBudget = budgetLimit !== null && totalCostNum > budgetLimit;

  return (
    <Card className="p-6 bg-card/60 backdrop-blur-md border-border/80 shadow-md">
      {/* Header & Budget Meter */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-border/60">
        <div>
          <div className="flex items-center gap-2">
            <ShoppingBag className="w-5 h-5 text-primary" />
            <h3 className="font-bold text-lg">Grounded Physical Basket</h3>
            <Badge variant="accent">{mission.items.length} Items</Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Every product is strictly validated against verified store inventory and shelf coordinates.
          </p>
        </div>

        <div className="flex items-center gap-4 bg-muted/40 p-3 rounded-2xl border border-border/60">
          <div>
            <span className="text-[11px] text-muted-foreground uppercase font-semibold block">
              Total Spend
            </span>
            <span className="text-xl font-extrabold text-foreground">
              {formatInr(mission.total_cost)}
            </span>
          </div>

          {budgetLimit !== null && (
            <div className="border-l border-border/60 pl-4">
              <span className="text-[11px] text-muted-foreground uppercase font-semibold block">
                Budget Target
              </span>
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-bold text-muted-foreground">
                  {formatInr(budgetLimit)}
                </span>
                <Badge variant={isOverBudget ? "destructive" : "accent"} className="text-[10px]">
                  {isOverBudget ? "Over Budget" : "Fits Budget"}
                </Badge>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Stores Breakdown */}
      <div className="mt-5 space-y-6">
        {Object.entries(itemsByStore).map(([storeName, items]) => {
          const storeSubtotal = items.reduce((acc, it) => {
            const sub = typeof it.subtotal === "string" ? parseFloat(it.subtotal) : (it.subtotal ?? 0);
            return acc + sub;
          }, 0);

          return (
            <div key={storeName} className="space-y-3">
              {/* Store Section Title */}
              <div className="flex items-center justify-between bg-muted/30 p-2.5 rounded-xl border border-border/40">
                <div className="flex items-center gap-2">
                  <StoreIcon className="w-4 h-4 text-primary" />
                  <h4 className="font-bold text-sm text-foreground">{storeName}</h4>
                  <Badge variant="secondary" className="text-[11px]">
                    {items.length} {items.length === 1 ? "item" : "items"}
                  </Badge>
                </div>
                <span className="text-xs font-semibold text-muted-foreground">
                  Subtotal: <strong className="text-foreground">{formatInr(storeSubtotal)}</strong>
                </span>
              </div>

              {/* Items List */}
              <div className="space-y-2">
                {items.map((item) => {
                  const isSubstituted = item.status === "substituted";
                  return (
                    <div
                      key={item.id}
                      className={`p-3.5 rounded-xl border transition-all ${
                        isSubstituted
                          ? "bg-amber-500/5 border-amber-500/30"
                          : "bg-card border-border/70 hover:border-border"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-semibold text-sm text-foreground">
                              {item.product_name || item.requested_label}
                            </span>
                            {item.product_brand && (
                              <span className="text-xs text-muted-foreground font-medium">
                                ({item.product_brand})
                              </span>
                            )}
                            {isSubstituted && (
                              <Badge variant="warning" className="text-[10px]">
                                <RefreshCw className="w-2.5 h-2.5 mr-1" />
                                Smart Substitute
                              </Badge>
                            )}
                          </div>

                          {/* Physical Aisle Tag */}
                          <div className="flex items-center gap-2 text-xs text-muted-foreground pt-0.5">
                            <span className="inline-flex items-center gap-1 font-mono px-2 py-0.5 rounded bg-muted text-foreground/80 font-medium">
                              <MapPin className="w-3 h-3 text-primary" />
                              Aisle {item.aisle ?? 1} • Bay {item.bay ?? 1} • Shelf {item.shelf ?? 1}
                            </span>
                            <span>•</span>
                            <span>{formatInr(item.unit_price)} each</span>
                          </div>

                          {isSubstituted && item.reason && (
                            <p className="text-xs text-amber-700 dark:text-amber-300 font-medium pt-1">
                              💡 {item.reason}
                            </p>
                          )}
                        </div>

                        {/* Price & Quantity Controls */}
                        <div className="flex flex-col items-end gap-2 shrink-0">
                          <span className="font-bold text-sm text-foreground">
                            {formatInr(item.subtotal)}
                          </span>

                          <div className="flex items-center gap-1.5 bg-muted/60 rounded-lg p-1 border border-border/60">
                            <button
                              type="button"
                              onClick={() =>
                                updateQtyMutation.mutate({
                                  itemId: item.id,
                                  quantity: item.quantity - 1,
                                })
                              }
                              disabled={updateQtyMutation.isPending}
                              className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-background transition-colors disabled:opacity-50"
                              title="Decrease quantity"
                            >
                              {item.quantity === 1 ? (
                                <Trash2 className="w-3.5 h-3.5 text-destructive" />
                              ) : (
                                <Minus className="w-3.5 h-3.5" />
                              )}
                            </button>

                            <span className="w-6 text-center text-xs font-bold font-mono">
                              {item.quantity}
                            </span>

                            <button
                              type="button"
                              onClick={() =>
                                updateQtyMutation.mutate({
                                  itemId: item.id,
                                  quantity: item.quantity + 1,
                                })
                              }
                              disabled={updateQtyMutation.isPending}
                              className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-background transition-colors disabled:opacity-50"
                              title="Increase quantity"
                            >
                              <Plus className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

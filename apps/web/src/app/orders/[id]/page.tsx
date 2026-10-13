"use client";

import React, { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  CheckCircle2,
  Clock,
  Store,
  MapPin,
  ShoppingBag,
  Sparkles,
  ArrowRight,
  Receipt,
  QrCode,
  Package,
  Layers,
  ArrowLeft,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { formatInr } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface OrderItem {
  id: string;
  product_id: string;
  sku: string;
  product_name: string;
  qty: number;
  unit_price: number;
  subtotal: number;
  aisle: number;
  bay: number;
  shelf: number;
}

interface OrderDetail {
  id: string;
  order_number: string;
  store_id: string;
  status: string;
  total_amount: number;
  currency: string;
  pickup_time_slot?: string | null;
  payment_status: string;
  payment_method: string;
  created_at: string;
  items: OrderItem[];
}

export default function OrderConfirmationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}): React.JSX.Element {
  const resolvedParams = use(params);
  const orderId = resolvedParams.id;

  const { data: order, isLoading, error } = useQuery({
    queryKey: ["order-detail", orderId],
    queryFn: async () => {
      return await apiClient.get<OrderDetail>(`/api/v1/orders/${orderId}`);
    },
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 space-y-3">
        <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        <p className="text-xs text-muted-foreground font-medium">Loading order confirmation...</p>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 space-y-4 text-center">
        <div className="w-14 h-14 rounded-full bg-destructive/10 text-destructive flex items-center justify-center">
          <Receipt className="w-7 h-7" />
        </div>
        <h3 className="font-bold text-lg text-foreground">Order Not Found</h3>
        <p className="text-xs text-muted-foreground max-w-sm">
          Could not locate order details. Please verify your account or check your recent orders list.
        </p>
        <Link href="/shop">
          <Button size="sm" className="text-xs">
            Return to Store
          </Button>
        </Link>
      </div>
    );
  }

  // Group items by Aisle
  const itemsByAisle: Record<number, OrderItem[]> = {};
  for (const item of order.items) {
    const aisleNum = item.aisle || 1;
    if (!itemsByAisle[aisleNum]) itemsByAisle[aisleNum] = [];
    itemsByAisle[aisleNum].push(item);
  }

  const aislesSorted = Object.keys(itemsByAisle)
    .map(Number)
    .sort((a, b) => a - b);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="border-b border-border/80 bg-background/80 backdrop-blur-md">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link href="/shop" className="flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground">
            <ArrowLeft className="w-4 h-4" /> Continue Shopping
          </Link>
          <div className="flex items-center gap-2">
            <ShoppingBag className="w-4 h-4 text-primary" />
            <span className="font-extrabold text-sm tracking-tight">OmniMission AI</span>
          </div>
          <span className="text-xs font-mono text-muted-foreground">#{order.order_number}</span>
        </div>
      </header>

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Celebration Banner */}
        <Card className="p-6 bg-gradient-to-r from-emerald-500/10 via-primary/10 to-amber-500/10 border-emerald-500/30 shadow-md space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500 text-white flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-extrabold text-foreground">Mission Accomplished!</h2>
                <Badge variant="accent" className="text-[10px]">
                  Order Confirmed
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Your items have been allocated from physical inventory and are being pre-packed.
              </p>
            </div>
          </div>

          <div className="pt-3 border-t border-border/40 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <span className="text-muted-foreground block text-[11px]">Order Reference</span>
              <span className="font-mono font-bold text-foreground">#{order.order_number}</span>
            </div>
            <div>
              <span className="text-muted-foreground block text-[11px]">Pickup Slot</span>
              <span className="font-semibold text-foreground">
                {order.pickup_time_slot || "Within 30 mins"}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground block text-[11px]">Payment</span>
              <span className="font-semibold text-emerald-600 dark:text-emerald-400 capitalize">
                {order.payment_method.replace("simulated_", "")} (Paid)
              </span>
            </div>
            <div>
              <span className="text-muted-foreground block text-[11px]">Total Paid</span>
              <span className="font-extrabold text-primary">{formatInr(order.total_amount)}</span>
            </div>
          </div>
        </Card>

        {/* Fulfillment Timeline */}
        <Card className="p-6 bg-card/60 backdrop-blur-md border-border/80 space-y-4">
          <h3 className="font-bold text-sm text-foreground flex items-center gap-2">
            <Clock className="w-4 h-4 text-primary" /> Store Fulfillment Timeline
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 pt-2">
            {[
              { title: "Order Placed", status: "completed", desc: "Inventory locked" },
              { title: "Staff Packing", status: "in_progress", desc: "Aisle route traversal" },
              { title: "Ready for Pickup", status: "pending", desc: "At store counter" },
              { title: "Completed", status: "pending", desc: "Handed to customer" },
            ].map((step, idx) => (
              <div key={step.title} className="flex flex-col space-y-1">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      step.status === "completed"
                        ? "bg-emerald-500 text-white"
                        : step.status === "in_progress"
                        ? "bg-primary text-white animate-pulse"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {idx + 1}
                  </div>
                  <span className="font-bold text-xs text-foreground">{step.title}</span>
                </div>
                <p className="text-[11px] text-muted-foreground pl-8">{step.desc}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Items Grouped by Physical Aisle */}
        <Card className="p-6 bg-card/60 backdrop-blur-md border-border/80 space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-border/60">
            <div>
              <h3 className="font-bold text-base text-foreground flex items-center gap-2">
                <Package className="w-4 h-4 text-primary" /> In-Store Item Navigation Map
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Organized by physical aisle sequence for express store walkthrough.
              </p>
            </div>
            <Badge variant="secondary" className="text-xs">
              {order.items.length} items
            </Badge>
          </div>

          <div className="space-y-4">
            {aislesSorted.map((aisleNum) => {
              const aisleItems = itemsByAisle[aisleNum];
              return (
                <div key={aisleNum} className="space-y-2">
                  <div className="flex items-center gap-2 bg-muted/40 px-3 py-1.5 rounded-xl border border-border/40">
                    <MapPin className="w-3.5 h-3.5 text-primary" />
                    <span className="font-bold text-xs text-foreground">Aisle {aisleNum}</span>
                    <span className="text-[11px] text-muted-foreground ml-auto font-mono">
                      {aisleItems.length} {aisleItems.length === 1 ? "item" : "items"}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pl-2">
                    {aisleItems.map((item) => (
                      <div
                        key={item.id}
                        className="p-3 rounded-xl border border-border/60 bg-card hover:border-border transition-colors flex items-center justify-between gap-3 text-xs"
                      >
                        <div className="min-w-0 flex-1">
                          <h5 className="font-semibold text-foreground truncate">
                            {item.product_name}
                          </h5>
                          <span className="text-[11px] text-muted-foreground font-mono">
                            Bay {item.bay} · Shelf {item.shelf} · Qty {item.qty}
                          </span>
                        </div>
                        <span className="font-bold text-foreground shrink-0">
                          {formatInr(item.subtotal)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-center gap-3 pt-2">
          <Link href="/shop">
            <Button className="gap-2 text-xs rounded-xl shadow-md" size="sm">
              <ShoppingBag className="w-3.5 h-3.5" /> Start New Mission
            </Button>
          </Link>
        </div>
      </main>
    </div>
  );
}

"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import {
  ShoppingBag,
  X,
  Plus,
  Minus,
  Trash2,
  MapPin,
  Store as StoreIcon,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { useCartStore } from "@/stores/cart-store";
import { formatInr } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CartItem } from "@/types/commerce";

export function CartDrawer(): React.JSX.Element | null {
  const { cart, isOpen, closeCart, fetchCart, updateItemQty, removeItem, clearCart, isLoading } =
    useCartStore();

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  if (!isOpen) return null;

  // Group items by store name
  const itemsByStore: Record<string, CartItem[]> = {};
  if (cart?.items) {
    for (const item of cart.items) {
      const storeLabel = item.store_name || "Physical Retail Store";
      if (!itemsByStore[storeLabel]) {
        itemsByStore[storeLabel] = [];
      }
      itemsByStore[storeLabel].push(item);
    }
  }

  const hasItems = cart && cart.items && cart.items.length > 0;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-background/80 backdrop-blur-sm animate-in fade-in-0 duration-200">
      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-card border-l border-border shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
          {/* Header */}
          <div className="p-4 border-b border-border/80 flex items-center justify-between bg-muted/30">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                <ShoppingBag className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-base text-foreground flex items-center gap-2">
                  Shopping Cart
                  {hasItems && (
                    <Badge variant="accent" className="text-xs">
                      {cart.total_items} items
                    </Badge>
                  )}
                </h3>
                <p className="text-xs text-muted-foreground">Real-time physical store inventory</p>
              </div>
            </div>
            <button
              onClick={closeCart}
              className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Close cart drawer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {!hasItems ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center text-muted-foreground">
                  <ShoppingBag className="w-8 h-8 stroke-1" />
                </div>
                <div className="space-y-1">
                  <h4 className="font-bold text-base text-foreground">Your basket is empty</h4>
                  <p className="text-xs text-muted-foreground max-w-xs">
                    Ask OmniMission AI to assemble ingredients or explore nearby physical store items.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={closeCart}
                  className="gap-2 text-xs"
                >
                  <Sparkles className="w-3.5 h-3.5 text-primary" /> Start shopping
                </Button>
              </div>
            ) : (
              Object.entries(itemsByStore).map(([storeName, items]) => (
                <div key={storeName} className="space-y-3">
                  <div className="flex items-center gap-2 bg-muted/40 px-3 py-2 rounded-xl border border-border/40">
                    <StoreIcon className="w-3.5 h-3.5 text-primary" />
                    <span className="text-xs font-bold text-foreground truncate">{storeName}</span>
                    <Badge variant="secondary" className="ml-auto text-[10px]">
                      {items.length} items
                    </Badge>
                  </div>

                  <div className="space-y-2">
                    {items.map((item) => (
                      <div
                        key={item.id}
                        className="p-3 rounded-xl border border-border/60 bg-card hover:border-border transition-colors space-y-2"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0 flex-1">
                            <h5 className="font-semibold text-xs text-foreground truncate">
                              {item.product_name}
                            </h5>
                            {item.product_brand && (
                              <p className="text-[11px] text-muted-foreground">{item.product_brand}</p>
                            )}
                            <div className="flex items-center gap-1.5 mt-1 text-[11px] text-muted-foreground">
                              <span className="inline-flex items-center gap-0.5 bg-muted px-1.5 py-0.5 rounded font-mono text-[10px]">
                                <MapPin className="w-2.5 h-2.5 text-primary" />
                                Aisle {item.aisle ?? 1}
                                {item.bay && ` · Bay ${item.bay}`}
                                {item.shelf && ` · Shelf ${item.shelf}`}
                              </span>
                              <span>•</span>
                              <span>{formatInr(item.unit_price)} each</span>
                            </div>
                          </div>

                          <span className="text-xs font-bold text-foreground shrink-0">
                            {formatInr(item.subtotal)}
                          </span>
                        </div>

                        {/* Controls */}
                        <div className="flex items-center justify-between pt-1 border-t border-border/40">
                          <button
                            type="button"
                            onClick={() => removeItem(item.id)}
                            className="text-[11px] text-destructive hover:underline flex items-center gap-1"
                          >
                            <Trash2 className="w-3 h-3" /> Remove
                          </button>

                          <div className="flex items-center gap-1 bg-muted/80 rounded-lg p-0.5 border border-border/40">
                            <button
                              type="button"
                              onClick={() => updateItemQty(item.id, item.qty - 1)}
                              className="w-5 h-5 flex items-center justify-center text-muted-foreground hover:text-foreground rounded hover:bg-background"
                              aria-label="Decrease quantity"
                            >
                              <Minus className="w-3 h-3" />
                            </button>
                            <span className="w-5 text-center text-xs font-mono font-bold">
                              {item.qty}
                            </span>
                            <button
                              type="button"
                              onClick={() => updateItemQty(item.id, item.qty + 1)}
                              className="w-5 h-5 flex items-center justify-center text-muted-foreground hover:text-foreground rounded hover:bg-background"
                              aria-label="Increase quantity"
                            >
                              <Plus className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {hasItems && (
            <div className="p-4 border-t border-border/80 bg-muted/20 space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground font-medium">Subtotal</span>
                <span className="font-extrabold text-base text-foreground">
                  {formatInr(cart.total_amount)}
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Taxes and fulfillment options calculated at simulated checkout.
              </p>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearCart}
                  disabled={isLoading}
                  className="text-xs"
                >
                  Clear
                </Button>
                <Link href="/checkout" onClick={closeCart} className="flex-1">
                  <Button className="w-full gap-2 text-xs" size="sm">
                    Checkout <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

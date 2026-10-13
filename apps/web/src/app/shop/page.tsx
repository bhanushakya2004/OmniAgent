"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  ShoppingBag,
  Sparkles,
  Search,
  Store,
  MapPin,
  Bot,
  User,
  SlidersHorizontal,
  ChevronDown,
  Compass,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import { useCartStore } from "@/stores/cart-store";
import { useStoreSelectionStore } from "@/stores/store-selection-store";
import { useMissionStream } from "@/hooks/use-mission-stream";
import { StorePicker } from "@/components/shopper/store-picker";
import { CatalogSearchView } from "@/components/shopper/catalog-search-view";
import { MissionComposer } from "@/components/shopper/mission-composer";
import { ReasoningTimeline } from "@/components/shopper/reasoning-timeline";
import { BasketView, MissionDetailData } from "@/components/shopper/basket-view";
import { WayfindingRoute } from "@/components/shopper/wayfinding-route";
import { CartDrawer } from "@/components/shopper/cart-drawer";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function ShopPage(): React.JSX.Element {
  const [activeMode, setActiveMode] = useState<"search" | "ai">("ai");
  const [showStorePicker, setShowStorePicker] = useState(false);
  const [activeMissionId, setActiveMissionId] = useState<string | null>(null);

  const { user, logout } = useAuthStore();
  const { cart, openCart, fetchCart } = useCartStore();
  const selectedStoreIds = useStoreSelectionStore((state) => state.selectedStoreIds);

  const {
    missionId: streamingMissionId,
    events,
    status: streamStatus,
    error: streamError,
    completedData,
    startStream,
    reset: resetStream,
  } = useMissionStream();

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  // Query mission details once streaming completes or active
  const { data: missionDetail, refetch: refetchMissionDetail } = useQuery({
    queryKey: ["mission-detail", activeMissionId],
    queryFn: async () => {
      if (!activeMissionId) return null;
      return await apiClient.get<MissionDetailData>(`/api/v1/missions/${activeMissionId}`);
    },
    enabled: !!activeMissionId,
    refetchInterval: streamStatus === "streaming" ? 3000 : false,
  });

  const handleMissionCreated = (missionId: string) => {
    setActiveMissionId(missionId);
    startStream(missionId);
  };

  const totalCartItems = cart?.total_items ?? 0;

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Top Navigation */}
      <header className="sticky top-0 z-40 border-b border-border/80 bg-background/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-primary to-amber-500 text-white shadow-md shadow-primary/20">
                <ShoppingBag className="h-5 w-5" />
              </span>
              <span className="text-xl font-bold tracking-tight text-foreground">
                OmniMission <span className="text-primary">AI</span>
              </span>
            </Link>

            <Badge variant="outline" className="hidden sm:inline-flex text-[11px] font-medium border-border/70">
              Phygital Retail
            </Badge>
          </div>

          {/* Store Quick Selector Toggle */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowStorePicker((prev) => !prev)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-muted/60 hover:bg-muted border border-border/60 text-xs font-semibold text-foreground transition-colors"
            >
              <Store className="w-3.5 h-3.5 text-primary" />
              <span>
                {selectedStoreIds.length === 0
                  ? "Select Nearby Store"
                  : `${selectedStoreIds.length} Store${selectedStoreIds.length > 1 ? "s" : ""} Active`}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
            </button>

            {/* Cart Button with Count Badge */}
            <button
              onClick={openCart}
              className="relative flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold shadow-md hover:bg-primary/90 transition-all"
              aria-label="Open Cart"
            >
              <ShoppingBag className="w-4 h-4" />
              <span className="hidden sm:inline">Cart</span>
              {totalCartItems > 0 && (
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white text-primary text-[11px] font-extrabold">
                  {totalCartItems}
                </span>
              )}
            </button>

            {/* User Account / Guest Sign In */}
            {user ? (
              <div className="flex items-center gap-2 pl-2">
                <span className="text-xs font-medium text-muted-foreground hidden md:inline">
                  {user.full_name || user.email}
                </span>
                <Button variant="ghost" size="sm" onClick={logout} className="text-xs">
                  Sign Out
                </Button>
              </div>
            ) : (
              <Link href="/login" className="pl-1">
                <Button variant="outline" size="sm" className="text-xs gap-1.5 rounded-xl">
                  <User className="w-3.5 h-3.5" /> Sign In
                </Button>
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Collapsible Store Picker Drawer/Sheet */}
      {showStorePicker && (
        <div className="border-b border-border bg-card/60 backdrop-blur-md p-4 animate-in slide-in-from-top duration-200">
          <div className="max-w-7xl mx-auto space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                Select Physical Stores for Inventory Grounding
              </h4>
              <button
                onClick={() => setShowStorePicker(false)}
                className="text-xs text-primary font-semibold hover:underline"
              >
                Done
              </button>
            </div>
            <StorePicker />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero Segmented Control */}
        <div className="flex flex-col items-center justify-center text-center space-y-4">
          <div className="space-y-1">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
              Physical Retail,{" "}
              <span className="bg-gradient-to-r from-primary to-amber-500 bg-clip-text text-transparent">
                Supercharged by AI
              </span>
            </h1>
            <p className="text-sm text-muted-foreground max-w-xl mx-auto">
              Plan goals in natural language or search live in-store catalog across aisles, bays, and shelves.
            </p>
          </div>

          {/* Segmented Mode Selector */}
          <div className="inline-flex p-1 rounded-2xl bg-muted/80 border border-border/80 shadow-inner">
            <button
              type="button"
              onClick={() => setActiveMode("ai")}
              className={`flex items-center gap-2 px-5 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                activeMode === "ai"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Sparkles className="w-4 h-4 text-primary" />
              Ask AI (Conversational Mission)
            </button>

            <button
              type="button"
              onClick={() => setActiveMode("search")}
              className={`flex items-center gap-2 px-5 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                activeMode === "search"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Search className="w-4 h-4 text-primary" />
              Search Catalog (Physical Inventory)
            </button>
          </div>
        </div>

        {/* Mode Render */}
        {activeMode === "search" ? (
          <div className="animate-in fade-in-50 duration-200">
            <CatalogSearchView />
          </div>
        ) : (
          <div className="space-y-8 animate-in fade-in-50 duration-200">
            {/* Mission Composer */}
            <MissionComposer
              onMissionCreated={handleMissionCreated}
              isStreaming={streamStatus === "streaming"}
            />

            {/* Live Streaming Reasoning Timeline */}
            {(events.length > 0 || streamStatus !== "idle") && (
              <ReasoningTimeline
                events={events}
                status={streamStatus}
                error={streamError}
              />
            )}

            {/* Generated Basket View */}
            {missionDetail && missionDetail.items && missionDetail.items.length > 0 && (
              <div className="space-y-6">
                <BasketView
                  mission={missionDetail}
                  onRefresh={() => refetchMissionDetail()}
                />
                <WayfindingRoute missionId={missionDetail.id} />
              </div>
            )}
          </div>
        )}
      </main>

      {/* Slide-over Cart Drawer */}
      <CartDrawer />
    </div>
  );
}

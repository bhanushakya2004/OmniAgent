"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  ShoppingBag,
  Sparkles,
  Store,
  Compass,
  History,
  LogOut,
  RefreshCw,
  Layers,
  CheckCircle2,
  ChevronRight,
  ArrowRight,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import { useMissionStream } from "@/hooks/use-mission-stream";
import { StorePicker } from "@/components/shopper/store-picker";
import { MissionComposer } from "@/components/shopper/mission-composer";
import { ReasoningTimeline } from "@/components/shopper/reasoning-timeline";
import { BasketView, MissionDetailData } from "@/components/shopper/basket-view";
import { WayfindingRoute } from "@/components/shopper/wayfinding-route";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

interface MissionListItem {
  id: string;
  raw_text: string;
  status: string;
  total_cost?: string | number | null;
  item_count: number;
  created_at: string;
}

export default function ShopperPage(): React.JSX.Element {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [activeMissionId, setActiveMissionId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"current" | "history">("current");

  const {
    missionId: streamingMissionId,
    events,
    status: streamStatus,
    error: streamError,
    completedData,
    startStream,
    reset: resetStream,
  } = useMissionStream();

  // Query mission details once streaming completes or when selecting historical mission
  const {
    data: missionDetail,
    isLoading: isLoadingDetail,
    refetch: refetchMissionDetail,
  } = useQuery({
    queryKey: ["mission-detail", activeMissionId],
    queryFn: async () => {
      if (!activeMissionId) return null;
      return await apiClient.get<MissionDetailData>(`/api/v1/missions/${activeMissionId}`);
    },
    enabled: Boolean(activeMissionId),
  });

  // Query past missions history
  const {
    data: historyData,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ["missions-history"],
    queryFn: async () => {
      return await apiClient.get<{ missions: MissionListItem[]; total: number }>("/api/v1/missions");
    },
  });

  // Handle new mission creation
  const handleMissionCreated = (newMissionId: string) => {
    setActiveMissionId(newMissionId);
    setActiveTab("current");
    startStream(newMissionId);
    refetchHistory();
  };

  // When stream completes, trigger query refresh for completed basket
  useEffect(() => {
    if (streamStatus === "completed" && activeMissionId) {
      refetchMissionDetail();
      refetchHistory();
    }
  }, [streamStatus, activeMissionId, refetchMissionDetail, refetchHistory]);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const handleSelectHistoricalMission = (mId: string) => {
    setActiveMissionId(mId);
    setActiveTab("current");
    resetStream();
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Navigation Header */}
      <header className="sticky top-0 z-40 w-full border-b border-border/80 bg-background/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2.5">
              <span className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary to-amber-500 text-white flex items-center justify-center shadow-sm">
                <ShoppingBag className="w-5 h-5" />
              </span>
              <div>
                <span className="font-extrabold text-base tracking-tight leading-none block">
                  OmniMission <span className="text-primary font-bold">AI</span>
                </span>
                <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block mt-0.5">
                  Phygital Retail Engine
                </span>
              </div>
            </Link>

            <div className="hidden sm:flex items-center gap-1.5 ml-4 pl-4 border-l border-border/80">
              <Badge variant="accent">Shopper Mode</Badge>
              <Link href="/merchant">
                <Button variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-foreground">
                  <Store className="w-3.5 h-3.5 mr-1" />
                  Merchant Portal
                </Button>
              </Link>
            </div>
          </div>

          {/* User profile & actions */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 border border-border/80 rounded-xl p-1 bg-muted/40">
              <button
                type="button"
                onClick={() => setActiveTab("current")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === "current"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Mission Workspace
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("history")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1 ${
                  activeTab === "history"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <History className="w-3 h-3" />
                History ({historyData?.total ?? 0})
              </button>
            </div>

            <div className="hidden md:flex items-center gap-2 pl-2">
              <span className="text-xs font-medium text-muted-foreground">
                {user?.full_name || user?.email || "Shopper"}
              </span>
            </div>

            <Button variant="outline" size="icon" onClick={handleLogout} title="Sign Out">
              <LogOut className="w-4 h-4 text-muted-foreground" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {activeTab === "history" ? (
          /* History View */
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2">
              <div>
                <h2 className="text-2xl font-bold tracking-tight">Your Past Missions</h2>
                <p className="text-sm text-muted-foreground">
                  View and replay previously planned shopping goals.
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={() => refetchHistory()}>
                <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Refresh
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {historyData?.missions?.map((m) => (
                <Card
                  key={m.id}
                  onClick={() => handleSelectHistoricalMission(m.id)}
                  className="p-5 cursor-pointer hover:border-primary/50 transition-all hover:shadow-md space-y-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <Badge variant={m.status === "completed" ? "accent" : "secondary"}>
                      {m.status.toUpperCase()}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(m.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <p className="font-semibold text-sm line-clamp-2 text-foreground">
                    "{m.raw_text}"
                  </p>

                  <div className="pt-2 border-t border-border/40 flex items-center justify-between text-xs font-medium">
                    <span className="text-muted-foreground">{m.item_count} grounded items</span>
                    <span className="font-bold text-primary">₹{m.total_cost || "0.00"}</span>
                  </div>
                </Card>
              ))}

              {(!historyData?.missions || historyData.missions.length === 0) && (
                <div className="col-span-full py-12 text-center text-muted-foreground">
                  <p>No historical missions yet. Create your first goal in the workspace!</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Current Mission Workspace */
          <div className="space-y-8">
            {/* 1. Store Selection & Geolocation */}
            <StorePicker />

            {/* 2. Mission Composer */}
            <MissionComposer
              onMissionCreated={handleMissionCreated}
              isStreaming={streamStatus === "streaming" || streamStatus === "connecting"}
            />

            {/* 3. Live Multi-Agent Reasoning Timeline */}
            <ReasoningTimeline
              events={events}
              status={streamStatus}
              error={streamError}
            />

            {/* 4. Grounded Basket Display (when mission detail loaded) */}
            {missionDetail && missionDetail.items.length > 0 && (
              <BasketView
                mission={missionDetail}
                onRefresh={refetchMissionDetail}
              />
            )}

            {/* 5. In-Store Wayfinding Route */}
            {missionDetail && missionDetail.items.length > 0 && (
              <WayfindingRoute missionId={missionDetail.id} />
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border/60 py-6 mt-auto bg-card/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted-foreground">
          <p>© 2026 OmniMission AI • Phygital Retail Intelligence on Google Gemini</p>
          <div className="flex items-center gap-4">
            <span>FastAPI Async Engine</span>
            <span>•</span>
            <span>PostgreSQL pgvector</span>
            <span>•</span>
            <span>Next.js 15 App Router</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

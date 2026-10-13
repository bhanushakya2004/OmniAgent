"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Navigation,
  CheckCircle2,
  Circle,
  Copy,
  Printer,
  MapPin,
  Check,
  Sparkles,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface Waypoint {
  step_number: number;
  store_id: string;
  store_name: string;
  aisle: number;
  bay: number;
  shelf: number;
  product_name: string;
  quantity: number;
  action: string;
}

interface RouteResponse {
  mission_id: string;
  total_stops: number;
  waypoints: Waypoint[];
}

interface WayfindingRouteProps {
  missionId: string;
}

export function WayfindingRoute({ missionId }: WayfindingRouteProps): React.JSX.Element {
  const [completedStops, setCompletedStops] = useState<number[]>([]);
  const [isCopied, setIsCopied] = useState(false);

  const { data: routeData, isLoading } = useQuery({
    queryKey: ["mission-route", missionId],
    queryFn: async () => {
      return await apiClient.get<RouteResponse>(`/api/v1/missions/${missionId}/route`);
    },
    enabled: Boolean(missionId),
  });

  const toggleStop = (stepNum: number) => {
    setCompletedStops((prev) =>
      prev.includes(stepNum) ? prev.filter((n) => n !== stepNum) : [...prev, stepNum]
    );
  };

  const copyRouteToClipboard = () => {
    if (!routeData) return;
    const text = routeData.waypoints
      .map(
        (w) =>
          `Step ${w.step_number}: ${w.store_name} | Aisle ${w.aisle}, Bay ${w.bay}, Shelf ${w.shelf} -> ${w.product_name}`
      )
      .join("\n");

    navigator.clipboard.writeText(text);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  if (isLoading) {
    return (
      <Card className="p-6 text-center text-sm text-muted-foreground">
        <div className="inline-block w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mb-2" />
        <p>Calculating optimal monotonic walking path...</p>
      </Card>
    );
  }

  const waypoints = routeData?.waypoints ?? [];
  const totalStops = waypoints.length;
  const progressPercent = totalStops > 0 ? Math.round((completedStops.length / totalStops) * 100) : 0;

  return (
    <Card className="p-6 bg-card/60 backdrop-blur-md border-border/80 shadow-md">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border/60">
        <div>
          <div className="flex items-center gap-2">
            <Navigation className="w-5 h-5 text-primary" />
            <h3 className="font-bold text-lg">In-Store Walking Route</h3>
            <Badge variant="accent">{totalStops} Stops</Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Monotonically ordered path through physical aisles (Aisle ASC, Bay ASC, Shelf ASC) to minimize walking time.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={copyRouteToClipboard}>
            {isCopied ? <Check className="w-3.5 h-3.5 mr-1 text-emerald-500" /> : <Copy className="w-3.5 h-3.5 mr-1" />}
            {isCopied ? "Copied" : "Copy Path"}
          </Button>
          <Button variant="ghost" size="sm" onClick={handlePrint}>
            <Printer className="w-3.5 h-3.5 mr-1" />
            Print
          </Button>
        </div>
      </div>

      {/* Progress Bar */}
      {totalStops > 0 && (
        <div className="mt-4 p-3 rounded-xl bg-muted/30 border border-border/40 space-y-1.5">
          <div className="flex justify-between text-xs font-semibold">
            <span>Store Navigation Progress</span>
            <span className="text-primary font-mono">{progressPercent}% Picked</span>
          </div>
          <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Waypoints List */}
      <div className="mt-5 space-y-3">
        {waypoints.map((wp) => {
          const isDone = completedStops.includes(wp.step_number);
          return (
            <div
              key={wp.step_number}
              onClick={() => toggleStop(wp.step_number)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                isDone
                  ? "bg-muted/40 border-border/40 opacity-60"
                  : "bg-card border-border/70 hover:border-primary/50 shadow-sm"
              }`}
            >
              <div className="flex items-start gap-3.5">
                <button
                  type="button"
                  className="mt-0.5 shrink-0 text-muted-foreground hover:text-foreground"
                >
                  {isDone ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  ) : (
                    <Circle className="w-5 h-5 text-muted-foreground/40" />
                  )}
                </button>

                <div className="space-y-1 w-full">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-primary/10 text-primary">
                        Stop #{wp.step_number}
                      </span>
                      <span className="text-xs font-semibold text-muted-foreground">
                        {wp.store_name}
                      </span>
                    </div>

                    <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-muted text-foreground/80">
                      Aisle {wp.aisle} • Bay {wp.bay} • Shelf {wp.shelf}
                    </span>
                  </div>

                  <p
                    className={`text-sm font-medium pt-0.5 ${
                      isDone ? "line-through text-muted-foreground" : "text-foreground"
                    }`}
                  >
                    {wp.action}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

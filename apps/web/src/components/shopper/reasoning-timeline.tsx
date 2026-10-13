"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  Clock,
  Bot,
  Wrench,
  ShieldCheck,
  ShoppingBag,
  Navigation,
  Sparkles,
  AlertCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { StreamEvent, StreamStatus } from "@/hooks/use-mission-stream";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ReasoningTimelineProps {
  events: StreamEvent[];
  status: StreamStatus;
  error: string | null;
}

export function ReasoningTimeline({
  events,
  status,
  error,
}: ReasoningTimelineProps): React.JSX.Element | null {
  const [expandedThoughts, setExpandedThoughts] = useState<Record<number, boolean>>({});

  if (status === "idle" && events.length === 0) return null;

  const toggleThought = (idx: number) => {
    setExpandedThoughts((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const getEventBadge = (type: string) => {
    switch (type) {
      case "agent_thought":
        return (
          <Badge variant="secondary" className="gap-1 text-[10px] bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20">
            <Bot className="w-3 h-3" /> Thought
          </Badge>
        );
      case "tool_call":
        return (
          <Badge variant="secondary" className="gap-1 text-[10px] bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20">
            <Wrench className="w-3 h-3" /> Tool Call
          </Badge>
        );
      case "tool_result":
        return (
          <Badge variant="secondary" className="gap-1 text-[10px] bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/20">
            <Sparkles className="w-3 h-3" /> Tool Result
          </Badge>
        );
      case "grounding_check":
        return (
          <Badge variant="secondary" className="gap-1 text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20">
            <ShieldCheck className="w-3 h-3" /> Grounding Check
          </Badge>
        );
      case "basket_update":
        return (
          <Badge variant="secondary" className="gap-1 text-[10px] bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20">
            <ShoppingBag className="w-3 h-3" /> Cart Action
          </Badge>
        );
      case "wayfinding_route":
        return (
          <Badge variant="secondary" className="gap-1 text-[10px] bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20">
            <Navigation className="w-3 h-3" /> Wayfinding
          </Badge>
        );
      case "mission_complete":
        return (
          <Badge variant="accent" className="gap-1 text-[10px]">
            <CheckCircle2 className="w-3 h-3" /> Completed
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary" className="text-[10px]">
            {type}
          </Badge>
        );
    }
  };

  return (
    <Card className="p-6 bg-card/60 backdrop-blur-md border-border/80 shadow-md">
      <div className="flex items-center justify-between pb-4 border-b border-border/60">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-primary" />
          <h3 className="font-bold text-lg">Multi-Agent Reasoning Stream</h3>
        </div>
        <div className="flex items-center gap-2">
          {status === "streaming" || status === "connecting" ? (
            <Badge variant="accent" className="animate-pulse">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping mr-1" />
              Agent Graph Active
            </Badge>
          ) : status === "completed" ? (
            <Badge variant="default">All Steps Completed</Badge>
          ) : null}
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Steps List */}
      <div className="mt-5 space-y-3">
        {events.map((evt, idx) => {
          const isThought = evt.event_type === "agent_thought";
          const thoughtText =
            typeof evt.payload.thought === "string"
              ? evt.payload.thought
              : typeof evt.payload.message === "string"
              ? evt.payload.message
              : "";
          const isExpanded = !!expandedThoughts[idx];

          return (
            <div
              key={`${evt.sequence_id}-${evt.event_type}-${idx}`}
              className="p-4 rounded-xl border border-border/70 bg-card shadow-sm transition-all space-y-2"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-[11px] text-muted-foreground">
                    #{evt.sequence_id}
                  </span>
                  {getEventBadge(evt.event_type)}
                </div>

                {isThought && thoughtText.length > 120 && (
                  <button
                    onClick={() => toggleThought(idx)}
                    className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
                  >
                    {isExpanded ? (
                      <>
                        Less <ChevronUp className="w-3.5 h-3.5" />
                      </>
                    ) : (
                      <>
                        More <ChevronDown className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                )}
              </div>

              {/* Event Content */}
              {isThought && (
                <p className={`text-xs text-foreground/90 leading-relaxed font-sans ${
                  !isExpanded && thoughtText.length > 120 ? "line-clamp-2" : ""
                }`}>
                  {thoughtText || "Deliberating next step..."}
                </p>
              )}

              {evt.event_type === "tool_call" && (
                <div className="text-xs font-mono bg-muted/60 p-2.5 rounded-lg border border-border/40 text-muted-foreground">
                  <span className="text-primary font-bold">
                    {String(evt.payload.tool || "tool")}
                  </span>
                  (
                  {evt.payload.inputs ? JSON.stringify(evt.payload.inputs) : ""}
                  )
                </div>
              )}

              {evt.event_type === "tool_result" && (
                <div className="text-xs font-mono bg-muted/40 p-2 rounded-lg text-muted-foreground">
                  Returned {String(evt.payload.hits ?? "result")}:{" "}
                  {JSON.stringify(evt.payload.result || evt.payload).slice(0, 160)}
                </div>
              )}

              {evt.event_type === "grounding_check" && (
                <div className="text-xs text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 shrink-0" />
                  Grounded: SKU {String(evt.payload.sku || "")} verified in store inventory
                  {evt.payload.aisle ? ` (Aisle ${evt.payload.aisle})` : ""}
                </div>
              )}

              {evt.event_type === "basket_update" && (
                <div className="text-xs text-amber-600 dark:text-amber-400 font-medium flex items-center gap-1.5">
                  <ShoppingBag className="w-4 h-4 shrink-0" />
                  Cart updated: {String(evt.payload.product_name || evt.payload.sku || "Item added")}
                </div>
              )}

              {evt.event_type === "wayfinding_route" && (
                <div className="text-xs text-indigo-600 dark:text-indigo-400 font-medium flex items-center gap-1.5">
                  <Navigation className="w-4 h-4 shrink-0" />
                  Optimal store walking path calculated ({String(evt.payload.distance_m || 45)}m walk)
                </div>
              )}

              {evt.event_type === "mission_complete" && (
                <div className="text-xs text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  Mission complete! {typeof evt.payload.summary === "string" ? evt.payload.summary : ""}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}

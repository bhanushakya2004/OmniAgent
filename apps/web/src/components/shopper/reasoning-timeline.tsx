"use client";

import React from "react";
import { CheckCircle2, Clock, Bot, Cpu, Sparkles, AlertCircle } from "lucide-react";
import { TimelineStepEvent, StreamStatus } from "@/hooks/use-mission-stream";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ReasoningTimelineProps {
  events: TimelineStepEvent[];
  status: StreamStatus;
  error: string | null;
}

export function ReasoningTimeline({
  events,
  status,
  error,
}: ReasoningTimelineProps): React.JSX.Element | null {
  if (status === "idle" && events.length === 0) return null;

  return (
    <Card className="p-6 bg-card/60 backdrop-blur-md border-border/80 shadow-md">
      <div className="flex items-center justify-between pb-4 border-b border-border/60">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-primary" />
          <h3 className="font-bold text-lg">Multi-Agent Reasoning Timeline</h3>
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
          const isDone = evt.status === "completed";
          return (
            <div
              key={`${evt.step}-${idx}`}
              className={`p-4 rounded-xl border transition-all ${
                isDone
                  ? "bg-card border-border/70 shadow-sm"
                  : "bg-primary/5 border-primary/30 ring-1 ring-primary/20"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">
                    {isDone ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                    ) : (
                      <div className="w-5 h-5 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="font-semibold text-sm text-foreground">{evt.title}</h4>
                      <Badge variant="secondary" className="text-[10px] py-0 px-2">
                        {evt.agent}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                      {evt.description}
                    </p>
                  </div>
                </div>

                {evt.latency_ms !== undefined && (
                  <span className="text-[11px] font-mono text-muted-foreground flex items-center gap-1 shrink-0">
                    <Clock className="w-3 h-3" />
                    {evt.latency_ms}ms
                  </span>
                )}
              </div>

              {/* Data tags if present */}
              {evt.data && Object.keys(evt.data).length > 0 && (
                <div className="mt-3 pt-2.5 border-t border-border/40 flex items-center gap-1.5 flex-wrap">
                  {Object.entries(evt.data).map(([k, v]) => {
                    if (v === null || v === undefined || typeof v === "object") return null;
                    return (
                      <span
                        key={k}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-muted text-muted-foreground border border-border/50"
                      >
                        {k}: <strong className="text-foreground">{String(v)}</strong>
                      </span>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}

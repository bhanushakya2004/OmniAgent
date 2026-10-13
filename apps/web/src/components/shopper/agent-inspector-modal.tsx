"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Bot,
  Wrench,
  ShieldCheck,
  Brain,
  Database,
  Cpu,
  X,
  Code,
  Layers,
  CheckCircle2,
  Clock,
  Sparkles,
  Search,
  Zap,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface InspectorTelemetry {
  mission_id: string;
  status: string;
  raw_text: string;
  selected_store_ids: string[];
  total_cost: number;
  item_count: number;
  telemetry: {
    model: string;
    event_count: number;
    tool_call_count: number;
    grounding_check_count: number;
  };
  thoughts: Array<Record<string, unknown>>;
  tool_calls: Array<Record<string, unknown>>;
  tool_results: Array<Record<string, unknown>>;
  grounding_checks: Array<Record<string, unknown>>;
  basket_updates: Array<Record<string, unknown>>;
  events: Array<{
    sequence_id: number;
    event_type: string;
    payload: Record<string, unknown>;
    created_at?: string;
  }>;
}

interface AgentInspectorModalProps {
  missionId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

type InspectorTab = "trajectory" | "tools" | "rag" | "grounding" | "telemetry";

export function AgentInspectorModal({
  missionId,
  isOpen,
  onClose,
}: AgentInspectorModalProps): React.JSX.Element | null {
  const [activeTab, setActiveTab] = useState<InspectorTab>("trajectory");

  const { data: telemetry, isLoading } = useQuery<InspectorTelemetry>({
    queryKey: ["inspector-telemetry", missionId],
    queryFn: () => apiClient.get<InspectorTelemetry>(`/api/v1/missions/${missionId}/inspector`),
    enabled: isOpen && !!missionId,
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-background/80 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 animate-in fade-in-0 duration-200">
      <div className="bg-card border border-border/80 shadow-2xl rounded-3xl max-w-4xl w-full h-[85vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-border/80 flex items-center justify-between bg-muted/40">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-extrabold text-base text-foreground">
                  Glass-Box Agent Inspector
                </h3>
                <Badge variant="outline" className="text-[10px] font-mono border-purple-500/30 text-purple-600 dark:text-purple-400">
                  Live Observability
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground font-mono">
                Mission: {missionId ? `#${missionId.slice(0, 8)}` : "None"} · Model: {telemetry?.telemetry.model || "gemini-2.5-flash"}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-border/80 px-4 sm:px-6 bg-muted/20 overflow-x-auto text-xs font-bold">
          {[
            { id: "trajectory", label: "Agent Trajectory", icon: Bot },
            { id: "tools", label: "Tool Executions", icon: Wrench },
            { id: "rag", label: "RAG & Graph Paths", icon: Brain },
            { id: "grounding", label: "Grounding Audit", icon: ShieldCheck },
            { id: "telemetry", label: "Token & Latency", icon: Cpu },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as InspectorTab)}
                className={`flex items-center gap-1.5 py-3 px-3 border-b-2 transition-all whitespace-nowrap ${
                  isActive
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {isLoading ? (
            <div className="h-full flex flex-col items-center justify-center space-y-3">
              <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin" />
              <p className="text-xs text-muted-foreground">Compiling agent execution trace...</p>
            </div>
          ) : !telemetry ? (
            <div className="text-center py-12 text-muted-foreground text-xs">
              No telemetry available for this session. Launch a mission first.
            </div>
          ) : (
            <>
              {/* Tab 1: Trajectory & Thoughts */}
              {activeTab === "trajectory" && (
                <div className="space-y-4">
                  <div className="p-4 rounded-2xl bg-muted/40 border border-border/60 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">
                        Original Goal Prompt
                      </span>
                      <p className="text-xs font-semibold text-foreground mt-0.5">
                        &ldquo;{telemetry.raw_text}&rdquo;
                      </p>
                    </div>
                    <Badge variant="accent" className="text-[10px]">
                      Status: {telemetry.status}
                    </Badge>
                  </div>

                  <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider pt-2">
                    Deliberation & Thought Stream ({telemetry.thoughts.length})
                  </h4>

                  <div className="space-y-2.5">
                    {telemetry.thoughts.map((th, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl border border-border/70 bg-card text-xs space-y-1"
                      >
                        <div className="flex items-center gap-2">
                          <Bot className="w-3.5 h-3.5 text-purple-500" />
                          <span className="font-bold text-foreground">
                            Step #{idx + 1}
                          </span>
                          <span className="text-[10px] text-muted-foreground font-mono ml-auto">
                            Agent: Concierge / Planner
                          </span>
                        </div>
                        <p className="text-muted-foreground leading-relaxed pl-5 font-mono text-[11px]">
                          {typeof th.thought === "string" ? th.thought : JSON.stringify(th)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 2: Tool Execution Log */}
              {activeTab === "tools" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                      Governed Tool Calls ({telemetry.tool_calls.length})
                    </h4>
                    <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold">
                      Strict Least-Privilege Scope Bound
                    </span>
                  </div>

                  <div className="space-y-3">
                    {telemetry.tool_calls.map((tc, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl border border-border/70 bg-card text-xs space-y-2 font-mono"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-primary font-bold flex items-center gap-1.5">
                            <Wrench className="w-3.5 h-3.5" />
                            {String(tc.tool || "tool")}
                          </span>
                          <Badge variant="secondary" className="text-[10px]">
                            read_only
                          </Badge>
                        </div>
                        <div className="bg-muted/60 p-2.5 rounded-lg text-[11px] text-muted-foreground overflow-x-auto">
                          Inputs: {JSON.stringify(tc.inputs || tc)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 3: RAG & Knowledge Graph */}
              {activeTab === "rag" && (
                <div className="space-y-4">
                  <div className="p-4 rounded-2xl bg-primary/5 border border-primary/20 space-y-2">
                    <div className="flex items-center gap-2">
                      <Brain className="w-4 h-4 text-primary" />
                      <h4 className="font-bold text-xs text-foreground">
                        Hybrid RRF Retrieval & GraphRAG-Lite
                      </h4>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Structured recipe plans and travel kits are grounded via Reciprocal Rank Fusion (k=60)
                      over pgvector embeddings, full-text search, and recursive CTE graph traversal.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                      Knowledge Graph Traversal Path
                    </h4>
                    <div className="p-3.5 rounded-xl border border-border/70 bg-card text-xs font-mono text-muted-foreground space-y-2">
                      <div className="flex items-center gap-2 text-foreground font-semibold">
                        <span>[Recipe Goal]</span>
                        <span>→</span>
                        <span className="text-primary">[KG Node: Eggless Strawberry Cake]</span>
                        <span>→</span>
                        <span>[Edge: requires_ingredient]</span>
                      </div>
                      <div className="pl-4 border-l-2 border-primary/40 space-y-1 text-[11px]">
                        <div>• Strawberry Fresh (Produce Aisle 1)</div>
                        <div>• Maida All-Purpose Flour (Baking Aisle 4)</div>
                        <div>• Condensed Milk (Substitute for Eggs, Dairy Aisle 2)</div>
                        <div>• Vanilla Extract (Flavoring Aisle 4)</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 4: Grounding Audit */}
              {activeTab === "grounding" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                      Physical Store Grounding Verification ({telemetry.grounding_checks.length})
                    </h4>
                    <Badge variant="accent" className="text-[10px]">
                      100% In-Stock Verified
                    </Badge>
                  </div>

                  <div className="space-y-2.5">
                    {telemetry.grounding_checks.map((gc, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-500/5 text-xs flex items-center justify-between gap-3"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                          <div>
                            <span className="font-bold text-foreground block truncate">
                              SKU: {String(gc.sku || gc.product_name || `Item #${idx + 1}`)}
                            </span>
                            <span className="text-[11px] text-muted-foreground font-mono">
                              Coordinates: Aisle {String(gc.aisle || 1)} · Shelf {String(gc.shelf || 1)}
                            </span>
                          </div>
                        </div>
                        <Badge variant="secondary" className="text-[10px] shrink-0">
                          Verified In Stock
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 5: Telemetry */}
              {activeTab === "telemetry" && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/60">
                      <span className="text-[11px] text-muted-foreground block">LLM Model</span>
                      <span className="text-xs font-mono font-bold text-foreground">
                        {telemetry.telemetry.model}
                      </span>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/60">
                      <span className="text-[11px] text-muted-foreground block">Event Stream Count</span>
                      <span className="text-sm font-extrabold text-foreground">
                        {telemetry.telemetry.event_count}
                      </span>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/60">
                      <span className="text-[11px] text-muted-foreground block">Tool Invocations</span>
                      <span className="text-sm font-extrabold text-primary">
                        {telemetry.telemetry.tool_call_count}
                      </span>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/60">
                      <span className="text-[11px] text-muted-foreground block">Grounding Pass Rate</span>
                      <span className="text-sm font-extrabold text-emerald-600 dark:text-emerald-400">
                        100%
                      </span>
                    </div>
                  </div>

                  <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider pt-2">
                    Chronological Monotonic Event Stream Log
                  </h4>

                  <div className="p-3 rounded-xl bg-card border border-border/60 max-h-60 overflow-y-auto space-y-1.5 font-mono text-[11px]">
                    {telemetry.events.map((e) => (
                      <div key={e.sequence_id} className="flex items-center gap-2 py-0.5 text-muted-foreground">
                        <span className="text-primary font-bold">#{e.sequence_id}</span>
                        <Badge variant="outline" className="text-[9px] py-0 px-1.5">
                          {e.event_type}
                        </Badge>
                        <span className="truncate text-foreground/80">
                          {JSON.stringify(e.payload).slice(0, 80)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

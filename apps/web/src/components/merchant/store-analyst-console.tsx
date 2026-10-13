"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import {
  Bot,
  Sparkles,
  Send,
  Loader2,
  Code,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  TrendingUp,
  ShieldCheck,
  RefreshCw,
  Clock,
  ChevronDown,
  ChevronUp,
  ShoppingBag,
} from "lucide-react";
import {
  queryStoreAnalyst,
  getDailyBriefing,
  getActionProposals,
  approveActionProposal,
  rejectActionProposal,
  AnalystResponse,
  DailyBriefing,
  ActionProposal,
} from "@/lib/merchant-api";
import { formatInr } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const CHART_COLORS = [
  "#f97316", // Orange / Primary
  "#3b82f6", // Blue
  "#10b981", // Emerald
  "#8b5cf6", // Purple
  "#ec4899", // Pink
  "#f59e0b", // Amber
];

const SUGGESTED_QUERIES = [
  "Which items have low stock or high stockout risk?",
  "Top selling products by revenue this week",
  "Aisle pick velocity and customer footfall",
  "Daily store revenue trends",
  "Active replenishment tasks across bays",
];

interface StoreAnalystConsoleProps {
  storeId: string;
}

export function StoreAnalystConsole({ storeId }: StoreAnalystConsoleProps): React.JSX.Element {
  const queryClient = useQueryClient();
  const [inputQuery, setInputQuery] = useState("");
  const [showSql, setShowSql] = useState(false);

  // 1. Fetch Proactive Daily Briefing
  const { data: briefing, isLoading: isLoadingBriefing } = useQuery<DailyBriefing>({
    queryKey: ["merchant", "briefing", storeId],
    queryFn: () => getDailyBriefing(storeId),
    enabled: !!storeId,
  });

  // 2. Fetch HITL Action Proposals
  const { data: proposals = [], refetch: refetchProposals } = useQuery<ActionProposal[]>({
    queryKey: ["merchant", "proposals", storeId],
    queryFn: () => getActionProposals(storeId),
    enabled: !!storeId,
  });

  // 3. Analyst Query Mutation
  const queryMutation = useMutation({
    mutationFn: (q: string) => queryStoreAnalyst(storeId, q),
    onSuccess: () => {
      refetchProposals();
    },
  });

  // 4. Approve Proposal Mutation
  const approveMutation = useMutation({
    mutationFn: (proposalId: string) => approveActionProposal(proposalId, "Approved via Console"),
    onSuccess: () => {
      refetchProposals();
      queryClient.invalidateQueries({ queryKey: ["merchant", "restock-tasks", storeId] });
      queryClient.invalidateQueries({ queryKey: ["merchant", "inventory", storeId] });
    },
  });

  // 5. Reject Proposal Mutation
  const rejectMutation = useMutation({
    mutationFn: (proposalId: string) => rejectActionProposal(proposalId, "Rejected via Console"),
    onSuccess: () => {
      refetchProposals();
    },
  });

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || queryMutation.isPending) return;
    queryMutation.mutate(inputQuery.trim());
  };

  const handleChipClick = (q: string) => {
    setInputQuery(q);
    queryMutation.mutate(q);
  };

  const analysisResult = queryMutation.data;

  return (
    <div className="space-y-6">
      {/* 1. Proactive Daily Operational Briefing */}
      {briefing && (
        <Card className="p-6 bg-gradient-to-r from-primary/5 via-card to-amber-500/5 border-border/80 shadow-md space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border/60">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              <div>
                <h3 className="font-extrabold text-base text-foreground">
                  Proactive Daily Briefing
                </h3>
                <span className="text-xs text-muted-foreground">{briefing.date} · {briefing.store_name}</span>
              </div>
            </div>
            <Badge variant="accent" className="self-start sm:self-auto text-xs">
              AI Operations Report
            </Badge>
          </div>

          <p className="text-xs font-semibold text-foreground/90 leading-relaxed">
            {briefing.executive_summary}
          </p>

          {/* KPI Snapshot Pills */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
            <div className="p-3 rounded-xl bg-card border border-border/60">
              <span className="text-[11px] text-muted-foreground block">Today&apos;s Revenue</span>
              <span className="text-base font-extrabold text-foreground">
                {formatInr(briefing.kpis.today_revenue_inr)}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-card border border-border/60">
              <span className="text-[11px] text-muted-foreground block">Stockout Risk</span>
              <span className="text-base font-extrabold text-amber-600 dark:text-amber-400">
                {briefing.kpis.low_stock_skus} SKUs Low
              </span>
            </div>
            <div className="p-3 rounded-xl bg-card border border-border/60">
              <span className="text-[11px] text-muted-foreground block">Critical Zero-Stock</span>
              <span className="text-base font-extrabold text-destructive">
                {briefing.kpis.out_of_stock_skus} SKUs
              </span>
            </div>
            <div className="p-3 rounded-xl bg-card border border-border/60">
              <span className="text-[11px] text-muted-foreground block">Pending HITL Actions</span>
              <span className="text-base font-extrabold text-primary">
                {briefing.pending_proposals_count} Proposals
              </span>
            </div>
          </div>

          {/* Urgent Alerts List */}
          {briefing.urgent_alerts.length > 0 && (
            <div className="space-y-1.5 pt-1">
              {briefing.urgent_alerts.map((alert, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 text-xs font-medium text-amber-700 dark:text-amber-300 bg-amber-500/10 px-3 py-1.5 rounded-lg border border-amber-500/20"
                >
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                  <span>{alert}</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* 2. Interactive Store Analyst Query Bar */}
      <Card className="p-6 bg-card/70 backdrop-blur-md border-border/80 shadow-md space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary" />
            <h3 className="font-bold text-base text-foreground">
              Store Analyst (Guarded NL2SQL)
            </h3>
          </div>
          <Badge variant="outline" className="text-[10px] gap-1 font-mono">
            <ShieldCheck className="w-3 h-3 text-emerald-500" /> AST SqlGuard Active
          </Badge>
        </div>

        <form onSubmit={handleSend} className="relative">
          <Input
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask questions about physical store inventory, sales, aisles, or restock needs..."
            className="pr-24 py-6 text-sm rounded-2xl bg-card border-border/80 focus-visible:ring-primary"
          />
          <Button
            type="submit"
            disabled={queryMutation.isPending || !inputQuery.trim()}
            size="sm"
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-xl text-xs gap-1.5"
          >
            {queryMutation.isPending ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
            Analyze
          </Button>
        </form>

        {/* Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1 text-xs">
          <span className="text-muted-foreground font-semibold text-[11px] mr-1">Suggestions:</span>
          {SUGGESTED_QUERIES.map((sq) => (
            <button
              key={sq}
              type="button"
              disabled={queryMutation.isPending}
              onClick={() => handleChipClick(sq)}
              className="px-2.5 py-1 rounded-xl bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground text-[11px] border border-border/60 transition-colors"
            >
              {sq}
            </button>
          ))}
        </div>
      </Card>

      {/* 3. Analyst Query Result with Recharts */}
      {analysisResult && (
        <Card className="p-6 bg-card/70 backdrop-blur-md border-border/80 shadow-lg space-y-5 animate-in fade-in-50 duration-200">
          <div className="flex items-center justify-between pb-3 border-b border-border/60">
            <div>
              <h4 className="font-extrabold text-base text-foreground">
                {analysisResult.chart_config?.title || "Operational Analysis"}
              </h4>
              <p className="text-xs text-muted-foreground mt-0.5">
                Executive response grounded in physical database records.
              </p>
            </div>
            {analysisResult.sql_query && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSql((prev) => !prev)}
                className="text-xs gap-1.5 rounded-xl font-mono"
              >
                <Code className="w-3.5 h-3.5 text-primary" />
                {showSql ? "Hide SQL" : "View SQL"}
                {showSql ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </Button>
            )}
          </div>

          {/* Generated SQL Collapsible */}
          {showSql && analysisResult.sql_query && (
            <div className="p-3 rounded-xl bg-muted/80 font-mono text-xs text-foreground/90 border border-border/70 overflow-x-auto space-y-1">
              <div className="flex items-center justify-between text-[10px] text-muted-foreground pb-1 border-b border-border/40">
                <span>Sanitized Postgres Query (SqlGuard Verified)</span>
                <span className="text-emerald-500 font-bold">Read-Only Safe</span>
              </div>
              <pre className="whitespace-pre-wrap">{analysisResult.sql_query.trim()}</pre>
            </div>
          )}

          {/* Executive Narrative */}
          <div className="p-4 rounded-xl bg-primary/5 border border-primary/20 text-xs text-foreground/90 leading-relaxed font-medium">
            💡 {analysisResult.answer}
          </div>

          {/* Dynamic Recharts Rendering */}
          {analysisResult.data && analysisResult.data.length > 0 && (
            <div className="pt-2">
              {analysisResult.chart_config?.chart_type === "bar" && (
                <div className="h-72 w-full pt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analysisResult.data} margin={{ top: 10, right: 20, left: 0, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis
                        dataKey={analysisResult.chart_config.x_axis || "name"}
                        tick={{ fontSize: 10 }}
                        angle={-20}
                        textAnchor="end"
                      />
                      <YAxis tick={{ fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#1e293b",
                          borderColor: "#334155",
                          borderRadius: "0.75rem",
                          fontSize: "12px",
                          color: "#fff",
                        }}
                      />
                      <Bar
                        dataKey={analysisResult.chart_config.y_axis || "value"}
                        fill="#f97316"
                        radius={[6, 6, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {analysisResult.chart_config?.chart_type === "line" && (
                <div className="h-72 w-full pt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={analysisResult.data} margin={{ top: 10, right: 20, left: 0, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis
                        dataKey={analysisResult.chart_config.x_axis || "date"}
                        tick={{ fontSize: 10 }}
                      />
                      <YAxis tick={{ fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#1e293b",
                          borderColor: "#334155",
                          borderRadius: "0.75rem",
                          fontSize: "12px",
                          color: "#fff",
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey={analysisResult.chart_config.y_axis || "value"}
                        stroke="#f97316"
                        strokeWidth={3}
                        dot={{ r: 4 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {analysisResult.chart_config?.chart_type === "pie" && (
                <div className="h-72 w-full pt-4 flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={analysisResult.data}
                        dataKey={analysisResult.chart_config.y_axis || "total_units"}
                        nameKey={analysisResult.chart_config.x_axis || "department"}
                        cx="50%"
                        cy="50%"
                        outerRadius={90}
                        label={({ name, percent }: { name?: string; percent?: number }) =>
                          `${name ?? ""} (${(((percent ?? 0) * 100)).toFixed(0)}%)`
                        }
                      >
                        {analysisResult.data.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}

              {analysisResult.chart_config?.chart_type === "table" && (
                <div className="overflow-x-auto max-h-80 border border-border/60 rounded-xl">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-muted/60 text-muted-foreground uppercase text-[10px] font-semibold sticky top-0">
                      <tr>
                        {Object.keys(analysisResult.data[0] || {}).map((col) => (
                          <th key={col} className="p-2.5">
                            {col.replace("_", " ")}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/40">
                      {analysisResult.data.map((row, idx) => (
                        <tr key={idx} className="hover:bg-muted/30">
                          {Object.values(row).map((val, cIdx) => (
                            <td key={cIdx} className="p-2.5 font-mono text-[11px]">
                              {val === null || val === undefined ? "—" : String(val)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </Card>
      )}

      {/* 4. Human-in-the-Loop Action Proposals Panel */}
      <Card className="p-6 bg-card/70 backdrop-blur-md border-border/80 shadow-md space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-border/60">
          <div>
            <h3 className="font-bold text-base text-foreground flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-primary" /> Human-in-the-Loop Action Proposals
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Consequential agent recommendations requiring store manager authorization.
            </p>
          </div>
          <Badge variant="secondary" className="text-xs">
            {proposals.length} Proposals
          </Badge>
        </div>

        {proposals.length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-6">
            No active proposals. When the Store Analyst detects critical inventory imbalances, action proposals will appear here for your approval.
          </p>
        ) : (
          <div className="space-y-3">
            {proposals.map((prop) => {
              const isPending = prop.status === "pending_approval";
              const isApproved = prop.status === "approved";
              const isRejected = prop.status === "rejected";

              return (
                <div
                  key={prop.id}
                  className={`p-4 rounded-xl border transition-all space-y-2.5 ${
                    isPending
                      ? "bg-card border-primary/30 ring-1 ring-primary/20"
                      : isApproved
                      ? "bg-emerald-500/5 border-emerald-500/30"
                      : "bg-muted/20 border-border/60 opacity-60"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-bold text-sm text-foreground">{prop.title}</h4>
                        <Badge
                          variant={
                            isPending ? "warning" : isApproved ? "accent" : "secondary"
                          }
                          className="text-[10px]"
                        >
                          {prop.status.replace("_", " ")}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                        {prop.description}
                      </p>
                    </div>

                    {isPending && (
                      <div className="flex items-center gap-1.5 shrink-0">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => rejectMutation.mutate(prop.id)}
                          disabled={rejectMutation.isPending || approveMutation.isPending}
                          className="text-xs h-8 text-destructive hover:bg-destructive/10"
                        >
                          <XCircle className="w-3.5 h-3.5 mr-1" /> Reject
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => approveMutation.mutate(prop.id)}
                          disabled={approveMutation.isPending || rejectMutation.isPending}
                          className="text-xs h-8 gap-1 shadow-sm"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" /> Approve & Execute
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}

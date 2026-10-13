"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Radar,
  Package,
  Camera,
  CheckSquare,
  Sparkles,
  RefreshCw,
  Store,
} from "lucide-react";
import { StoreHeader } from "@/components/merchant/store-header";
import { KpiOverview } from "@/components/merchant/kpi-overview";
import { DemandRadar } from "@/components/merchant/demand-radar";
import { InventoryTable } from "@/components/merchant/inventory-table";
import { ShelfAuditPanel } from "@/components/merchant/shelf-audit-panel";
import { RestockTasksKanban } from "@/components/merchant/restock-tasks-kanban";
import {
  getMerchantStores,
  getStoreOverviewKpis,
  getDemandSignals,
  getStoreInventory,
  getRestockTasks,
} from "@/lib/merchant-api";

type ActiveTab = "overview" | "inventory" | "shelf-audit" | "restock-tasks";

export default function MerchantPortalPage() {
  const queryClient = useQueryClient();
  const [selectedStoreId, setSelectedStoreId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<ActiveTab>("overview");
  const [filterLowStockOnly, setFilterLowStockOnly] = useState(false);

  // 1. Fetch merchant stores
  const {
    data: stores = [],
    isLoading: isLoadingStores,
    refetch: refetchStores,
  } = useQuery({
    queryKey: ["merchant", "stores"],
    queryFn: getMerchantStores,
  });

  // Select first store on load
  useEffect(() => {
    if (stores.length > 0 && !selectedStoreId) {
      setSelectedStoreId(stores[0].id);
    }
  }, [stores, selectedStoreId]);

  // 2. Fetch KPIs
  const {
    data: kpis = null,
    isLoading: isLoadingKpis,
    refetch: refetchKpis,
  } = useQuery({
    queryKey: ["merchant", "kpis", selectedStoreId],
    queryFn: () => getStoreOverviewKpis(selectedStoreId),
    enabled: !!selectedStoreId,
  });

  // 3. Fetch Demand Signals
  const {
    data: demandSignals = [],
    isLoading: isLoadingDemand,
    refetch: refetchDemand,
  } = useQuery({
    queryKey: ["merchant", "demand", selectedStoreId],
    queryFn: () => getDemandSignals(selectedStoreId, 12),
    enabled: !!selectedStoreId,
  });

  // 4. Fetch Inventory
  const {
    data: inventory = [],
    isLoading: isLoadingInventory,
    refetch: refetchInventory,
  } = useQuery({
    queryKey: ["merchant", "inventory", selectedStoreId],
    queryFn: () => getStoreInventory(selectedStoreId),
    enabled: !!selectedStoreId,
  });

  // 5. Fetch Restock Tasks
  const {
    data: restockTasks = [],
    isLoading: isLoadingTasks,
    refetch: refetchTasks,
  } = useQuery({
    queryKey: ["merchant", "tasks", selectedStoreId],
    queryFn: () => getRestockTasks(selectedStoreId),
    enabled: !!selectedStoreId,
  });

  const handleGlobalRefresh = () => {
    if (!selectedStoreId) return;
    queryClient.invalidateQueries({ queryKey: ["merchant"] });
  };

  const handleAuditCompleted = () => {
    queryClient.invalidateQueries({ queryKey: ["merchant", "tasks", selectedStoreId] });
    queryClient.invalidateQueries({ queryKey: ["merchant", "kpis", selectedStoreId] });
    queryClient.invalidateQueries({ queryKey: ["merchant", "inventory", selectedStoreId] });
  };

  const handleViewTasks = () => {
    setActiveTab("restock-tasks");
  };

  const handleViewAtRiskSkus = () => {
    setFilterLowStockOnly(true);
    setActiveTab("inventory");
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 pb-16">
      {/* Top Navigation */}
      <StoreHeader
        stores={stores}
        selectedStoreId={selectedStoreId}
        onSelectStore={(id) => {
          setSelectedStoreId(id);
          setFilterLowStockOnly(false);
        }}
        isLoading={isLoadingStores || isLoadingKpis || isLoadingInventory}
        onRefresh={handleGlobalRefresh}
      />

      <main className="mx-auto max-w-7xl px-4 pt-6 sm:px-6 space-y-6">
        {/* KPI Overview */}
        <KpiOverview
          kpis={kpis}
          isLoading={isLoadingKpis}
          onViewTasksTab={handleViewTasks}
          onViewAtRiskSkus={handleViewAtRiskSkus}
        />

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-200 dark:border-slate-800">
          <nav className="-mb-px flex space-x-6 overflow-x-auto text-sm font-semibold">
            <button
              onClick={() => {
                setActiveTab("overview");
                setFilterLowStockOnly(false);
              }}
              className={`flex items-center gap-2 border-b-2 py-3 px-1 transition-all ${
                activeTab === "overview"
                  ? "border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400"
                  : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              <Radar className="h-4 w-4" />
              Demand Radar & Signals
            </button>

            <button
              onClick={() => {
                setActiveTab("inventory");
              }}
              className={`flex items-center gap-2 border-b-2 py-3 px-1 transition-all ${
                activeTab === "inventory"
                  ? "border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400"
                  : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              <Package className="h-4 w-4" />
              Store Inventory ({inventory.length})
            </button>

            <button
              onClick={() => {
                setActiveTab("shelf-audit");
                setFilterLowStockOnly(false);
              }}
              className={`flex items-center gap-2 border-b-2 py-3 px-1 transition-all ${
                activeTab === "shelf-audit"
                  ? "border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400"
                  : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              <Camera className="h-4 w-4" />
              AI Shelf Audit
            </button>

            <button
              onClick={() => {
                setActiveTab("restock-tasks");
                setFilterLowStockOnly(false);
              }}
              className={`flex items-center gap-2 border-b-2 py-3 px-1 transition-all ${
                activeTab === "restock-tasks"
                  ? "border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400"
                  : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              <CheckSquare className="h-4 w-4" />
              Restock Tasks ({restockTasks.filter((t) => t.status === "pending" || t.status === "approved").length})
            </button>
          </nav>
        </div>

        {/* Tab Content Panes */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            <DemandRadar
              signals={demandSignals}
              isLoading={isLoadingDemand}
            />

            {/* Quick shelf audit banner */}
            <div className="rounded-2xl border border-teal-200 bg-gradient-to-r from-teal-500/10 via-emerald-500/10 to-transparent p-5 dark:border-teal-900/50">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-teal-600" />
                    Automated Vision Shelf Audit Ready
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                    Upload shelf facing photos to detect out-of-stock gaps and auto-create replenishment work orders.
                  </p>
                </div>
                <button
                  onClick={() => setActiveTab("shelf-audit")}
                  className="rounded-xl bg-teal-600 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-700 shadow-sm"
                >
                  Start Shelf Audit
                </button>
              </div>
            </div>

            {/* Live Inventory Preview */}
            <InventoryTable
              storeId={selectedStoreId}
              items={inventory}
              isLoading={isLoadingInventory}
              onRefresh={handleGlobalRefresh}
              filterLowStock={false}
            />
          </div>
        )}

        {activeTab === "inventory" && (
          <InventoryTable
            storeId={selectedStoreId}
            items={inventory}
            isLoading={isLoadingInventory}
            onRefresh={handleGlobalRefresh}
            filterLowStock={filterLowStockOnly}
          />
        )}

        {activeTab === "shelf-audit" && (
          <ShelfAuditPanel
            storeId={selectedStoreId}
            onAuditFinished={handleAuditCompleted}
            onViewTasksTab={handleViewTasks}
          />
        )}

        {activeTab === "restock-tasks" && (
          <RestockTasksKanban
            tasks={restockTasks}
            isLoading={isLoadingTasks}
            onRefresh={handleGlobalRefresh}
          />
        )}
      </main>
    </div>
  );
}

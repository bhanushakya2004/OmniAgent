"use client";

import React, { useState, useMemo } from "react";
import {
  Search,
  Filter,
  Upload,
  Plus,
  Minus,
  Check,
  AlertCircle,
  FileSpreadsheet,
  X,
  MapPin,
  RefreshCw,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type {
  MerchantInventoryItem,
  CsvImportReport,
} from "@/lib/merchant-api";
import {
  updateStoreInventory,
  importInventoryCsv,
} from "@/lib/merchant-api";

interface InventoryTableProps {
  storeId: string;
  items: MerchantInventoryItem[];
  isLoading: boolean;
  onRefresh: () => void;
  filterLowStock?: boolean;
}

export function InventoryTable({
  storeId,
  items,
  isLoading,
  onRefresh,
  filterLowStock = false,
}: InventoryTableProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>(
    filterLowStock ? "low_stock" : "all"
  );
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  // CSV Modal State
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [isUploadingCsv, setIsUploadingCsv] = useState(false);
  const [csvReport, setCsvReport] = useState<CsvImportReport | null>(null);
  const [csvError, setCsvError] = useState<string | null>(null);

  // Quick stock adjuster
  const handleStockAdjust = async (item: MerchantInventoryItem, delta: number) => {
    const nextQty = Math.max(0, item.stock_qty + delta);
    setUpdatingId(item.id);
    try {
      await updateStoreInventory(item.id, { stock_qty: nextQty });
      onRefresh();
    } catch (err) {
      console.error("Failed to update inventory", err);
    } finally {
      setUpdatingId(null);
    }
  };

  // CSV Import handler
  const handleCsvSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvFile) return;

    setIsUploadingCsv(true);
    setCsvError(null);
    setCsvReport(null);

    try {
      const report = await importInventoryCsv(storeId, csvFile);
      setCsvReport(report);
      onRefresh();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "CSV import failed";
      setCsvError(message);
    } finally {
      setIsUploadingCsv(false);
    }
  };

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      // Status filter
      if (statusFilter === "low_stock" && item.stock_status !== "low_stock" && item.stock_status !== "out_of_stock") {
        return false;
      }
      if (statusFilter === "out_of_stock" && item.stock_status !== "out_of_stock") {
        return false;
      }
      if (statusFilter === "healthy" && item.stock_status !== "healthy") {
        return false;
      }

      // Search query
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesName = item.product_name.toLowerCase().includes(query);
        const matchesSku = item.sku.toLowerCase().includes(query);
        const matchesCategory = item.category.toLowerCase().includes(query);
        const matchesAisle = `aisle ${item.aisle}`.includes(query);
        return matchesName || matchesSku || matchesCategory || matchesAisle;
      }

      return true;
    });
  }, [items, statusFilter, searchQuery]);

  return (
    <Card className="rounded-2xl border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <CardHeader className="border-b border-slate-100 pb-4 dark:border-slate-800">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="text-base font-bold text-slate-900 dark:text-slate-100">
              Real-Time Shelf Inventory
            </CardTitle>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Live stock counts, price authority, and in-store aisle coordinates
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setCsvFile(null);
                setCsvReport(null);
                setCsvError(null);
                setIsCsvModalOpen(true);
              }}
              className="h-9 gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200"
            >
              <Upload className="h-3.5 w-3.5" />
              Batch CSV Upload
            </Button>
          </div>
        </div>

        {/* Filter controls */}
        <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative flex-1 sm:max-w-xs">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
            <Input
              type="text"
              placeholder="Filter by SKU, product, aisle..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9 pl-9 text-xs"
            />
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
            {[
              { id: "all", label: `All (${items.length})` },
              {
                id: "low_stock",
                label: `Low / At Risk (${items.filter((i) => i.stock_status === "low_stock" || i.stock_status === "out_of_stock").length})`,
              },
              {
                id: "out_of_stock",
                label: `Out of Stock (${items.filter((i) => i.stock_status === "out_of_stock").length})`,
              },
              {
                id: "healthy",
                label: `Healthy (${items.filter((i) => i.stock_status === "healthy").length})`,
              },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`whitespace-nowrap rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                  statusFilter === tab.id
                    ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-8 text-center text-xs text-slate-500">
            <RefreshCw className="mx-auto h-6 w-6 animate-spin text-slate-400 mb-2" />
            Loading real-time catalog inventory...
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500">
            No items matching your search filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-100 bg-slate-50/70 text-slate-500 dark:border-slate-800 dark:bg-slate-800/50">
                <tr>
                  <th className="px-4 py-3 font-semibold">Product & SKU</th>
                  <th className="px-4 py-3 font-semibold">Category</th>
                  <th className="px-4 py-3 font-semibold">Shelf Location</th>
                  <th className="px-4 py-3 font-semibold">Price</th>
                  <th className="px-4 py-3 font-semibold">Stock Level</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredItems.map((item) => {
                  const isUpdating = updatingId === item.id;
                  return (
                    <tr
                      key={item.id}
                      className="transition-colors hover:bg-slate-50/60 dark:hover:bg-slate-800/40"
                    >
                      <td className="px-4 py-3">
                        <p className="font-semibold text-slate-900 dark:text-slate-100">
                          {item.product_name}
                        </p>
                        <p className="font-mono text-[10px] text-slate-400">
                          {item.sku}
                        </p>
                      </td>

                      <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                        {item.category}
                      </td>

                      <td className="px-4 py-3">
                        <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 font-mono text-[11px] font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                          <MapPin className="h-3 w-3 text-emerald-600" />
                          Aisle {item.aisle} · Bay {item.bay} · Shelf {item.shelf}
                        </span>
                      </td>

                      <td className="px-4 py-3 font-semibold text-slate-900 dark:text-slate-100">
                        ₹{Number(item.price).toFixed(0)}
                      </td>

                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span
                            className={`font-mono text-sm font-bold ${
                              item.stock_qty === 0
                                ? "text-rose-600 dark:text-rose-400"
                                : item.stock_qty <= item.low_stock_threshold
                                ? "text-amber-600 dark:text-amber-400"
                                : "text-slate-800 dark:text-slate-200"
                            }`}
                          >
                            {item.stock_qty}
                          </span>
                          <span className="text-[10px] text-slate-400">units</span>
                        </div>
                      </td>

                      <td className="px-4 py-3">
                        {item.stock_status === "out_of_stock" ? (
                          <Badge variant="outline" className="border-rose-200 bg-rose-50 text-[10px] text-rose-700 dark:border-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
                            Out of Stock
                          </Badge>
                        ) : item.stock_status === "low_stock" ? (
                          <Badge variant="outline" className="border-amber-200 bg-amber-50 text-[10px] text-amber-700 dark:border-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
                            Low Stock (≤{item.low_stock_threshold})
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-[10px] text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                            In Stock
                          </Badge>
                        )}
                      </td>

                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={isUpdating || item.stock_qty <= 0}
                            onClick={() => handleStockAdjust(item, -1)}
                            className="h-7 w-7 p-0"
                            title="Decrease 1 unit"
                          >
                            <Minus className="h-3 w-3" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={isUpdating}
                            onClick={() => handleStockAdjust(item, 5)}
                            className="h-7 px-2 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400"
                            title="Restock +5 units"
                          >
                            +5
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={isUpdating}
                            onClick={() => handleStockAdjust(item, 1)}
                            className="h-7 w-7 p-0"
                            title="Increase 1 unit"
                          >
                            <Plus className="h-3 w-3" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>

      {/* CSV Batch Upload Modal */}
      {isCsvModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5 text-emerald-600" />
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Batch CSV Inventory Upload
                </h3>
              </div>
              <button
                onClick={() => setIsCsvModalOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCsvSubmit} className="mt-4 space-y-4">
              <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-300">
                <p className="font-semibold text-slate-800 dark:text-slate-200 mb-1">
                  Required CSV Columns:
                </p>
                <code className="block rounded bg-slate-200/80 p-1.5 font-mono text-[11px] text-slate-800 dark:bg-slate-950 dark:text-emerald-400">
                  sku_slug,stock_qty,aisle,bay,shelf
                </code>
                <p className="mt-1 text-[11px] text-slate-500">
                  Example: <span className="font-mono">almond-flour-500g,50,3,2,1</span>
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Select CSV File
                </label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                  className="block w-full text-xs text-slate-500 file:mr-4 file:rounded-xl file:border-0 file:bg-slate-100 file:px-4 file:py-2 file:text-xs file:font-semibold file:text-slate-700 hover:file:bg-slate-200 dark:file:bg-slate-800 dark:file:text-slate-200"
                />
              </div>

              {csvError && (
                <div className="flex items-center gap-2 rounded-xl bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-950/50 dark:text-rose-300 border border-rose-200 dark:border-rose-900">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{csvError}</span>
                </div>
              )}

              {csvReport && (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 space-y-1">
                  <p className="font-bold flex items-center gap-1.5">
                    <Check className="h-4 w-4 text-emerald-600" />
                    Batch import finished!
                  </p>
                  <p>Total Rows: {csvReport.total_rows}</p>
                  <p>Updated SKUs: {csvReport.updated_count}</p>
                  <p>New Imported SKUs: {csvReport.imported_count}</p>
                  {Boolean(csvReport.errors && csvReport.errors.length > 0) && (
                    <div className="mt-2 text-rose-600 dark:text-rose-400">
                      <p className="font-semibold">{csvReport.errors?.length} Row Errors:</p>
                      <ul className="list-disc pl-4 text-[11px]">
                        {csvReport.errors?.slice(0, 3).map((err, i) => (
                          <li key={i}>
                            {err.line ? `Line ${String(err.line)}: ` : ""}
                            {err.error ? String(err.error) : JSON.stringify(err)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsCsvModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={!csvFile || isUploadingCsv}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1.5"
                >
                  {isUploadingCsv ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      Uploading & Validating...
                    </>
                  ) : (
                    <>
                      <Upload className="h-3.5 w-3.5" />
                      Upload Batch CSV
                    </>
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Card>
  );
}

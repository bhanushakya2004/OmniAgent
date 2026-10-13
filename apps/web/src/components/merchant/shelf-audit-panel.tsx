"use client";

import React, { useState } from "react";
import {
  Camera,
  Upload,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  MapPin,
  ArrowRight,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ShelfAuditResult } from "@/lib/merchant-api";
import { uploadShelfImage, runShelfAudit } from "@/lib/merchant-api";

interface ShelfAuditPanelProps {
  storeId: string;
  onAuditFinished: () => void;
  onViewTasksTab?: () => void;
}

export function ShelfAuditPanel({
  storeId,
  onAuditFinished,
  onViewTasksTab,
}: ShelfAuditPanelProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [aisleNumber, setAisleNumber] = useState<number>(3);
  const [isRunningAudit, setIsRunningAudit] = useState(false);
  const [auditResult, setAuditResult] = useState<ShelfAuditResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setAuditResult(null);
      setErrorMessage(null);
    }
  };

  const handleExecuteAudit = async () => {
    if (!selectedFile) return;

    setIsRunningAudit(true);
    setErrorMessage(null);
    try {
      // 1. Upload photo
      const uploadRes = await uploadShelfImage(selectedFile);

      // 2. Run vision audit
      const result = await runShelfAudit({
        store_id: storeId,
        file_url: uploadRes.file_url,
        aisle: aisleNumber,
      });

      setAuditResult(result);
      onAuditFinished();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Shelf audit failed";
      setErrorMessage(msg);
    } finally {
      setIsRunningAudit(false);
    }
  };

  return (
    <Card className="rounded-2xl border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <CardHeader className="border-b border-slate-100 pb-4 dark:border-slate-800">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-50 text-teal-600 dark:bg-teal-950/60 dark:text-teal-400">
              <Camera className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-slate-900 dark:text-slate-100">
                Visual Shelf Audit (Gemini Vision)
              </CardTitle>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Analyze shelf photos, detect out-of-stock gaps, and auto-draft replenishment tasks
              </p>
            </div>
          </div>
          <Badge variant="outline" className="w-fit border-teal-200 bg-teal-50 text-xs text-teal-700 dark:border-teal-800 dark:bg-teal-950/50 dark:text-teal-300">
            <Sparkles className="mr-1 h-3 w-3 text-teal-600" />
            Multi-Modal Vision Agent
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Upload & Trigger Controls */}
          <div className="space-y-4 lg:col-span-5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Target Physical Aisle
              </label>
              <select
                value={aisleNumber}
                onChange={(e) => setAisleNumber(Number(e.target.value))}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-900 focus:outline-none dark:border-slate-800 dark:bg-slate-800 dark:text-slate-100"
              >
                <option value={1}>Aisle 1 - Staples, Rice & Grains</option>
                <option value={2}>Aisle 2 - Dairy & Fresh Curd</option>
                <option value={3}>Aisle 3 - Baking & Cocoa Essentials</option>
                <option value={4}>Aisle 4 - Snacks & Munchies</option>
                <option value={5}>Aisle 5 - Beverages & Mixers</option>
                <option value={7}>Aisle 7 - Travel Toiletries & Personal Care</option>
                <option value={8}>Aisle 8 - Protein & Health Supplements</option>
                <option value={10}>Aisle 10 - Party Disposables</option>
              </select>
            </div>

            {/* Photo dropzone */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Shelf Photograph
              </label>
              <div className="relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50/60 p-5 text-center transition-all hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-800/40 dark:hover:bg-slate-800/60">
                {previewUrl ? (
                  <div className="space-y-2">
                    <img
                      src={previewUrl}
                      alt="Shelf Preview"
                      className="mx-auto max-h-40 rounded-xl object-contain shadow-sm"
                    />
                    <p className="text-[11px] text-slate-500 font-medium">
                      {selectedFile?.name}
                    </p>
                  </div>
                ) : (
                  <>
                    <Camera className="h-8 w-8 text-slate-400 mb-2" />
                    <p className="text-xs font-medium text-slate-700 dark:text-slate-300">
                      Take or upload shelf facing photo
                    </p>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      JPEG, PNG up to 10MB
                    </p>
                  </>
                )}
                <input
                  type="file"
                  accept="image/jpeg,image/png"
                  onChange={handleFileChange}
                  className="absolute inset-0 cursor-pointer opacity-0"
                />
              </div>
            </div>

            {errorMessage && (
              <div className="flex items-center gap-2 rounded-xl bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-950/50 dark:text-rose-300 border border-rose-200 dark:border-rose-900">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <Button
              onClick={handleExecuteAudit}
              disabled={!selectedFile || isRunningAudit}
              className="w-full bg-teal-600 hover:bg-teal-700 text-white gap-2 font-semibold"
            >
              {isRunningAudit ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Gemini Auditing Shelf Facing...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Run AI Shelf Audit
                </>
              )}
            </Button>
          </div>

          {/* Audit Results Presentation */}
          <div className="lg:col-span-7">
            {auditResult ? (
              <div className="space-y-4">
                <div className="rounded-2xl border border-teal-200 bg-teal-50/80 p-4 dark:border-teal-800 dark:bg-teal-950/40">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-xs font-bold text-teal-800 dark:text-teal-200">
                      <CheckCircle2 className="h-4 w-4 text-teal-600" />
                      Shelf Audit Complete · Aisle {auditResult.aisle}
                    </span>
                    <Badge className="bg-teal-600 text-white text-[11px]">
                      {auditResult.total_gaps_detected} Gaps Detected
                    </Badge>
                  </div>
                  <p className="mt-2 text-xs text-slate-700 dark:text-slate-300">
                    {auditResult.summary}
                  </p>
                  <div className="mt-3 flex items-center justify-between border-t border-teal-200/60 pt-2 text-[11px] text-teal-800 dark:text-teal-300">
                    <span>
                      ✓ {(auditResult.findings?.length ?? 0)} Restock replenishment tasks auto-drafted.
                    </span>
                    {onViewTasksTab && (
                      <button
                        onClick={onViewTasksTab}
                        className="flex items-center gap-1 font-bold underline hover:text-teal-900"
                      >
                        View Tasks <ArrowRight className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Detected Facing Discrepancies:
                  </h4>
                  <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                    {(auditResult.findings ?? []).map((f, i) => (
                      <div
                        key={i}
                        className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-xs font-bold text-slate-900 dark:text-slate-100">
                              {f.product_name}
                            </p>
                            <span className="inline-flex items-center gap-1 font-mono text-[10px] text-slate-500">
                              <MapPin className="h-2.5 w-2.5 text-teal-600" />
                              Aisle {f.aisle} · Bay {f.bay} · Shelf {f.shelf}
                            </span>
                          </div>

                          <Badge
                            variant="outline"
                            className={
                              f.severity === "high"
                                ? "border-rose-200 bg-rose-50 text-[10px] text-rose-700"
                                : "border-amber-200 bg-amber-50 text-[10px] text-amber-700"
                            }
                          >
                            {f.severity} severity
                          </Badge>
                        </div>

                        <div className="mt-2 flex items-center justify-between text-[11px]">
                          <span className="text-slate-500">
                            Estimated Visible: <strong className="text-slate-800 dark:text-slate-200">{f.current_qty_estimate} units</strong>
                          </span>
                          <span className="font-semibold text-teal-600 dark:text-teal-400">
                            Recommended Restock: +{f.recommended_qty} units
                          </span>
                        </div>
                        <p className="mt-1 text-[11px] text-slate-500 italic">
                          "{f.reason}"
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex h-full flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 p-8 text-center dark:border-slate-800">
                <Sparkles className="h-10 w-10 text-slate-300 dark:text-slate-700 mb-2" />
                <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Ready to inspect physical shelves
                </h4>
                <p className="max-w-sm mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Upload an aisle photo to have Gemini Vision identify missing items and automatically create store replenishment checklists.
                </p>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

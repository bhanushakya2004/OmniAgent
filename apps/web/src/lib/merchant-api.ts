import { apiClient } from "./api-client";
import type { components } from "./api-types";

export type MerchantStore = components["schemas"]["MerchantStoreResponse"];
export type MerchantInventoryItem = components["schemas"]["MerchantInventoryItemResponse"];
export type UpdateInventoryPayload = components["schemas"]["UpdateInventoryRequest"];
export type CsvImportReport = components["schemas"]["CsvImportReport"];
export type StoreOverviewKpis = components["schemas"]["StoreOverviewKpis"];
export type DemandSignal = components["schemas"]["DemandSignal"];
export type ShelfAuditResult = components["schemas"]["ShelfAuditResult"];
export type RestockTask = components["schemas"]["RestockTaskResponse"];

/**
 * Fetch all stores owned by the authenticated merchant.
 */
export async function getMerchantStores(): Promise<MerchantStore[]> {
  return apiClient.get<MerchantStore[]>("/api/v1/merchant/stores");
}

/**
 * Fetch real-time inventory with shelf coordinates for a store.
 */
export async function getStoreInventory(storeId: string): Promise<MerchantInventoryItem[]> {
  return apiClient.get<MerchantInventoryItem[]>(`/api/v1/merchant/inventory?store_id=${storeId}`);
}

/**
 * Update stock quantity, price, or aisle/bay/shelf coordinates for a SKU.
 */
export async function updateStoreInventory(
  inventoryId: string,
  payload: UpdateInventoryPayload
): Promise<MerchantInventoryItem> {
  return apiClient.patch<MerchantInventoryItem>(`/api/v1/merchant/inventory/${inventoryId}`, payload);
}

/**
 * Upload inventory batch CSV file for a store.
 */
export async function importInventoryCsv(
  storeId: string,
  file: File
): Promise<CsvImportReport> {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient.post<CsvImportReport>(
    `/api/v1/merchant/inventory/import?store_id=${storeId}`,
    formData
  );
}

/**
 * Fetch store KPI telemetry (active missions, grounded GMV, at-risk SKUs).
 */
export async function getStoreOverviewKpis(storeId: string): Promise<StoreOverviewKpis> {
  return apiClient.get<StoreOverviewKpis>(`/api/v1/merchant/analytics/overview?store_id=${storeId}`);
}

/**
 * Fetch trending demand signals and out-of-stock customer queries.
 */
export async function getDemandSignals(
  storeId: string,
  limit: number = 10
): Promise<DemandSignal[]> {
  return apiClient.get<DemandSignal[]>(
    `/api/v1/merchant/analytics/demand?store_id=${storeId}&limit=${limit}`
  );
}

/**
 * Upload shelf image to storage.
 */
export async function uploadShelfImage(file: File): Promise<{ file_url: string; filename: string }> {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient.post<{ file_url: string; filename: string }>("/api/v1/uploads", formData);
}

/**
 * Conduct AI Vision shelf audit on uploaded photo.
 */
export async function runShelfAudit(payload: {
  store_id: string;
  file_url: string;
  aisle: number;
}): Promise<ShelfAuditResult> {
  return apiClient.post<ShelfAuditResult>("/api/v1/merchant/shelf-audit", payload);
}

/**
 * List replenishment restock tasks for a store.
 */
export async function getRestockTasks(storeId: string): Promise<RestockTask[]> {
  return apiClient.get<RestockTask[]>(`/api/v1/merchant/restock-tasks?store_id=${storeId}`);
}

/**
 * Update replenishment restock task status.
 */
export async function updateRestockTask(
  taskId: string,
  status: "pending" | "approved" | "completed" | "dismissed"
): Promise<RestockTask> {
  return apiClient.patch<RestockTask>(`/api/v1/merchant/restock-tasks/${taskId}`, { status });
}

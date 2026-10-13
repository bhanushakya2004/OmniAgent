/**
 * Centralized React Query key factory to eliminate magic strings
 * and guarantee predictable cache invalidation.
 */

export const queryKeys = {
  auth: {
    me: () => ["auth", "me"] as const,
  },
  stores: {
    all: () => ["stores"] as const,
    nearby: (lat: number, lng: number, radius = 25) =>
      ["stores", "nearby", { lat, lng, radius }] as const,
    detail: (id: string) => ["stores", "detail", id] as const,
    search: (query: string) => ["stores", "search", query] as const,
  },
  catalog: {
    search: (q: string, storeIds: string[], filters?: Record<string, unknown>) =>
      ["catalog", "search", { q, storeIds, ...filters }] as const,
  },
  missions: {
    list: () => ["missions", "list"] as const,
    detail: (id: string) => ["missions", "detail", id] as const,
    route: (id: string) => ["missions", "route", id] as const,
  },
  merchant: {
    stores: () => ["merchant", "stores"] as const,
    inventory: (storeId?: string) => ["merchant", "inventory", storeId] as const,
    overview: (storeId?: string) => ["merchant", "overview", storeId] as const,
    demand: (storeId?: string) => ["merchant", "demand", storeId] as const,
    stockoutRisk: (storeId?: string) => ["merchant", "stockout-risk", storeId] as const,
    restockTasks: (storeId?: string) => ["merchant", "restock-tasks", storeId] as const,
    shelfAudits: (storeId?: string) => ["merchant", "shelf-audits", storeId] as const,
  },
};

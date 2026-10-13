/**
 * Strongly typed HTTP client with automatic JWT bearer attachment,
 * single-flight refresh token rotation, and RFC 7807 problem handling.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

export class ApiError extends Error {
  status: number;
  code: string;
  detail: string;
  errors?: Array<Record<string, unknown>>;

  constructor(status: number, code: string, detail: string, errors?: Array<Record<string, unknown>>) {
    super(detail);
    this.status = status;
    this.code = code;
    this.detail = detail;
    this.errors = errors;
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  // Attach token from localStorage if available in browser
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("omni_access_token");
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // send cookies for refresh token
  });

  if (response.status === 401 && !endpoint.includes("/auth/login") && !endpoint.includes("/auth/refresh")) {
    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve: resolve as (v: unknown) => void, reject });
      }).then((newToken) => {
        headers.set("Authorization", `Bearer ${newToken}`);
        return fetch(url, { ...options, headers, credentials: "include" }).then((res) => res.json());
      });
    }

    isRefreshing = true;

    try {
      const refreshRes = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });

      if (!refreshRes.ok) {
        throw new Error("Refresh failed");
      }

      const refreshData = await refreshRes.json();
      const newToken = refreshData.access_token as string;

      if (typeof window !== "undefined") {
        localStorage.setItem("omni_access_token", newToken);
      }

      processQueue(null, newToken);
      headers.set("Authorization", `Bearer ${newToken}`);

      const retryRes = await fetch(url, { ...options, headers, credentials: "include" });
      return (await retryRes.json()) as T;
    } catch (refreshErr) {
      processQueue(refreshErr, null);
      if (typeof window !== "undefined") {
        localStorage.removeItem("omni_access_token");
        localStorage.removeItem("omni_user");
        window.location.href = "/login";
      }
      throw refreshErr;
    } finally {
      isRefreshing = false;
    }
  }

  if (!response.ok) {
    let errorData: { code?: string; detail?: string; errors?: Array<Record<string, unknown>> } = {};
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText, code: "UNKNOWN_ERROR" };
    }
    throw new ApiError(
      response.status,
      errorData.code || "API_ERROR",
      errorData.detail || "An unexpected error occurred",
      errorData.errors
    );
  }

  if (response.status === 204) {
    return {} as T;
  }

  return (await response.json()) as T;
}

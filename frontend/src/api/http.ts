const DEFAULT_API_BASE_URL = "http://localhost:8080";
const API_BASE_URL_STORAGE_KEY = "tp-api-base-url";

function canUseWindow(): boolean {
  return typeof window !== "undefined";
}

export function getStoredApiBaseUrl(): string {
  if (!canUseWindow()) {
    return "";
  }

  return window.localStorage.getItem(API_BASE_URL_STORAGE_KEY)?.trim() ?? "";
}

export function setStoredApiBaseUrl(value: string): void {
  if (!canUseWindow()) {
    return;
  }

  const normalized = value.trim();
  if (!normalized) {
    window.localStorage.removeItem(API_BASE_URL_STORAGE_KEY);
    return;
  }

  window.localStorage.setItem(API_BASE_URL_STORAGE_KEY, normalized);
}

export function getApiBaseUrl(): string {
  return getStoredApiBaseUrl() || import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

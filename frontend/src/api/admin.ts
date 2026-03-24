import { apiFetch } from "./http";

export interface BootstrapResponse {
  status: string;
}

export interface SeedDefaultJarsResponse {
  created: number;
  skipped: number;
  items: Array<{
    code: string;
    name: string;
    status: string;
  }>;
}

export interface InitializeSystemResponse {
  status: string;
  bootstrapStatus: string;
  defaultJars: SeedDefaultJarsResponse;
}

export interface MigrationItem {
  jarCode: string;
  jarName: string;
  sourceCode: string;
  status: string;
  reason: string;
}

export interface MigrationResult {
  dryRun: boolean;
  candidates: number;
  created: number;
  skipped: number;
  items: MigrationItem[];
}

export function bootstrapSheets(): Promise<BootstrapResponse> {
  return apiFetch<BootstrapResponse>("/api/v1/admin/bootstrap", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function initializeSystem(): Promise<InitializeSystemResponse> {
  return apiFetch<InitializeSystemResponse>("/api/v1/admin/initialize-system", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function migrateLegacyJars(dryRun: boolean): Promise<MigrationResult> {
  return apiFetch<MigrationResult>("/api/v1/admin/migrate-legacy-jars", {
    method: "POST",
    body: JSON.stringify({ dryRun }),
  });
}

export function seedDefaultJars(): Promise<SeedDefaultJarsResponse> {
  return apiFetch<SeedDefaultJarsResponse>("/api/v1/admin/seed-default-jars", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

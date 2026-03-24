import { apiFetch } from "./http";

export interface Source {
  code: string;
  name: string;
  kind: string;
  provider: string;
  linkedJarCode: string;
  openingBalance: number;
  actualBalance: number;
  goldQuantityChi: number;
  goldPricePerChi: number;
  isActive: boolean;
  note: string;
}

export interface SourceInput {
  code: string;
  name: string;
  kind: string;
  provider: string;
  linkedJarCode: string;
  openingBalance: number;
  actualBalance?: number;
  goldQuantityChi: number;
  goldPricePerChi: number;
  isActive: boolean;
  note: string;
}

export interface SourceUpdateInput {
  name: string;
  kind: string;
  provider: string;
  linkedJarCode: string;
  openingBalance: number;
  actualBalance: number;
  goldQuantityChi: number;
  goldPricePerChi: number;
  isActive: boolean;
  note: string;
}

interface ListSourcesResponse {
  items: Source[];
}

export function listSources(): Promise<ListSourcesResponse> {
  return apiFetch<ListSourcesResponse>("/api/v1/sources");
}

export function createSource(input: SourceInput): Promise<Source> {
  return apiFetch<Source>("/api/v1/sources", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateSource(code: string, input: SourceUpdateInput): Promise<Source> {
  return apiFetch<Source>(`/api/v1/sources/${encodeURIComponent(code)}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

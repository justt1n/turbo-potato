import { apiFetch } from "./http";

export interface AssetItem {
  code: string;
  name: string;
  kind: string;
  provider: string;
  linkedJarCode: string;
  openingBalance: number;
  inflowTotal: number;
  outflowTotal: number;
  bookBalance: number;
  actualBalance: number;
  goldQuantityChi: number;
  goldPricePerChi: number;
  discrepancy: number;
  isActive: boolean;
  note: string;
  lastActivityAt?: string;
}

export interface JarTotal {
  jarCode: string;
  totalBookBalance: number;
  totalActualBalance: number;
  sourceCount: number;
}

export interface AssetOverview {
  totalBookBalance: number;
  totalActualBalance: number;
  totalDiscrepancy: number;
  activeSources: number;
  jarTotals: JarTotal[];
  items: AssetItem[];
}

export function getAssetsOverview(): Promise<AssetOverview> {
  return apiFetch<AssetOverview>("/api/v1/assets/overview");
}

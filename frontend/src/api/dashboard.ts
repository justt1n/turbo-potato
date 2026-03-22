import { apiFetch } from "./http";

export interface DashboardMetricValue {
  label: string;
  value: string;
  caption: string;
  progress: number;
  status: string;
}

export interface DashboardSummaryItem {
  label: string;
  value: string;
}

export interface DashboardBaselineSeries {
  label: string;
  description: string;
  values: number[];
  current: string;
  delta: string;
  colorToken: string;
}

export interface DashboardSummary {
  sts: DashboardMetricValue;
  anomaly: DashboardMetricValue;
  tar: DashboardMetricValue;
  goalPace: DashboardMetricValue;
  operatingPosture: {
    status: string;
    items: DashboardSummaryItem[];
  };
  baselines: DashboardBaselineSeries[];
}

export interface DashboardReport {
  id: string;
  kind: "daily" | "monthly";
  periodKey: string;
  title: string;
  summary: string;
  body: string;
  verdict: string;
  status: string;
  model: string;
  promptSource: string;
  trigger: string;
  createdAt: string;
}

export interface DashboardReportsSnapshot {
  daily: DashboardReport;
  monthly?: DashboardReport;
}

export function getDashboardSummary(): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>("/api/v1/dashboard/summary");
}

export function getDashboardReports(): Promise<DashboardReportsSnapshot> {
  return apiFetch<DashboardReportsSnapshot>("/api/v1/dashboard/reports");
}

export function generateMonthlyReport(): Promise<DashboardReport> {
  return apiFetch<DashboardReport>("/api/v1/dashboard/reports/monthly", {
    method: "POST",
    body: JSON.stringify({ trigger: "manual-dashboard" }),
  });
}

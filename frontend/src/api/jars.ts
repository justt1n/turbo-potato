import { apiFetch } from "./http";

export interface Jar {
  code: string;
  name: string;
  kind: string;
  openingBalance: number;
  actualBalance: number;
  isActive: boolean;
  note: string;
}

export interface JarInput {
  code: string;
  name: string;
  kind: string;
  openingBalance: number;
  actualBalance?: number;
  isActive: boolean;
  note: string;
}

export interface JarUpdateInput {
  name: string;
  kind: string;
  openingBalance: number;
  actualBalance: number;
  isActive: boolean;
  note: string;
}

interface ListJarsResponse {
  items: Jar[];
}

export function listJars(): Promise<ListJarsResponse> {
  return apiFetch<ListJarsResponse>("/api/v1/jars");
}

export function createJar(input: JarInput): Promise<Jar> {
  return apiFetch<Jar>("/api/v1/jars", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateJar(code: string, input: JarUpdateInput): Promise<Jar> {
  return apiFetch<Jar>(`/api/v1/jars/${encodeURIComponent(code)}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

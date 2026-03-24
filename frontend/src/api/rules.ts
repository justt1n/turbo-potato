import { apiFetch } from "./http";

export interface FixedCostRule {
  name: string;
  expectedAmount: number;
  windowStartDay: number;
  windowEndDay: number;
  linkedJarCode?: string;
  isActive: boolean;
}

export interface FixedCostRuleInput {
  name: string;
  expectedAmount: number;
  windowStartDay: number;
  windowEndDay: number;
  linkedJarCode?: string;
  isActive: boolean;
}

export interface FixedCostRuleUpdateInput {
  expectedAmount: number;
  windowStartDay: number;
  windowEndDay: number;
  linkedJarCode?: string;
  isActive: boolean;
}

interface ListRulesResponse {
  items: FixedCostRule[];
}

export function listFixedCostRules(): Promise<ListRulesResponse> {
  return apiFetch<ListRulesResponse>("/api/v1/fixed-cost-rules");
}

export function createFixedCostRule(input: FixedCostRuleInput): Promise<FixedCostRule> {
  return apiFetch<FixedCostRule>("/api/v1/fixed-cost-rules", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateFixedCostRule(ruleName: string, input: FixedCostRuleUpdateInput): Promise<FixedCostRule> {
  return apiFetch<FixedCostRule>(`/api/v1/fixed-cost-rules/${encodeURIComponent(ruleName)}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

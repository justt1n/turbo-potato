import { apiFetch } from "./http";

export type GoalStatus = "active" | "completed" | "paused";

export interface Goal {
  name: string;
  targetAmount: number;
  startDate: string;
  targetDate?: string;
  status: GoalStatus;
}

export interface GoalInput {
  name: string;
  targetAmount: number;
  startDate?: string;
  targetDate?: string;
  status?: GoalStatus;
}

export interface GoalUpdateInput {
  targetAmount: number;
  startDate?: string;
  targetDate?: string;
  status: GoalStatus;
}

interface ListGoalsResponse {
  items: Goal[];
}

export function listGoals(): Promise<ListGoalsResponse> {
  return apiFetch<ListGoalsResponse>("/api/v1/goals");
}

export function createGoal(input: GoalInput): Promise<Goal> {
  return apiFetch<Goal>("/api/v1/goals", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateGoal(goalName: string, input: GoalUpdateInput): Promise<Goal> {
  return apiFetch<Goal>(`/api/v1/goals/${encodeURIComponent(goalName)}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

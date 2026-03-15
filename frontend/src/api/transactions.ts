import { apiFetch } from "./http";

export type TransactionType = "IN" | "OUT" | "TRANSFER";

export interface Transaction {
  id: string;
  occurredAt: string;
  type: TransactionType;
  amount: number;
  currency: string;
  jarCode?: string;
  goalName?: string;
  accountName?: string;
  isFixed: boolean;
  note: string;
  source: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateTransactionInput {
  occurredAt?: string;
  type: TransactionType;
  amount: number;
  currency: string;
  jarCode?: string;
  goalName?: string;
  accountName?: string;
  isFixed: boolean;
  note: string;
  source: string;
}

interface ListTransactionsResponse {
  items: Transaction[];
}

export function listTransactions(): Promise<ListTransactionsResponse> {
  return apiFetch<ListTransactionsResponse>("/api/v1/transactions");
}

export function createTransaction(input: CreateTransactionInput): Promise<Transaction> {
  return apiFetch<Transaction>("/api/v1/transactions", {
    method: "POST",
    body: JSON.stringify(input),
  });
}


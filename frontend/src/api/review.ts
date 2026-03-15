import { apiFetch } from "./http";
import type { Transaction } from "./transactions";

export interface ParsedReceipt {
  id: string;
  transactionId: string;
  rawInput: string;
  regexAmount: number;
  regexTags: string[];
  llmModel: string;
  llmOutputJson: string;
  validationNote: string;
  confidence: string;
  promptSource: string;
  createdAt: string;
}

export interface ParsedReceiptReviewItem {
  receipt: ParsedReceipt;
  transaction?: Transaction;
}

interface ListParsedReceiptsResponse {
  items: ParsedReceiptReviewItem[];
}

export function listParsedReceipts(): Promise<ListParsedReceiptsResponse> {
  return apiFetch<ListParsedReceiptsResponse>("/api/v1/parsed-receipts");
}

export function getParsedReceipt(receiptId: string): Promise<ParsedReceiptReviewItem> {
  return apiFetch<ParsedReceiptReviewItem>(`/api/v1/parsed-receipts/${receiptId}`);
}

interface ReviewActionInput {
  reason?: string;
  actor?: string;
}

export interface CorrectParsedReceiptInput {
  occurredAt: string;
  type: "IN" | "OUT" | "TRANSFER";
  amount: number;
  currency: string;
  jarCode?: string;
  goalName?: string;
  accountName?: string;
  isFixed?: boolean;
  note?: string;
  status?: "draft" | "confirmed" | "reverted";
  reason?: string;
  actor?: string;
}

export function confirmParsedReceipt(receiptId: string, input: ReviewActionInput = {}): Promise<ParsedReceiptReviewItem> {
  return apiFetch<ParsedReceiptReviewItem>(`/api/v1/parsed-receipts/${receiptId}/confirm`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function undoParsedReceipt(receiptId: string, input: ReviewActionInput = {}): Promise<ParsedReceiptReviewItem> {
  return apiFetch<ParsedReceiptReviewItem>(`/api/v1/parsed-receipts/${receiptId}/undo`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function correctParsedReceipt(
  receiptId: string,
  input: CorrectParsedReceiptInput,
): Promise<ParsedReceiptReviewItem> {
  return apiFetch<ParsedReceiptReviewItem>(`/api/v1/parsed-receipts/${receiptId}/correct`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

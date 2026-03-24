import { apiFetch } from "./http";

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

export interface ChatIngestionInput {
  rawInput: string;
  source?: string;
  actor?: string;
}

export interface ChatIngestionResult {
  transactionId: string;
  receipt: ParsedReceipt;
}

export function ingestChat(input: ChatIngestionInput): Promise<ChatIngestionResult> {
  return apiFetch<ChatIngestionResult>("/api/v1/ingestion/chat", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

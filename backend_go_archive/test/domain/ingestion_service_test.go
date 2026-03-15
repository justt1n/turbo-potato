package domain_test

import (
	"context"
	"testing"
	"time"

	"github.com/admin/turbo-potato/backend/internal/ai"
	"github.com/admin/turbo-potato/backend/internal/domain/ingestion"
	"github.com/admin/turbo-potato/backend/internal/domain/transactions"
)

type fakeReceiptRepository struct {
	items []ingestion.ParsedReceipt
}

func (r *fakeReceiptRepository) SaveParsedReceipt(_ context.Context, receipt ingestion.ParsedReceipt) (ingestion.ParsedReceipt, error) {
	r.items = append(r.items, receipt)
	return receipt, nil
}

type fakeAIClient struct {
	output ai.CompletionOutput
	err    error
}

func (c fakeAIClient) Complete(context.Context, ai.CompletionInput) (ai.CompletionOutput, error) {
	return c.output, c.err
}

func TestIngestionUsesLLMSuggestionButRegexOverridesAmount(t *testing.T) {
	txRepo := &fakeTransactionsRepository{}
	audit := &fakeAuditLogger{}
	txService := transactions.NewService(txRepo, audit, fakeIDGenerator{}, fakeClock{})
	receipts := &fakeReceiptRepository{}

	service := ingestion.NewService(
		txService,
		receipts,
		fakeAIClient{
			output: ai.CompletionOutput{
				Model: "gpt-5-mini",
				Text:  `{"action":"OUT","amount":999999,"jar_category":"GiaoDuc","is_fixed":false,"clean_note":"coffee with team"}`,
			},
		},
		fakeClock{},
		"gpt-5-mini",
		`Raw: {{raw_input}} Amount: {{regex_amount}}`,
		"test-prompt",
	)

	result, err := service.IngestChat(context.Background(), ingestion.IngestInput{
		RawInput: "di nhau 500k #team",
		Source:   "chat",
	})
	if err != nil {
		t.Fatalf("IngestChat() error = %v", err)
	}

	if result.TransactionID == "" {
		t.Fatal("expected transaction id")
	}
	if len(txRepo.items) != 1 {
		t.Fatalf("expected one transaction, got %d", len(txRepo.items))
	}
	if txRepo.items[0].Amount != 500000 {
		t.Fatalf("expected regex amount to win, got %d", txRepo.items[0].Amount)
	}
	if txRepo.items[0].JarCode != "GiaoDuc" {
		t.Fatalf("expected llm jar suggestion, got %s", txRepo.items[0].JarCode)
	}
	if len(receipts.items) != 1 {
		t.Fatalf("expected one parsed receipt, got %d", len(receipts.items))
	}
	if receipts.items[0].ValidationNote != "amount overridden by regex after llm mismatch" {
		t.Fatalf("unexpected validation note: %s", receipts.items[0].ValidationNote)
	}
}

func TestIngestionFallsBackWhenAIUnavailable(t *testing.T) {
	txRepo := &fakeTransactionsRepository{}
	audit := &fakeAuditLogger{}
	txService := transactions.NewService(txRepo, audit, fakeIDGenerator{}, fakeClock{})
	receipts := &fakeReceiptRepository{}

	service := ingestion.NewService(
		txService,
		receipts,
		ai.NoopClient{},
		fakeClock{},
		"",
		"",
		"none",
	)

	_, err := service.IngestChat(context.Background(), ingestion.IngestInput{
		RawInput: "thu freelance 2tr",
		Source:   "chat",
	})
	if err != nil {
		t.Fatalf("IngestChat() error = %v", err)
	}

	if len(txRepo.items) != 1 {
		t.Fatalf("expected one transaction, got %d", len(txRepo.items))
	}
	if txRepo.items[0].Type != transactions.TypeIncome {
		t.Fatalf("expected fallback income classification, got %s", txRepo.items[0].Type)
	}
	if receipts.items[0].PromptSource != "none" {
		t.Fatalf("expected prompt source none, got %s", receipts.items[0].PromptSource)
	}
}

func TestFakeClockStillStableForIngestion(t *testing.T) {
	if got := (fakeClock{}).Now(); !got.Equal(time.Date(2026, 3, 15, 10, 0, 0, 0, time.UTC)) {
		t.Fatalf("unexpected fake clock value: %v", got)
	}
}

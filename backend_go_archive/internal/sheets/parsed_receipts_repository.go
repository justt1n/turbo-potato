package sheets

import (
	"context"
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/admin/turbo-potato/backend/internal/domain/ingestion"
)

const parsedReceiptsRange = "Parsed_Receipts!A:K"

type GoogleParsedReceiptsRepository struct {
	client        ValuesAPI
	spreadsheetID string
}

func NewGoogleParsedReceiptsRepository(client ValuesAPI, spreadsheetID string) *GoogleParsedReceiptsRepository {
	return &GoogleParsedReceiptsRepository{
		client:        client,
		spreadsheetID: spreadsheetID,
	}
}

func (r *GoogleParsedReceiptsRepository) SaveParsedReceipt(ctx context.Context, receipt ingestion.ParsedReceipt) (ingestion.ParsedReceipt, error) {
	row := [][]interface{}{{
		receipt.ID,
		receipt.TransactionID,
		receipt.RawInput,
		receipt.RegexAmount,
		strings.Join(receipt.RegexTags, ","),
		receipt.LLMModel,
		receipt.LLMOutputJSON,
		receipt.ValidationNote,
		receipt.Confidence,
		receipt.PromptSource,
		receipt.CreatedAt.UTC().Format(time.RFC3339),
	}}
	if err := r.client.Append(ctx, r.spreadsheetID, parsedReceiptsRange, row); err != nil {
		return ingestion.ParsedReceipt{}, err
	}
	return receipt, nil
}

type MemoryParsedReceiptsRepository struct {
	mu    sync.Mutex
	items []ingestion.ParsedReceipt
}

func NewMemoryParsedReceiptsRepository() *MemoryParsedReceiptsRepository {
	return &MemoryParsedReceiptsRepository{
		items: make([]ingestion.ParsedReceipt, 0),
	}
}

func (r *MemoryParsedReceiptsRepository) SaveParsedReceipt(_ context.Context, receipt ingestion.ParsedReceipt) (ingestion.ParsedReceipt, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.items = append(r.items, receipt)
	return receipt, nil
}

func parseTagsCSV(raw string) []string {
	if strings.TrimSpace(raw) == "" {
		return nil
	}
	parts := strings.Split(raw, ",")
	out := make([]string, 0, len(parts))
	for _, part := range parts {
		if trimmed := strings.TrimSpace(part); trimmed != "" {
			out = append(out, trimmed)
		}
	}
	return out
}

func parsedReceiptFromRow(row []interface{}) (ingestion.ParsedReceipt, error) {
	if len(row) < 11 {
		return ingestion.ParsedReceipt{}, fmt.Errorf("parsed receipt row has %d columns, expected at least 11", len(row))
	}

	createdAt, err := time.Parse(time.RFC3339, stringify(row[10]))
	if err != nil {
		return ingestion.ParsedReceipt{}, fmt.Errorf("parse parsed receipt createdAt: %w", err)
	}

	var rawJSON string
	switch typed := row[6].(type) {
	case string:
		rawJSON = typed
	default:
		bytes, _ := json.Marshal(typed)
		rawJSON = string(bytes)
	}

	return ingestion.ParsedReceipt{
		ID:             stringify(row[0]),
		TransactionID:  stringify(row[1]),
		RawInput:       stringify(row[2]),
		RegexAmount:    parseInt64Safe(stringify(row[3])),
		RegexTags:      parseTagsCSV(stringify(row[4])),
		LLMModel:       stringify(row[5]),
		LLMOutputJSON:  rawJSON,
		ValidationNote: stringify(row[7]),
		Confidence:     stringify(row[8]),
		PromptSource:   stringify(row[9]),
		CreatedAt:      createdAt,
	}, nil
}

func parseInt64Safe(raw string) int64 {
	value, err := strconv.ParseInt(raw, 10, 64)
	if err != nil {
		return 0
	}
	return value
}

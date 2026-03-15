package sheets

import (
	"context"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/admin/turbo-potato/backend/internal/domain/transactions"
)

const transactionsRange = "Transactions!A:N"

type GoogleTransactionRepository struct {
	client        ValuesAPI
	spreadsheetID string
}

func NewGoogleTransactionRepository(client ValuesAPI, spreadsheetID string) *GoogleTransactionRepository {
	return &GoogleTransactionRepository{
		client:        client,
		spreadsheetID: spreadsheetID,
	}
}

func (r *GoogleTransactionRepository) CreateTransaction(ctx context.Context, tx transactions.Transaction) (transactions.Transaction, error) {
	row := [][]interface{}{transactionToRow(tx)}
	if err := r.client.Append(ctx, r.spreadsheetID, transactionsRange, row); err != nil {
		return transactions.Transaction{}, err
	}

	return tx, nil
}

func (r *GoogleTransactionRepository) GetTransaction(ctx context.Context, id string) (transactions.Transaction, error) {
	rows, err := r.client.Get(ctx, r.spreadsheetID, "Transactions!A2:N")
	if err != nil {
		return transactions.Transaction{}, err
	}

	for _, row := range rows {
		if len(row) == 0 {
			continue
		}

		if stringify(row[0]) == id {
			return transactionFromRow(row)
		}
	}

	return transactions.Transaction{}, fmt.Errorf("transaction %s not found", id)
}

func (r *GoogleTransactionRepository) UpdateTransaction(ctx context.Context, tx transactions.Transaction) (transactions.Transaction, error) {
	rows, err := r.client.Get(ctx, r.spreadsheetID, "Transactions!A2:N")
	if err != nil {
		return transactions.Transaction{}, err
	}

	for index, row := range rows {
		if len(row) == 0 {
			continue
		}

		if stringify(row[0]) == tx.ID {
			rangeRef := fmt.Sprintf("Transactions!A%d:N%d", index+2, index+2)
			if err := r.client.Update(ctx, r.spreadsheetID, rangeRef, [][]interface{}{transactionToRow(tx)}); err != nil {
				return transactions.Transaction{}, err
			}
			return tx, nil
		}
	}

	return transactions.Transaction{}, fmt.Errorf("transaction %s not found", tx.ID)
}

func (r *GoogleTransactionRepository) ListTransactions(ctx context.Context) ([]transactions.Transaction, error) {
	rows, err := r.client.Get(ctx, r.spreadsheetID, "Transactions!A2:N")
	if err != nil {
		return nil, err
	}

	items := make([]transactions.Transaction, 0, len(rows))
	for _, row := range rows {
		if len(row) == 0 {
			continue
		}

		tx, err := transactionFromRow(row)
		if err != nil {
			return nil, err
		}

		items = append(items, tx)
	}

	return items, nil
}

type GoogleAuditLogger struct {
	client        ValuesAPI
	spreadsheetID string
}

func NewGoogleAuditLogger(client ValuesAPI, spreadsheetID string) *GoogleAuditLogger {
	return &GoogleAuditLogger{
		client:        client,
		spreadsheetID: spreadsheetID,
	}
}

func (l *GoogleAuditLogger) Log(ctx context.Context, entry transactions.AuditEntry) error {
	return l.client.Append(ctx, l.spreadsheetID, "Audit_Log!A:H", [][]interface{}{{
		entry.ID,
		entry.TransactionID,
		entry.Action,
		entry.PreviousValue,
		entry.NewValue,
		entry.Reason,
		entry.Actor,
		entry.CreatedAt.UTC().Format(time.RFC3339),
	}})
}

func transactionToRow(tx transactions.Transaction) []interface{} {
	return []interface{}{
		tx.ID,
		tx.OccurredAt.UTC().Format(time.RFC3339),
		string(tx.Type),
		tx.Amount,
		tx.Currency,
		tx.JarCode,
		tx.GoalName,
		tx.Account,
		tx.IsFixed,
		tx.Note,
		tx.Source,
		string(tx.Status),
		tx.CreatedAt.UTC().Format(time.RFC3339),
		tx.UpdatedAt.UTC().Format(time.RFC3339),
	}
}

func transactionFromRow(row []interface{}) (transactions.Transaction, error) {
	if len(row) < 14 {
		return transactions.Transaction{}, fmt.Errorf("transaction row has %d columns, expected at least 14", len(row))
	}

	occurredAt, err := time.Parse(time.RFC3339, stringify(row[1]))
	if err != nil {
		return transactions.Transaction{}, fmt.Errorf("parse occurredAt: %w", err)
	}

	amount, err := strconv.ParseInt(stringify(row[3]), 10, 64)
	if err != nil {
		return transactions.Transaction{}, fmt.Errorf("parse amount: %w", err)
	}

	isFixed, err := strconv.ParseBool(strings.ToLower(stringify(row[8])))
	if err != nil {
		return transactions.Transaction{}, fmt.Errorf("parse isFixed: %w", err)
	}

	createdAt, err := time.Parse(time.RFC3339, stringify(row[12]))
	if err != nil {
		return transactions.Transaction{}, fmt.Errorf("parse createdAt: %w", err)
	}

	updatedAt, err := time.Parse(time.RFC3339, stringify(row[13]))
	if err != nil {
		return transactions.Transaction{}, fmt.Errorf("parse updatedAt: %w", err)
	}

	return transactions.Transaction{
		ID:         stringify(row[0]),
		OccurredAt: occurredAt,
		Type:       transactions.Type(stringify(row[2])),
		Amount:     amount,
		Currency:   stringify(row[4]),
		JarCode:    stringify(row[5]),
		GoalName:   stringify(row[6]),
		Account:    stringify(row[7]),
		IsFixed:    isFixed,
		Note:       stringify(row[9]),
		Source:     stringify(row[10]),
		Status:     transactions.Status(stringify(row[11])),
		CreatedAt:  createdAt,
		UpdatedAt:  updatedAt,
	}, nil
}

func stringify(value interface{}) string {
	switch typed := value.(type) {
	case string:
		return typed
	case bool:
		return strconv.FormatBool(typed)
	case int64:
		return strconv.FormatInt(typed, 10)
	case float64:
		return strconv.FormatInt(int64(typed), 10)
	default:
		return fmt.Sprint(typed)
	}
}

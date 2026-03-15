package domain_test

import (
	"context"
	"testing"
	"time"

	"github.com/admin/turbo-potato/backend/internal/domain/transactions"
)

type fakeTransactionsRepository struct {
	items []transactions.Transaction
}

func (r *fakeTransactionsRepository) CreateTransaction(_ context.Context, tx transactions.Transaction) (transactions.Transaction, error) {
	r.items = append(r.items, tx)
	return tx, nil
}

func (r *fakeTransactionsRepository) GetTransaction(_ context.Context, id string) (transactions.Transaction, error) {
	for _, item := range r.items {
		if item.ID == id {
			return item, nil
		}
	}
	return transactions.Transaction{}, context.DeadlineExceeded
}

func (r *fakeTransactionsRepository) UpdateTransaction(_ context.Context, tx transactions.Transaction) (transactions.Transaction, error) {
	for index, item := range r.items {
		if item.ID == tx.ID {
			r.items[index] = tx
			return tx, nil
		}
	}
	return transactions.Transaction{}, context.DeadlineExceeded
}

func (r *fakeTransactionsRepository) ListTransactions(_ context.Context) ([]transactions.Transaction, error) {
	return append([]transactions.Transaction(nil), r.items...), nil
}

type fakeIDGenerator struct{}

func (fakeIDGenerator) NewTransactionID() string { return "TX-001" }

type fakeClock struct{}

func (fakeClock) Now() time.Time {
	return time.Date(2026, 3, 15, 10, 0, 0, 0, time.UTC)
}

type fakeAuditLogger struct {
	entries []transactions.AuditEntry
}

func (l *fakeAuditLogger) Log(_ context.Context, entry transactions.AuditEntry) error {
	l.entries = append(l.entries, entry)
	return nil
}

func TestCreateTransactionDefaults(t *testing.T) {
	repo := &fakeTransactionsRepository{}
	audit := &fakeAuditLogger{}
	service := transactions.NewService(repo, audit, fakeIDGenerator{}, fakeClock{})

	transaction, err := service.Create(context.Background(), transactions.CreateInput{
		Type:   transactions.TypeExpense,
		Amount: 500000,
	})
	if err != nil {
		t.Fatalf("Create() error = %v", err)
	}

	if transaction.ID != "TX-001" {
		t.Fatalf("expected generated id, got %q", transaction.ID)
	}
}

func TestCorrectTransactionWritesAudit(t *testing.T) {
	repo := &fakeTransactionsRepository{
		items: []transactions.Transaction{{
			ID:         "TX-001",
			OccurredAt: time.Date(2026, 3, 15, 10, 0, 0, 0, time.UTC),
			Type:       transactions.TypeExpense,
			Amount:     500000,
			Currency:   "VND",
			Note:       "wrong jar",
			Status:     transactions.StatusConfirmed,
		}},
	}
	audit := &fakeAuditLogger{}
	service := transactions.NewService(repo, audit, fakeIDGenerator{}, fakeClock{})

	updated, err := service.Correct(context.Background(), "TX-001", transactions.UpdateInput{
		OccurredAt: time.Date(2026, 3, 15, 10, 0, 0, 0, time.UTC),
		Type:       transactions.TypeExpense,
		Amount:     500000,
		Currency:   "VND",
		JarCode:    "HuongThu",
		Note:       "fixed jar",
		Status:     transactions.StatusConfirmed,
	}, "llm classified wrong", "user")
	if err != nil {
		t.Fatalf("Correct() error = %v", err)
	}

	if updated.JarCode != "HuongThu" {
		t.Fatalf("expected updated jar code, got %q", updated.JarCode)
	}
	if len(audit.entries) != 1 {
		t.Fatalf("expected one audit entry, got %d", len(audit.entries))
	}
}

func TestUndoTransactionSetsReverted(t *testing.T) {
	repo := &fakeTransactionsRepository{
		items: []transactions.Transaction{{
			ID:         "TX-001",
			OccurredAt: time.Date(2026, 3, 15, 10, 0, 0, 0, time.UTC),
			Type:       transactions.TypeExpense,
			Amount:     500000,
			Currency:   "VND",
			Status:     transactions.StatusConfirmed,
		}},
	}
	audit := &fakeAuditLogger{}
	service := transactions.NewService(repo, audit, fakeIDGenerator{}, fakeClock{})

	updated, err := service.Undo(context.Background(), "TX-001", "mist entry", "user")
	if err != nil {
		t.Fatalf("Undo() error = %v", err)
	}

	if updated.Status != transactions.StatusReverted {
		t.Fatalf("expected reverted status, got %q", updated.Status)
	}
}

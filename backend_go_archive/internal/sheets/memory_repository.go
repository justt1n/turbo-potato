package sheets

import (
	"context"
	"fmt"
	"sync"

	"github.com/admin/turbo-potato/backend/internal/domain/transactions"
)

type MemoryTransactionRepository struct {
	mu    sync.RWMutex
	items []transactions.Transaction
}

func NewMemoryTransactionRepository() *MemoryTransactionRepository {
	return &MemoryTransactionRepository{
		items: make([]transactions.Transaction, 0),
	}
}

func (r *MemoryTransactionRepository) CreateTransaction(_ context.Context, tx transactions.Transaction) (transactions.Transaction, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.items = append(r.items, tx)
	return tx, nil
}

func (r *MemoryTransactionRepository) GetTransaction(_ context.Context, id string) (transactions.Transaction, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	for _, item := range r.items {
		if item.ID == id {
			return item, nil
		}
	}

	return transactions.Transaction{}, fmt.Errorf("transaction %s not found", id)
}

func (r *MemoryTransactionRepository) UpdateTransaction(_ context.Context, tx transactions.Transaction) (transactions.Transaction, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	for index, item := range r.items {
		if item.ID == tx.ID {
			r.items[index] = tx
			return tx, nil
		}
	}

	return transactions.Transaction{}, fmt.Errorf("transaction %s not found", tx.ID)
}

func (r *MemoryTransactionRepository) ListTransactions(_ context.Context) ([]transactions.Transaction, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	items := make([]transactions.Transaction, len(r.items))
	copy(items, r.items)
	return items, nil
}

type MemoryAuditLogger struct {
	mu      sync.Mutex
	entries []transactions.AuditEntry
}

func NewMemoryAuditLogger() *MemoryAuditLogger {
	return &MemoryAuditLogger{
		entries: make([]transactions.AuditEntry, 0),
	}
}

func (l *MemoryAuditLogger) Log(_ context.Context, entry transactions.AuditEntry) error {
	l.mu.Lock()
	defer l.mu.Unlock()
	l.entries = append(l.entries, entry)
	return nil
}

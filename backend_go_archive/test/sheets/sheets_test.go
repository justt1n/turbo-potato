package sheets_test

import (
	"context"
	"testing"
	"time"

	"github.com/admin/turbo-potato/backend/internal/domain/rules"
	"github.com/admin/turbo-potato/backend/internal/domain/transactions"
	"github.com/admin/turbo-potato/backend/internal/sheets"
)

type fakeValuesClient struct {
	appended [][]interface{}
	rows     [][]interface{}
	updated  map[string][][]interface{}
}

func (f *fakeValuesClient) Append(_ context.Context, _ string, _ string, values [][]interface{}) error {
	f.appended = values
	return nil
}

func (f *fakeValuesClient) Get(_ context.Context, _ string, _ string) ([][]interface{}, error) {
	return f.rows, nil
}

func (f *fakeValuesClient) Update(_ context.Context, _ string, readRange string, values [][]interface{}) error {
	if f.updated == nil {
		f.updated = map[string][][]interface{}{}
	}
	f.updated[readRange] = values
	return nil
}

type fakeAdmin struct {
	titles []string
	added  []string
}

func (f *fakeAdmin) GetSheetTitles(_ context.Context, _ string) ([]string, error) {
	return append([]string(nil), f.titles...), nil
}

func (f *fakeAdmin) AddSheets(_ context.Context, _ string, titles []string) error {
	f.added = append(f.added, titles...)
	return nil
}

func TestGoogleTransactionRepositoryCreateTransaction(t *testing.T) {
	client := &fakeValuesClient{}
	repo := sheets.NewGoogleTransactionRepository(client, "sheet-id")

	tx := transactions.Transaction{
		ID:         "TX-1",
		OccurredAt: time.Date(2026, 3, 15, 10, 0, 0, 0, time.UTC),
		Type:       transactions.TypeExpense,
		Amount:     500000,
		Currency:   "VND",
		CreatedAt:  time.Date(2026, 3, 15, 10, 0, 0, 0, time.UTC),
		UpdatedAt:  time.Date(2026, 3, 15, 10, 0, 0, 0, time.UTC),
	}

	if _, err := repo.CreateTransaction(context.Background(), tx); err != nil {
		t.Fatalf("CreateTransaction() error = %v", err)
	}
}

func TestSpreadsheetBootstrapperAddsMissingSheetsAndHeaders(t *testing.T) {
	admin := &fakeAdmin{titles: []string{"Transactions"}}
	values := &fakeValuesClient{}
	bootstrapper := sheets.NewSpreadsheetBootstrapper(admin, values, "sheet-id")

	if err := bootstrapper.Bootstrap(context.Background()); err != nil {
		t.Fatalf("Bootstrap() error = %v", err)
	}

	if len(admin.added) == 0 {
		t.Fatal("expected missing sheets to be added")
	}
}

func TestMemoryRulesRepositoryCreateFixedCostRule(t *testing.T) {
	repo := sheets.NewMemoryRulesRepository()
	_, err := repo.CreateFixedCostRule(context.Background(), rules.FixedCostRule{
		Name:           "Rent",
		ExpectedAmount: 5000000,
		WindowStartDay: 1,
		WindowEndDay:   5,
		IsActive:       true,
	})
	if err != nil {
		t.Fatalf("CreateFixedCostRule() error = %v", err)
	}
}

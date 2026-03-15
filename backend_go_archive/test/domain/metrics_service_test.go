package domain_test

import (
	"context"
	"testing"
	"time"

	"github.com/admin/turbo-potato/backend/internal/domain/goals"
	"github.com/admin/turbo-potato/backend/internal/domain/metrics"
	"github.com/admin/turbo-potato/backend/internal/domain/rules"
	"github.com/admin/turbo-potato/backend/internal/domain/transactions"
)

type fakeMetricsTransactions struct {
	items []transactions.Transaction
}

func (r *fakeMetricsTransactions) List(_ context.Context) ([]transactions.Transaction, error) {
	return append([]transactions.Transaction(nil), r.items...), nil
}

type fakeMetricsGoals struct {
	items []goals.Goal
}

func (r *fakeMetricsGoals) List(_ context.Context) ([]goals.Goal, error) {
	return append([]goals.Goal(nil), r.items...), nil
}

type fakeMetricsRules struct {
	items []rules.FixedCostRule
}

func (r *fakeMetricsRules) ListFixedCostRules(_ context.Context) ([]rules.FixedCostRule, error) {
	return append([]rules.FixedCostRule(nil), r.items...), nil
}

type metricsClock struct{}

func (metricsClock) Now() time.Time {
	return time.Date(2026, 3, 15, 10, 0, 0, 0, time.UTC)
}

func TestMetricsSummary(t *testing.T) {
	service := metrics.NewService(
		&fakeMetricsTransactions{
			items: []transactions.Transaction{
				{
					ID:         "TX-1",
					OccurredAt: time.Date(2026, 3, 15, 9, 0, 0, 0, time.UTC),
					Type:       transactions.TypeExpense,
					Amount:     300000,
					Currency:   "VND",
					IsFixed:    false,
					Status:     transactions.StatusConfirmed,
				},
				{
					ID:         "TX-2",
					OccurredAt: time.Date(2026, 3, 10, 9, 0, 0, 0, time.UTC),
					Type:       transactions.TypeIncome,
					Amount:     20000000,
					Currency:   "VND",
					Status:     transactions.StatusConfirmed,
				},
				{
					ID:         "TX-3",
					OccurredAt: time.Date(2026, 3, 12, 9, 0, 0, 0, time.UTC),
					Type:       transactions.TypeTransfer,
					Amount:     5000000,
					Currency:   "VND",
					GoalName:   "Mua xe SH",
					Status:     transactions.StatusConfirmed,
				},
			},
		},
		&fakeMetricsGoals{
			items: []goals.Goal{
				{
					Name:         "Mua xe SH",
					TargetAmount: 100000000,
					StartDate:    time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC),
					Status:       goals.StatusActive,
				},
			},
		},
		&fakeMetricsRules{
			items: []rules.FixedCostRule{
				{
					Name:           "Rent",
					ExpectedAmount: 5000000,
					WindowStartDay: 1,
					WindowEndDay:   5,
					IsActive:       true,
				},
			},
		},
		metricsClock{},
	)

	summary, err := service.Summary(context.Background())
	if err != nil {
		t.Fatalf("Summary() error = %v", err)
	}

	if summary.STS.Label == "" {
		t.Fatal("expected STS metric")
	}
	if len(summary.Baselines) != 3 {
		t.Fatalf("expected 3 baseline series, got %d", len(summary.Baselines))
	}
	if summary.OperatingPosture.Status == "" {
		t.Fatal("expected operating posture status")
	}
}

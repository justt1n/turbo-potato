package domain_test

import (
	"context"
	"testing"
	"time"

	"github.com/admin/turbo-potato/backend/internal/ai"
	"github.com/admin/turbo-potato/backend/internal/domain/goals"
	"github.com/admin/turbo-potato/backend/internal/domain/metrics"
	"github.com/admin/turbo-potato/backend/internal/domain/reports"
	"github.com/admin/turbo-potato/backend/internal/domain/rules"
	"github.com/admin/turbo-potato/backend/internal/domain/transactions"
)

type fakeReportsRepo struct {
	items []reports.Report
}

func (r *fakeReportsRepo) Save(_ context.Context, report reports.Report) (reports.Report, error) {
	r.items = append(r.items, report)
	return report, nil
}

func (r *fakeReportsRepo) FindByKindAndPeriod(_ context.Context, kind reports.Kind, periodKey string) (*reports.Report, error) {
	for index := len(r.items) - 1; index >= 0; index-- {
		if r.items[index].Kind == kind && r.items[index].PeriodKey == periodKey {
			item := r.items[index]
			return &item, nil
		}
	}
	return nil, nil
}

func (r *fakeReportsRepo) LatestByKind(_ context.Context, kind reports.Kind) (*reports.Report, error) {
	for index := len(r.items) - 1; index >= 0; index-- {
		if r.items[index].Kind == kind {
			item := r.items[index]
			return &item, nil
		}
	}
	return nil, nil
}

type fakeReportsMetrics struct {
	summary metrics.Summary
}

func (r fakeReportsMetrics) Summary(context.Context) (metrics.Summary, error) {
	return r.summary, nil
}

type fakeReportsClock struct {
	now time.Time
}

func (c fakeReportsClock) Now() time.Time {
	return c.now
}

func TestReportsDashboardAutoGeneratesDaily(t *testing.T) {
	repo := &fakeReportsRepo{}
	service := reports.NewService(
		repo,
		fakeReportsMetrics{summary: metrics.Summary{
			STS:      metrics.MetricValue{Value: "450k VND", Status: "healthy"},
			Anomaly:  metrics.MetricValue{Value: "0.32", Status: "healthy"},
			GoalPace: metrics.MetricValue{Value: "40%", Status: "warning"},
			OperatingPosture: metrics.OperatingPosture{
				Status: "watch",
			},
		}},
		&fakeMetricsTransactions{items: []transactions.Transaction{
			{ID: "TX-1", Type: transactions.TypeExpense, Amount: 250000, Status: transactions.StatusConfirmed, OccurredAt: time.Date(2026, 3, 16, 8, 0, 0, 0, time.UTC)},
		}},
		&fakeMetricsGoals{items: []goals.Goal{{Name: "Emergency", Status: goals.StatusActive}}},
		&fakeMetricsRules{items: []rules.FixedCostRule{{Name: "Rent", IsActive: true}}},
		ai.NoopClient{},
		fakeReportsClock{now: time.Date(2026, 3, 16, 10, 0, 0, 0, time.UTC)},
		time.UTC,
		"test-model",
		"daily prompt",
		"monthly prompt",
		"daily-prompt",
		"monthly-prompt",
	)

	snapshot, err := service.Dashboard(context.Background())
	if err != nil {
		t.Fatalf("Dashboard() error = %v", err)
	}

	if snapshot.Daily.Kind != reports.KindDaily {
		t.Fatalf("expected daily report, got %q", snapshot.Daily.Kind)
	}
	if snapshot.Daily.PeriodKey != "2026-03-16" {
		t.Fatalf("expected daily period key, got %q", snapshot.Daily.PeriodKey)
	}
	if len(repo.items) != 1 {
		t.Fatalf("expected 1 saved report, got %d", len(repo.items))
	}
}

func TestReportsDashboardAutoGeneratesMonthlyOnFirstDay(t *testing.T) {
	repo := &fakeReportsRepo{}
	service := reports.NewService(
		repo,
		fakeReportsMetrics{summary: metrics.Summary{
			STS:              metrics.MetricValue{Value: "450k VND", Status: "healthy"},
			Anomaly:          metrics.MetricValue{Value: "0.32", Status: "healthy"},
			GoalPace:         metrics.MetricValue{Value: "40%", Status: "warning"},
			OperatingPosture: metrics.OperatingPosture{Status: "healthy"},
		}},
		&fakeMetricsTransactions{},
		&fakeMetricsGoals{},
		&fakeMetricsRules{},
		ai.NoopClient{},
		fakeReportsClock{now: time.Date(2026, 4, 1, 7, 0, 0, 0, time.UTC)},
		time.UTC,
		"test-model",
		"daily prompt",
		"monthly prompt",
		"daily-prompt",
		"monthly-prompt",
	)

	snapshot, err := service.Dashboard(context.Background())
	if err != nil {
		t.Fatalf("Dashboard() error = %v", err)
	}

	if snapshot.Monthly == nil {
		t.Fatal("expected monthly report on first day of month")
	}
	if snapshot.Monthly.PeriodKey != "2026-04" {
		t.Fatalf("expected monthly period key, got %q", snapshot.Monthly.PeriodKey)
	}
	if len(repo.items) != 2 {
		t.Fatalf("expected 2 saved reports, got %d", len(repo.items))
	}
}

func TestGenerateMonthlyForcesNewReport(t *testing.T) {
	repo := &fakeReportsRepo{
		items: []reports.Report{
			{ID: "RPT-OLD", Kind: reports.KindMonthly, PeriodKey: "2026-03"},
		},
	}
	service := reports.NewService(
		repo,
		fakeReportsMetrics{summary: metrics.Summary{
			STS:              metrics.MetricValue{Value: "500k VND"},
			Anomaly:          metrics.MetricValue{Value: "0.00"},
			GoalPace:         metrics.MetricValue{Value: "60%"},
			OperatingPosture: metrics.OperatingPosture{Status: "watch"},
		}},
		&fakeMetricsTransactions{},
		&fakeMetricsGoals{},
		&fakeMetricsRules{},
		ai.NoopClient{},
		fakeReportsClock{now: time.Date(2026, 3, 20, 10, 0, 0, 0, time.UTC)},
		time.UTC,
		"test-model",
		"daily prompt",
		"monthly prompt",
		"daily-prompt",
		"monthly-prompt",
	)

	report, err := service.GenerateMonthly(context.Background(), reports.GenerateInput{Trigger: "manual"})
	if err != nil {
		t.Fatalf("GenerateMonthly() error = %v", err)
	}

	if report.Kind != reports.KindMonthly {
		t.Fatalf("expected monthly report, got %q", report.Kind)
	}
	if len(repo.items) != 2 {
		t.Fatalf("expected 2 reports, got %d", len(repo.items))
	}
}

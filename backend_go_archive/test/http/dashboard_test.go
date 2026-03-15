package http_test

import (
	"context"
	"encoding/json"
	"net/http/httptest"
	"testing"

	"github.com/admin/turbo-potato/backend/internal/domain/metrics"
	"github.com/admin/turbo-potato/backend/internal/domain/reports"
	httptransport "github.com/admin/turbo-potato/backend/internal/http"
	"github.com/gofiber/fiber/v2"
)

type fakeDashboardMetricsService struct{}
type fakeDashboardReportsService struct{}

func (fakeDashboardMetricsService) Summary(context.Context) (metrics.Summary, error) {
	return metrics.Summary{
		STS: metrics.MetricValue{
			Label:    "STS Today",
			Value:    "268k",
			Caption:  "Daily spend allowance",
			Progress: 72,
			Status:   "healthy",
		},
	}, nil
}

func (fakeDashboardReportsService) Dashboard(context.Context) (reports.Snapshot, error) {
	return reports.Snapshot{}, nil
}

func (fakeDashboardReportsService) GenerateMonthly(context.Context, reports.GenerateInput) (reports.Report, error) {
	return reports.Report{}, nil
}

func TestDashboardSummaryEndpoint(t *testing.T) {
	app := fiber.New()
	httptransport.Register(app, &fakeTransactionService{}, &fakeGoalsService{}, &fakeRulesService{}, fakeDashboardMetricsService{}, fakeIngestionService{}, fakeDashboardReportsService{}, fakeBootstrapper{})

	req := httptest.NewRequest("GET", "/api/v1/dashboard/summary", nil)
	resp, err := app.Test(req)
	if err != nil {
		t.Fatalf("app.Test() error = %v", err)
	}

	if resp.StatusCode != fiber.StatusOK {
		t.Fatalf("expected %d, got %d", fiber.StatusOK, resp.StatusCode)
	}

	var payload metrics.Summary
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		t.Fatalf("Decode() error = %v", err)
	}

	if payload.STS.Label != "STS Today" {
		t.Fatalf("expected sts label, got %q", payload.STS.Label)
	}
}

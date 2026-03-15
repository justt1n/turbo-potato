package http_test

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/admin/turbo-potato/backend/internal/domain/goals"
	"github.com/admin/turbo-potato/backend/internal/domain/ingestion"
	"github.com/admin/turbo-potato/backend/internal/domain/metrics"
	"github.com/admin/turbo-potato/backend/internal/domain/reports"
	"github.com/admin/turbo-potato/backend/internal/domain/rules"
	"github.com/admin/turbo-potato/backend/internal/domain/transactions"
	httptransport "github.com/admin/turbo-potato/backend/internal/http"
	"github.com/gofiber/fiber/v2"
)

type fakeTransactionService struct{ items []transactions.Transaction }
type fakeGoalsService struct{ items []goals.Goal }
type fakeRulesService struct{ items []rules.FixedCostRule }
type fakeBootstrapper struct{}
type fakeMetricsService struct{}
type fakeIngestionService struct{}
type fakeReportsService struct{}

func (s *fakeTransactionService) Create(_ context.Context, input transactions.CreateInput) (transactions.Transaction, error) {
	item := transactions.Transaction{ID: "TX-100", Type: input.Type, Amount: input.Amount, Currency: input.Currency}
	s.items = append(s.items, item)
	return item, nil
}

func (s *fakeTransactionService) Correct(_ context.Context, id string, input transactions.UpdateInput, _, _ string) (transactions.Transaction, error) {
	item := transactions.Transaction{ID: id, Type: input.Type, Amount: input.Amount, Currency: input.Currency, Status: input.Status, JarCode: input.JarCode, Note: input.Note}
	return item, nil
}

func (s *fakeTransactionService) Undo(_ context.Context, id, _, _ string) (transactions.Transaction, error) {
	return transactions.Transaction{ID: id, Status: transactions.StatusReverted}, nil
}

func (s *fakeTransactionService) List(_ context.Context) ([]transactions.Transaction, error) {
	return s.items, nil
}

func (s *fakeGoalsService) Create(_ context.Context, input goals.CreateInput) (goals.Goal, error) {
	item := goals.Goal{Name: input.Name, TargetAmount: input.TargetAmount, StartDate: time.Now().UTC(), Status: input.Status}
	s.items = append(s.items, item)
	return item, nil
}

func (s *fakeGoalsService) List(_ context.Context) ([]goals.Goal, error) {
	return s.items, nil
}

func (s *fakeRulesService) CreateFixedCostRule(_ context.Context, input rules.CreateFixedCostRuleInput) (rules.FixedCostRule, error) {
	item := rules.FixedCostRule{Name: input.Name, ExpectedAmount: input.ExpectedAmount, WindowStartDay: input.WindowStartDay, WindowEndDay: input.WindowEndDay}
	s.items = append(s.items, item)
	return item, nil
}

func (s *fakeRulesService) ListFixedCostRules(_ context.Context) ([]rules.FixedCostRule, error) {
	return s.items, nil
}

func (fakeBootstrapper) Bootstrap(context.Context) error { return nil }
func (fakeMetricsService) Summary(context.Context) (metrics.Summary, error) {
	return metrics.Summary{}, nil
}
func (fakeIngestionService) IngestChat(_ context.Context, input ingestion.IngestInput) (ingestion.Result, error) {
	return ingestion.Result{
		TransactionID: "TX-DRAFT-1",
		Receipt: ingestion.ParsedReceipt{
			ID:            "RCPT-1",
			TransactionID: "TX-DRAFT-1",
			RawInput:      input.RawInput,
			PromptSource:  "test-prompt",
		},
	}, nil
}

func (fakeReportsService) Dashboard(context.Context) (reports.Snapshot, error) {
	return reports.Snapshot{
		Daily: reports.Report{
			ID:        "RPT-1",
			Kind:      reports.KindDaily,
			PeriodKey: "2026-03-16",
			Title:     "Daily financial status",
			Status:    "healthy",
		},
	}, nil
}

func (fakeReportsService) GenerateMonthly(context.Context, reports.GenerateInput) (reports.Report, error) {
	return reports.Report{
		ID:        "RPT-2",
		Kind:      reports.KindMonthly,
		PeriodKey: "2026-03",
		Title:     "Monthly financial status",
		Status:    "watch",
	}, nil
}

func TestCreateGoalEndpoint(t *testing.T) {
	app := fiber.New()
	httptransport.Register(app, &fakeTransactionService{}, &fakeGoalsService{}, &fakeRulesService{}, fakeMetricsService{}, fakeIngestionService{}, fakeReportsService{}, fakeBootstrapper{})

	body, _ := json.Marshal(map[string]any{"name": "Mua xe SH", "targetAmount": 100000000, "status": "active"})
	req := httptest.NewRequest("POST", "/api/v1/goals", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	resp, err := app.Test(req)
	if err != nil {
		t.Fatalf("app.Test() error = %v", err)
	}
	if resp.StatusCode != fiber.StatusCreated {
		t.Fatalf("expected %d, got %d", fiber.StatusCreated, resp.StatusCode)
	}
}

func TestBootstrapEndpoint(t *testing.T) {
	app := fiber.New()
	httptransport.Register(app, &fakeTransactionService{}, &fakeGoalsService{}, &fakeRulesService{}, fakeMetricsService{}, fakeIngestionService{}, fakeReportsService{}, fakeBootstrapper{})

	req := httptest.NewRequest("POST", "/api/v1/admin/bootstrap", nil)
	resp, err := app.Test(req)
	if err != nil {
		t.Fatalf("app.Test() error = %v", err)
	}
	if resp.StatusCode != fiber.StatusOK {
		t.Fatalf("expected %d, got %d", fiber.StatusOK, resp.StatusCode)
	}
}

func TestCorrectTransactionEndpoint(t *testing.T) {
	app := fiber.New()
	httptransport.Register(app, &fakeTransactionService{}, &fakeGoalsService{}, &fakeRulesService{}, fakeMetricsService{}, fakeIngestionService{}, fakeReportsService{}, fakeBootstrapper{})

	body, _ := json.Marshal(map[string]any{
		"type":     "OUT",
		"amount":   200000,
		"currency": "VND",
		"jarCode":  "HuongThu",
		"note":     "corrected",
		"status":   "confirmed",
		"reason":   "wrong category",
		"actor":    "user",
	})
	req := httptest.NewRequest("POST", "/api/v1/transactions/TX-100/correct", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	resp, err := app.Test(req)
	if err != nil {
		t.Fatalf("app.Test() error = %v", err)
	}
	if resp.StatusCode != fiber.StatusOK {
		t.Fatalf("expected %d, got %d", fiber.StatusOK, resp.StatusCode)
	}
}

func TestUndoTransactionEndpoint(t *testing.T) {
	app := fiber.New()
	httptransport.Register(app, &fakeTransactionService{}, &fakeGoalsService{}, &fakeRulesService{}, fakeMetricsService{}, fakeIngestionService{}, fakeReportsService{}, fakeBootstrapper{})

	body, _ := json.Marshal(map[string]any{
		"reason": "mist entry",
		"actor":  "user",
	})
	req := httptest.NewRequest("POST", "/api/v1/transactions/TX-100/undo", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	resp, err := app.Test(req)
	if err != nil {
		t.Fatalf("app.Test() error = %v", err)
	}
	if resp.StatusCode != fiber.StatusOK {
		t.Fatalf("expected %d, got %d", fiber.StatusOK, resp.StatusCode)
	}
}

func TestIngestChatEndpoint(t *testing.T) {
	app := fiber.New()
	httptransport.Register(app, &fakeTransactionService{}, &fakeGoalsService{}, &fakeRulesService{}, fakeMetricsService{}, fakeIngestionService{}, fakeReportsService{}, fakeBootstrapper{})

	body, _ := json.Marshal(map[string]any{
		"rawInput": "di nhau voi phong 500k #team",
		"source":   "chat",
		"actor":    "user",
	})
	req := httptest.NewRequest("POST", "/api/v1/ingestion/chat", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	resp, err := app.Test(req)
	if err != nil {
		t.Fatalf("app.Test() error = %v", err)
	}
	if resp.StatusCode != fiber.StatusCreated {
		t.Fatalf("expected %d, got %d", fiber.StatusCreated, resp.StatusCode)
	}
}

func TestDashboardReportsEndpoint(t *testing.T) {
	app := fiber.New()
	httptransport.Register(app, &fakeTransactionService{}, &fakeGoalsService{}, &fakeRulesService{}, fakeMetricsService{}, fakeIngestionService{}, fakeReportsService{}, fakeBootstrapper{})

	req := httptest.NewRequest("GET", "/api/v1/dashboard/reports", nil)
	resp, err := app.Test(req)
	if err != nil {
		t.Fatalf("app.Test() error = %v", err)
	}
	if resp.StatusCode != fiber.StatusOK {
		t.Fatalf("expected %d, got %d", fiber.StatusOK, resp.StatusCode)
	}
}

func TestGenerateMonthlyReportEndpoint(t *testing.T) {
	app := fiber.New()
	httptransport.Register(app, &fakeTransactionService{}, &fakeGoalsService{}, &fakeRulesService{}, fakeMetricsService{}, fakeIngestionService{}, fakeReportsService{}, fakeBootstrapper{})

	body, _ := json.Marshal(map[string]any{"trigger": "manual"})
	req := httptest.NewRequest("POST", "/api/v1/dashboard/reports/monthly", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	resp, err := app.Test(req)
	if err != nil {
		t.Fatalf("app.Test() error = %v", err)
	}
	if resp.StatusCode != fiber.StatusCreated {
		t.Fatalf("expected %d, got %d", fiber.StatusCreated, resp.StatusCode)
	}
}

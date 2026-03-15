package http

import (
	"context"
	"time"

	"github.com/admin/turbo-potato/backend/internal/domain/goals"
	"github.com/admin/turbo-potato/backend/internal/domain/ingestion"
	"github.com/admin/turbo-potato/backend/internal/domain/metrics"
	"github.com/admin/turbo-potato/backend/internal/domain/reports"
	"github.com/admin/turbo-potato/backend/internal/domain/rules"
	"github.com/admin/turbo-potato/backend/internal/domain/transactions"
	"github.com/gofiber/fiber/v2"
)

type transactionService interface {
	Create(ctx context.Context, input transactions.CreateInput) (transactions.Transaction, error)
	Correct(ctx context.Context, id string, input transactions.UpdateInput, reason, actor string) (transactions.Transaction, error)
	Undo(ctx context.Context, id, reason, actor string) (transactions.Transaction, error)
	List(ctx context.Context) ([]transactions.Transaction, error)
}

type goalsService interface {
	Create(ctx context.Context, input goals.CreateInput) (goals.Goal, error)
	List(ctx context.Context) ([]goals.Goal, error)
}

type fixedCostRulesService interface {
	CreateFixedCostRule(ctx context.Context, input rules.CreateFixedCostRuleInput) (rules.FixedCostRule, error)
	ListFixedCostRules(ctx context.Context) ([]rules.FixedCostRule, error)
}

type metricsService interface {
	Summary(ctx context.Context) (metrics.Summary, error)
}

type ingestionService interface {
	IngestChat(ctx context.Context, input ingestion.IngestInput) (ingestion.Result, error)
}

type reportsService interface {
	Dashboard(ctx context.Context) (reports.Snapshot, error)
	GenerateMonthly(ctx context.Context, input reports.GenerateInput) (reports.Report, error)
}

type transactionHandler struct {
	service      transactionService
	goals        goalsService
	rules        fixedCostRulesService
	metrics      metricsService
	ingestion    ingestionService
	reports      reportsService
	bootstrapper sheetsBootstrapper
}

type sheetsBootstrapper interface {
	Bootstrap(ctx context.Context) error
}

func Register(app *fiber.App, service transactionService, goals goalsService, rules fixedCostRulesService, metrics metricsService, ingestion ingestionService, reports reportsService, bootstrapper sheetsBootstrapper) {
	handler := transactionHandler{
		service:      service,
		goals:        goals,
		rules:        rules,
		metrics:      metrics,
		ingestion:    ingestion,
		reports:      reports,
		bootstrapper: bootstrapper,
	}

	api := app.Group("/api/v1")
	api.Get("/health", handler.health)
	api.Get("/dashboard/summary", handler.dashboardSummary)
	api.Get("/dashboard/reports", handler.dashboardReports)
	api.Post("/dashboard/reports/monthly", handler.generateMonthlyReport)
	api.Post("/ingestion/chat", handler.ingestChat)
	api.Get("/transactions", handler.listTransactions)
	api.Post("/transactions", handler.createTransaction)
	api.Post("/transactions/:id/correct", handler.correctTransaction)
	api.Post("/transactions/:id/undo", handler.undoTransaction)
	api.Get("/goals", handler.listGoals)
	api.Post("/goals", handler.createGoal)
	api.Get("/fixed-cost-rules", handler.listFixedCostRules)
	api.Post("/fixed-cost-rules", handler.createFixedCostRule)
	api.Post("/admin/bootstrap", handler.bootstrap)
}

func (h transactionHandler) health(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"status": "ok",
	})
}

type createTransactionRequest struct {
	OccurredAt string `json:"occurredAt"`
	Type       string `json:"type"`
	Amount     int64  `json:"amount"`
	Currency   string `json:"currency"`
	JarCode    string `json:"jarCode"`
	GoalName   string `json:"goalName"`
	Account    string `json:"accountName"`
	IsFixed    bool   `json:"isFixed"`
	Note       string `json:"note"`
	Source     string `json:"source"`
	Status     string `json:"status"`
}

func (h transactionHandler) createTransaction(c *fiber.Ctx) error {
	var request createTransactionRequest
	if err := c.BodyParser(&request); err != nil {
		return fiber.NewError(fiber.StatusBadRequest, "invalid request body")
	}

	var occurredAt time.Time
	if request.OccurredAt != "" {
		parsed, err := time.Parse(time.RFC3339, request.OccurredAt)
		if err != nil {
			return fiber.NewError(fiber.StatusBadRequest, "occurredAt must be RFC3339")
		}
		occurredAt = parsed
	}

	transaction, err := h.service.Create(c.UserContext(), transactions.CreateInput{
		OccurredAt: occurredAt,
		Type:       transactions.Type(request.Type),
		Amount:     request.Amount,
		Currency:   request.Currency,
		JarCode:    request.JarCode,
		GoalName:   request.GoalName,
		Account:    request.Account,
		IsFixed:    request.IsFixed,
		Note:       request.Note,
		Source:     request.Source,
		Status:     transactions.Status(request.Status),
	})
	if err != nil {
		return fiber.NewError(fiber.StatusBadRequest, err.Error())
	}

	return c.Status(fiber.StatusCreated).JSON(transaction)
}

func (h transactionHandler) listTransactions(c *fiber.Ctx) error {
	items, err := h.service.List(c.UserContext())
	if err != nil {
		return fiber.NewError(fiber.StatusInternalServerError, err.Error())
	}

	return c.JSON(fiber.Map{
		"items": items,
	})
}

func (h transactionHandler) bootstrap(c *fiber.Ctx) error {
	if err := h.bootstrapper.Bootstrap(c.UserContext()); err != nil {
		return fiber.NewError(fiber.StatusInternalServerError, err.Error())
	}

	return c.JSON(fiber.Map{
		"status": "bootstrapped",
	})
}

func (h transactionHandler) dashboardSummary(c *fiber.Ctx) error {
	summary, err := h.metrics.Summary(c.UserContext())
	if err != nil {
		return fiber.NewError(fiber.StatusInternalServerError, err.Error())
	}

	return c.JSON(summary)
}

func (h transactionHandler) dashboardReports(c *fiber.Ctx) error {
	snapshot, err := h.reports.Dashboard(c.UserContext())
	if err != nil {
		return fiber.NewError(fiber.StatusInternalServerError, err.Error())
	}

	return c.JSON(snapshot)
}

func (h transactionHandler) generateMonthlyReport(c *fiber.Ctx) error {
	var request generateMonthlyReportRequest
	if err := c.BodyParser(&request); err != nil && len(c.Body()) > 0 {
		return fiber.NewError(fiber.StatusBadRequest, "invalid request body")
	}

	report, err := h.reports.GenerateMonthly(c.UserContext(), reports.GenerateInput{
		Trigger: request.Trigger,
		Actor:   request.Actor,
	})
	if err != nil {
		return fiber.NewError(fiber.StatusInternalServerError, err.Error())
	}

	return c.Status(fiber.StatusCreated).JSON(report)
}

type createGoalRequest struct {
	Name         string `json:"name"`
	TargetAmount int64  `json:"targetAmount"`
	StartDate    string `json:"startDate"`
	TargetDate   string `json:"targetDate"`
	Status       string `json:"status"`
}

type correctTransactionRequest struct {
	OccurredAt string `json:"occurredAt"`
	Type       string `json:"type"`
	Amount     int64  `json:"amount"`
	Currency   string `json:"currency"`
	JarCode    string `json:"jarCode"`
	GoalName   string `json:"goalName"`
	Account    string `json:"accountName"`
	IsFixed    bool   `json:"isFixed"`
	Note       string `json:"note"`
	Status     string `json:"status"`
	Reason     string `json:"reason"`
	Actor      string `json:"actor"`
}

type undoTransactionRequest struct {
	Reason string `json:"reason"`
	Actor  string `json:"actor"`
}

type ingestChatRequest struct {
	RawInput string `json:"rawInput"`
	Source   string `json:"source"`
	Actor    string `json:"actor"`
}

type generateMonthlyReportRequest struct {
	Trigger string `json:"trigger"`
	Actor   string `json:"actor"`
}

func (h transactionHandler) createGoal(c *fiber.Ctx) error {
	var request createGoalRequest
	if err := c.BodyParser(&request); err != nil {
		return fiber.NewError(fiber.StatusBadRequest, "invalid request body")
	}

	var startDate time.Time
	if request.StartDate != "" {
		parsed, err := time.Parse(time.RFC3339, request.StartDate)
		if err != nil {
			return fiber.NewError(fiber.StatusBadRequest, "startDate must be RFC3339")
		}
		startDate = parsed
	}

	var targetDate time.Time
	if request.TargetDate != "" {
		parsed, err := time.Parse(time.RFC3339, request.TargetDate)
		if err != nil {
			return fiber.NewError(fiber.StatusBadRequest, "targetDate must be RFC3339")
		}
		targetDate = parsed
	}

	item, err := h.goals.Create(c.UserContext(), goals.CreateInput{
		Name:         request.Name,
		TargetAmount: request.TargetAmount,
		StartDate:    startDate,
		TargetDate:   targetDate,
		Status:       goals.Status(request.Status),
	})
	if err != nil {
		return fiber.NewError(fiber.StatusBadRequest, err.Error())
	}

	return c.Status(fiber.StatusCreated).JSON(item)
}

func (h transactionHandler) listGoals(c *fiber.Ctx) error {
	items, err := h.goals.List(c.UserContext())
	if err != nil {
		return fiber.NewError(fiber.StatusInternalServerError, err.Error())
	}

	return c.JSON(fiber.Map{"items": items})
}

type createFixedCostRuleRequest struct {
	Name           string `json:"name"`
	ExpectedAmount int64  `json:"expectedAmount"`
	WindowStartDay int    `json:"windowStartDay"`
	WindowEndDay   int    `json:"windowEndDay"`
	LinkedJarCode  string `json:"linkedJarCode"`
	IsActive       bool   `json:"isActive"`
}

func (h transactionHandler) createFixedCostRule(c *fiber.Ctx) error {
	var request createFixedCostRuleRequest
	if err := c.BodyParser(&request); err != nil {
		return fiber.NewError(fiber.StatusBadRequest, "invalid request body")
	}

	item, err := h.rules.CreateFixedCostRule(c.UserContext(), rules.CreateFixedCostRuleInput{
		Name:           request.Name,
		ExpectedAmount: request.ExpectedAmount,
		WindowStartDay: request.WindowStartDay,
		WindowEndDay:   request.WindowEndDay,
		LinkedJarCode:  request.LinkedJarCode,
		IsActive:       request.IsActive,
	})
	if err != nil {
		return fiber.NewError(fiber.StatusBadRequest, err.Error())
	}

	return c.Status(fiber.StatusCreated).JSON(item)
}

func (h transactionHandler) listFixedCostRules(c *fiber.Ctx) error {
	items, err := h.rules.ListFixedCostRules(c.UserContext())
	if err != nil {
		return fiber.NewError(fiber.StatusInternalServerError, err.Error())
	}

	return c.JSON(fiber.Map{"items": items})
}

func (h transactionHandler) ingestChat(c *fiber.Ctx) error {
	var request ingestChatRequest
	if err := c.BodyParser(&request); err != nil {
		return fiber.NewError(fiber.StatusBadRequest, "invalid request body")
	}

	result, err := h.ingestion.IngestChat(c.UserContext(), ingestion.IngestInput{
		RawInput: request.RawInput,
		Source:   request.Source,
		Actor:    request.Actor,
	})
	if err != nil {
		return fiber.NewError(fiber.StatusBadRequest, err.Error())
	}

	return c.Status(fiber.StatusCreated).JSON(result)
}

func (h transactionHandler) correctTransaction(c *fiber.Ctx) error {
	var request correctTransactionRequest
	if err := c.BodyParser(&request); err != nil {
		return fiber.NewError(fiber.StatusBadRequest, "invalid request body")
	}

	var occurredAt time.Time
	if request.OccurredAt != "" {
		parsed, err := time.Parse(time.RFC3339, request.OccurredAt)
		if err != nil {
			return fiber.NewError(fiber.StatusBadRequest, "occurredAt must be RFC3339")
		}
		occurredAt = parsed
	}

	item, err := h.service.Correct(c.UserContext(), c.Params("id"), transactions.UpdateInput{
		OccurredAt: occurredAt,
		Type:       transactions.Type(request.Type),
		Amount:     request.Amount,
		Currency:   request.Currency,
		JarCode:    request.JarCode,
		GoalName:   request.GoalName,
		Account:    request.Account,
		IsFixed:    request.IsFixed,
		Note:       request.Note,
		Status:     transactions.Status(request.Status),
	}, request.Reason, request.Actor)
	if err != nil {
		return fiber.NewError(fiber.StatusBadRequest, err.Error())
	}

	return c.JSON(item)
}

func (h transactionHandler) undoTransaction(c *fiber.Ctx) error {
	var request undoTransactionRequest
	if err := c.BodyParser(&request); err != nil {
		return fiber.NewError(fiber.StatusBadRequest, "invalid request body")
	}

	item, err := h.service.Undo(c.UserContext(), c.Params("id"), request.Reason, request.Actor)
	if err != nil {
		return fiber.NewError(fiber.StatusBadRequest, err.Error())
	}

	return c.JSON(item)
}

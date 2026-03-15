package app

import (
	"context"
	"fmt"
	"time"

	"github.com/admin/turbo-potato/backend/internal/ai"
	"github.com/admin/turbo-potato/backend/internal/config"
	"github.com/admin/turbo-potato/backend/internal/domain/goals"
	"github.com/admin/turbo-potato/backend/internal/domain/ingestion"
	"github.com/admin/turbo-potato/backend/internal/domain/metrics"
	"github.com/admin/turbo-potato/backend/internal/domain/reports"
	"github.com/admin/turbo-potato/backend/internal/domain/rules"
	"github.com/admin/turbo-potato/backend/internal/domain/transactions"
	httptransport "github.com/admin/turbo-potato/backend/internal/http"
	"github.com/admin/turbo-potato/backend/internal/sheets"
	"github.com/gofiber/fiber/v2"
)

type App struct {
	fiber        *fiber.App
	port         string
	bootstrapper sheets.Bootstrapper
}

func New(cfg config.Config) (*App, error) {
	deps, err := newSheetsDependencies(context.Background(), cfg)
	if err != nil {
		return nil, err
	}

	txService := transactions.NewService(deps.repo, deps.audit, &transactionIDGenerator{}, systemClock{})
	goalsService := goals.NewService(deps.goalsRepo)
	rulesService := rules.NewService(deps.rulesRepo)
	metricsService := metrics.NewService(txService, goalsService, rulesService, systemClock{})
	location := loadLocation(cfg.App.Timezone)
	aiClient := ai.NewClient(cfg)
	ingestionService := ingestion.NewService(
		txService,
		deps.receiptsRepo,
		aiClient,
		systemClock{},
		cfg.AI.Model,
		cfg.AI.Prompt,
		promptSource(cfg),
	)
	reportService := reports.NewService(
		deps.reportsRepo,
		metricsService,
		txService,
		goalsService,
		rulesService,
		aiClient,
		systemClock{},
		location,
		cfg.AI.Model,
		cfg.AI.DailyReportPrompt,
		cfg.AI.MonthlyReportPrompt,
		reportPromptSource(cfg, reports.KindDaily),
		reportPromptSource(cfg, reports.KindMonthly),
	)

	server := fiber.New()
	httptransport.Register(server, txService, goalsService, rulesService, metricsService, ingestionService, reportService, deps.bootstrapper)

	return &App{
		fiber:        server,
		port:         cfg.App.Port,
		bootstrapper: deps.bootstrapper,
	}, nil
}

func (a *App) Listen() error {
	if err := a.bootstrapper.Bootstrap(context.Background()); err != nil {
		return fmt.Errorf("bootstrap spreadsheet: %w", err)
	}

	return a.fiber.Listen(fmt.Sprintf(":%s", a.port))
}

type sheetsDependencies struct {
	repo         transactions.Repository
	audit        transactions.AuditLogger
	receiptsRepo ingestion.ReceiptRepository
	reportsRepo  reports.Repository
	goalsRepo    goals.Repository
	rulesRepo    rules.Repository
	bootstrapper sheets.Bootstrapper
}

func newSheetsDependencies(ctx context.Context, cfg config.Config) (sheetsDependencies, error) {
	if !cfg.UseGoogleSheets() {
		return sheetsDependencies{
			repo:         sheets.NewMemoryTransactionRepository(),
			audit:        sheets.NewMemoryAuditLogger(),
			receiptsRepo: sheets.NewMemoryParsedReceiptsRepository(),
			reportsRepo:  sheets.NewMemoryReportsRepository(),
			goalsRepo:    sheets.NewMemoryGoalsRepository(),
			rulesRepo:    sheets.NewMemoryRulesRepository(),
			bootstrapper: sheets.NewNoopBootstrapper(),
		}, nil
	}

	client, err := sheets.NewGoogleValuesClient(ctx, cfg)
	if err != nil {
		return sheetsDependencies{}, fmt.Errorf("create google sheets client: %w", err)
	}

	return sheetsDependencies{
		repo:         sheets.NewGoogleTransactionRepository(client, cfg.Sheets.SpreadsheetID),
		audit:        sheets.NewGoogleAuditLogger(client, cfg.Sheets.SpreadsheetID),
		receiptsRepo: sheets.NewGoogleParsedReceiptsRepository(client, cfg.Sheets.SpreadsheetID),
		reportsRepo:  sheets.NewGoogleReportsRepository(client, cfg.Sheets.SpreadsheetID),
		goalsRepo:    sheets.NewGoogleGoalsRepository(client, cfg.Sheets.SpreadsheetID),
		rulesRepo:    sheets.NewGoogleRulesRepository(client, cfg.Sheets.SpreadsheetID),
		bootstrapper: sheets.NewSpreadsheetBootstrapper(client, client, cfg.Sheets.SpreadsheetID),
	}, nil
}

func promptSource(cfg config.Config) string {
	switch {
	case cfg.AI.PromptFile != "":
		return cfg.AI.PromptFile
	case cfg.AI.Prompt != "":
		return "inline-config"
	default:
		return "default"
	}
}

func reportPromptSource(cfg config.Config, kind reports.Kind) string {
	switch kind {
	case reports.KindMonthly:
		switch {
		case cfg.AI.MonthlyReportPromptFile != "":
			return cfg.AI.MonthlyReportPromptFile
		case cfg.AI.MonthlyReportPrompt != "":
			return "inline-config"
		default:
			return "default"
		}
	default:
		switch {
		case cfg.AI.DailyReportPromptFile != "":
			return cfg.AI.DailyReportPromptFile
		case cfg.AI.DailyReportPrompt != "":
			return "inline-config"
		default:
			return "default"
		}
	}
}

func loadLocation(name string) *time.Location {
	if name == "" {
		return time.UTC
	}

	location, err := time.LoadLocation(name)
	if err != nil {
		return time.UTC
	}

	return location
}

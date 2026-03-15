package reports

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/admin/turbo-potato/backend/internal/ai"
	"github.com/admin/turbo-potato/backend/internal/domain/goals"
	"github.com/admin/turbo-potato/backend/internal/domain/metrics"
	"github.com/admin/turbo-potato/backend/internal/domain/rules"
	"github.com/admin/turbo-potato/backend/internal/domain/transactions"
)

type Repository interface {
	Save(ctx context.Context, report Report) (Report, error)
	FindByKindAndPeriod(ctx context.Context, kind Kind, periodKey string) (*Report, error)
	LatestByKind(ctx context.Context, kind Kind) (*Report, error)
}

type MetricsReader interface {
	Summary(ctx context.Context) (metrics.Summary, error)
}

type TransactionsReader interface {
	List(ctx context.Context) ([]transactions.Transaction, error)
}

type GoalsReader interface {
	List(ctx context.Context) ([]goals.Goal, error)
}

type RulesReader interface {
	ListFixedCostRules(ctx context.Context) ([]rules.FixedCostRule, error)
}

type Clock interface {
	Now() time.Time
}

type Service struct {
	repo                Repository
	metrics             MetricsReader
	transactions        TransactionsReader
	goals               GoalsReader
	rules               RulesReader
	aiClient            ai.Client
	clock               Clock
	location            *time.Location
	model               string
	dailyPrompt         string
	monthlyPrompt       string
	dailyPromptSource   string
	monthlyPromptSource string
}

func NewService(
	repo Repository,
	metrics MetricsReader,
	transactions TransactionsReader,
	goals GoalsReader,
	rules RulesReader,
	aiClient ai.Client,
	clock Clock,
	location *time.Location,
	model, dailyPrompt, monthlyPrompt, dailyPromptSource, monthlyPromptSource string,
) *Service {
	if location == nil {
		location = time.UTC
	}

	return &Service{
		repo:                repo,
		metrics:             metrics,
		transactions:        transactions,
		goals:               goals,
		rules:               rules,
		aiClient:            aiClient,
		clock:               clock,
		location:            location,
		model:               model,
		dailyPrompt:         dailyPrompt,
		monthlyPrompt:       monthlyPrompt,
		dailyPromptSource:   dailyPromptSource,
		monthlyPromptSource: monthlyPromptSource,
	}
}

func (s *Service) Dashboard(ctx context.Context) (Snapshot, error) {
	now := s.clock.Now().In(s.location)

	daily, err := s.ensure(ctx, KindDaily, now, "auto-daily")
	if err != nil {
		return Snapshot{}, err
	}

	var monthly *Report
	if now.Day() == 1 {
		currentMonthly, err := s.ensure(ctx, KindMonthly, now, "auto-monthly")
		if err != nil {
			return Snapshot{}, err
		}
		monthly = &currentMonthly
	} else {
		monthly, err = s.repo.LatestByKind(ctx, KindMonthly)
		if err != nil {
			return Snapshot{}, err
		}
	}

	return Snapshot{
		Daily:   daily,
		Monthly: monthly,
	}, nil
}

func (s *Service) GenerateMonthly(ctx context.Context, input GenerateInput) (Report, error) {
	trigger := strings.TrimSpace(input.Trigger)
	if trigger == "" {
		trigger = "manual-monthly"
	}

	return s.generate(ctx, KindMonthly, s.clock.Now().In(s.location), trigger, true)
}

func (s *Service) ensure(ctx context.Context, kind Kind, now time.Time, trigger string) (Report, error) {
	return s.generate(ctx, kind, now, trigger, false)
}

func (s *Service) generate(ctx context.Context, kind Kind, now time.Time, trigger string, force bool) (Report, error) {
	periodKey := periodKey(kind, now)
	if !force {
		existing, err := s.repo.FindByKindAndPeriod(ctx, kind, periodKey)
		if err != nil {
			return Report{}, err
		}
		if existing != nil {
			return *existing, nil
		}
	}

	summary, err := s.metrics.Summary(ctx)
	if err != nil {
		return Report{}, err
	}

	allTransactions, err := s.transactions.List(ctx)
	if err != nil {
		return Report{}, err
	}

	allGoals, err := s.goals.List(ctx)
	if err != nil {
		return Report{}, err
	}

	allRules, err := s.rules.ListFixedCostRules(ctx)
	if err != nil {
		return Report{}, err
	}

	financialSnapshot := buildFinancialSnapshot(now, allTransactions, allGoals, allRules, summary)
	payloadBytes, _ := json.MarshalIndent(financialSnapshot, "", "  ")

	promptTemplate, promptSource := s.promptConfig(kind)
	prompt := renderPrompt(promptTemplate, kind, periodKey, now, summary, string(payloadBytes))

	report, generationErr := s.generateNarrative(ctx, kind, trigger, periodKey, now, prompt, promptSource, financialSnapshot)
	if generationErr != nil {
		return Report{}, generationErr
	}

	return s.repo.Save(ctx, report)
}

func (s *Service) generateNarrative(
	ctx context.Context,
	kind Kind,
	trigger, periodKey string,
	now time.Time,
	prompt, promptSource string,
	financialSnapshot reportContext,
) (Report, error) {
	output, err := s.aiClient.Complete(ctx, ai.CompletionInput{
		Model:  s.model,
		Prompt: prompt,
	})
	if err == nil {
		if parsed, parseErr := parseGeneratedReport(output.Text); parseErr == nil {
			parsed.ID = fmt.Sprintf("RPT-%d", now.UTC().UnixNano())
			parsed.Kind = kind
			parsed.PeriodKey = periodKey
			parsed.Model = firstNonEmpty(output.Model, s.model, "configurable-analyst")
			parsed.PromptSource = firstNonEmpty(promptSource, "config-default")
			parsed.Trigger = trigger
			parsed.CreatedAt = now.UTC()
			return parsed, nil
		}
	}

	return fallbackReport(kind, periodKey, trigger, now, promptSource, firstNonEmpty(s.model, "fallback-analyst"), financialSnapshot), nil
}

func (s *Service) promptConfig(kind Kind) (string, string) {
	switch kind {
	case KindMonthly:
		return s.monthlyPrompt, firstNonEmpty(s.monthlyPromptSource, "default")
	default:
		return s.dailyPrompt, firstNonEmpty(s.dailyPromptSource, "default")
	}
}

type reportContext struct {
	RangeLabel             string          `json:"rangeLabel"`
	TodayExpense           int64           `json:"todayExpense"`
	MonthExpense           int64           `json:"monthExpense"`
	MonthIncome            int64           `json:"monthIncome"`
	MonthTransfers         int64           `json:"monthTransfers"`
	ConfirmedExpensesCount int             `json:"confirmedExpensesCount"`
	DraftCount             int             `json:"draftCount"`
	RevertedCount          int             `json:"revertedCount"`
	ActiveGoals            []string        `json:"activeGoals"`
	ActiveFixedRules       int             `json:"activeFixedRules"`
	Metrics                metrics.Summary `json:"metrics"`
}

func buildFinancialSnapshot(now time.Time, items []transactions.Transaction, goalsList []goals.Goal, rulesList []rules.FixedCostRule, summary metrics.Summary) reportContext {
	locNow := now.UTC()
	snapshot := reportContext{
		RangeLabel:       now.Format("02 Jan 2006"),
		ActiveGoals:      make([]string, 0),
		ActiveFixedRules: 0,
		Metrics:          summary,
	}

	for _, goal := range goalsList {
		if goal.Status == goals.StatusActive {
			snapshot.ActiveGoals = append(snapshot.ActiveGoals, goal.Name)
		}
	}

	for _, rule := range rulesList {
		if rule.IsActive {
			snapshot.ActiveFixedRules++
		}
	}

	for _, item := range items {
		if item.Status == transactions.StatusReverted {
			snapshot.RevertedCount++
			continue
		}
		if item.Status == transactions.StatusDraft {
			snapshot.DraftCount++
		}
		if item.Type == transactions.TypeExpense && sameDay(item.OccurredAt, locNow) {
			snapshot.TodayExpense += item.Amount
		}
		if item.OccurredAt.Year() != locNow.Year() || item.OccurredAt.Month() != locNow.Month() {
			continue
		}
		switch item.Type {
		case transactions.TypeExpense:
			snapshot.MonthExpense += item.Amount
			if item.Status == transactions.StatusConfirmed {
				snapshot.ConfirmedExpensesCount++
			}
		case transactions.TypeIncome:
			snapshot.MonthIncome += item.Amount
		case transactions.TypeTransfer:
			snapshot.MonthTransfers += item.Amount
		}
	}

	return snapshot
}

func renderPrompt(template string, kind Kind, periodKey string, now time.Time, summary metrics.Summary, snapshotJSON string) string {
	summaryJSON, _ := json.MarshalIndent(summary, "", "  ")

	replacer := strings.NewReplacer(
		"{{kind}}", string(kind),
		"{{period_key}}", periodKey,
		"{{generated_at}}", now.Format(time.RFC3339),
		"{{summary_json}}", string(summaryJSON),
		"{{snapshot_json}}", snapshotJSON,
	)

	rendered := strings.TrimSpace(replacer.Replace(template))
	if rendered != "" {
		return rendered
	}

	return replacer.Replace(`You are a personal finance analyst.
Return strict JSON with keys: title, summary, body, verdict, status.
Kind: {{kind}}
Period: {{period_key}}
Generated at: {{generated_at}}
Metrics:
{{summary_json}}
Snapshot:
{{snapshot_json}}`)
}

func parseGeneratedReport(raw string) (Report, error) {
	var payload struct {
		Title   string `json:"title"`
		Summary string `json:"summary"`
		Body    string `json:"body"`
		Verdict string `json:"verdict"`
		Status  string `json:"status"`
	}

	if err := json.Unmarshal([]byte(raw), &payload); err != nil {
		return Report{}, err
	}
	if strings.TrimSpace(payload.Title) == "" || strings.TrimSpace(payload.Body) == "" {
		return Report{}, fmt.Errorf("report output missing title or body")
	}

	return Report{
		Title:   strings.TrimSpace(payload.Title),
		Summary: strings.TrimSpace(payload.Summary),
		Body:    strings.TrimSpace(payload.Body),
		Verdict: strings.TrimSpace(payload.Verdict),
		Status:  firstNonEmpty(strings.TrimSpace(payload.Status), "watch"),
	}, nil
}

func fallbackReport(kind Kind, periodKey, trigger string, now time.Time, promptSource, model string, snapshot reportContext) Report {
	status := snapshot.Metrics.OperatingPosture.Status
	titlePrefix := "Daily"
	rangeLabel := now.Format("02 Jan 2006")
	if kind == KindMonthly {
		titlePrefix = "Monthly"
		rangeLabel = now.Format("January 2006")
	}

	summary := fmt.Sprintf(
		"%s report for %s: STS %s, anomaly %s, goal pace %s.",
		titlePrefix,
		rangeLabel,
		snapshot.Metrics.STS.Value,
		snapshot.Metrics.Anomaly.Value,
		snapshot.Metrics.GoalPace.Value,
	)

	body := strings.Join([]string{
		fmt.Sprintf("Today spend: %s", compactCurrency(snapshot.TodayExpense)),
		fmt.Sprintf("Month expense: %s", compactCurrency(snapshot.MonthExpense)),
		fmt.Sprintf("Month income: %s", compactCurrency(snapshot.MonthIncome)),
		fmt.Sprintf("Transfers to goals: %s", compactCurrency(snapshot.MonthTransfers)),
		fmt.Sprintf("Draft entries waiting review: %d", snapshot.DraftCount),
		fmt.Sprintf("Active goals: %d", len(snapshot.ActiveGoals)),
	}, "\n")

	return Report{
		ID:           fmt.Sprintf("RPT-%d", now.UTC().UnixNano()),
		Kind:         kind,
		PeriodKey:    periodKey,
		Title:        fmt.Sprintf("%s financial status", titlePrefix),
		Summary:      summary,
		Body:         body,
		Verdict:      verdictFromStatus(status),
		Status:       firstNonEmpty(status, "watch"),
		Model:        firstNonEmpty(model, "fallback-analyst"),
		PromptSource: firstNonEmpty(promptSource, "default"),
		Trigger:      trigger,
		CreatedAt:    now.UTC(),
	}
}

func periodKey(kind Kind, now time.Time) string {
	switch kind {
	case KindMonthly:
		return now.Format("2006-01")
	default:
		return now.Format("2006-01-02")
	}
}

func verdictFromStatus(status string) string {
	switch status {
	case "healthy":
		return "Financial posture looks good and under control."
	case "critical":
		return "Financial posture needs attention right now."
	default:
		return "Financial posture is mixed and worth monitoring."
	}
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return value
		}
	}
	return ""
}

func sameDay(a, b time.Time) bool {
	return a.UTC().Year() == b.UTC().Year() &&
		a.UTC().Month() == b.UTC().Month() &&
		a.UTC().Day() == b.UTC().Day()
}

func compactCurrency(amount int64) string {
	sign := ""
	if amount < 0 {
		sign = "-"
		amount = -amount
	}
	switch {
	case amount >= 1_000_000_000:
		return fmt.Sprintf("%s%.1fB VND", sign, float64(amount)/1_000_000_000)
	case amount >= 1_000_000:
		return fmt.Sprintf("%s%.1fM VND", sign, float64(amount)/1_000_000)
	case amount >= 1_000:
		return fmt.Sprintf("%s%.0fk VND", sign, float64(amount)/1_000)
	default:
		return fmt.Sprintf("%s%d VND", sign, amount)
	}
}

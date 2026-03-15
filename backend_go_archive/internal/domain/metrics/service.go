package metrics

import (
	"context"
	"fmt"
	"math"
	"time"

	"github.com/admin/turbo-potato/backend/internal/domain/goals"
	"github.com/admin/turbo-potato/backend/internal/domain/rules"
	"github.com/admin/turbo-potato/backend/internal/domain/transactions"
)

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
	transactions TransactionsReader
	goals        GoalsReader
	rules        RulesReader
	clock        Clock
}

func NewService(transactions TransactionsReader, goals GoalsReader, rules RulesReader, clock Clock) *Service {
	return &Service{
		transactions: transactions,
		goals:        goals,
		rules:        rules,
		clock:        clock,
	}
}

func (s *Service) Summary(ctx context.Context) (Summary, error) {
	allTransactions, err := s.transactions.List(ctx)
	if err != nil {
		return Summary{}, err
	}

	allGoals, err := s.goals.List(ctx)
	if err != nil {
		return Summary{}, err
	}

	allRules, err := s.rules.ListFixedCostRules(ctx)
	if err != nil {
		return Summary{}, err
	}

	now := s.clock.Now().UTC()
	sts := calculateSTS(allTransactions, now)
	anomaly := calculateAnomaly(allTransactions, now)
	goalPace, goalVelocity, goalETA := calculateGoalPace(allTransactions, allGoals, now)
	fixedCostLoad, runwayMonths := calculateOperatingMetrics(allTransactions, allRules, now)

	return Summary{
		STS:      sts,
		Anomaly:  anomaly,
		GoalPace: goalPace,
		OperatingPosture: OperatingPosture{
			Status: postureStatus(sts.Progress, fixedCostLoad),
			Items: []SummaryItem{
				{Label: "Runway", Value: fmt.Sprintf("%.1f months", runwayMonths)},
				{Label: "Fixed-cost load", Value: fmt.Sprintf("%d%%", fixedCostLoad)},
				{Label: "Goal velocity", Value: goalVelocity},
				{Label: "ETA", Value: goalETA},
			},
		},
		Baselines: buildBaselines(allTransactions, allGoals, allRules, now),
	}, nil
}

func calculateSTS(items []transactions.Transaction, now time.Time) MetricValue {
	const monthlyVariableBudget = 9300000.0

	currentMonthSpent := 0.0
	for _, item := range items {
		if item.Status == transactions.StatusReverted || item.Type != transactions.TypeExpense || item.IsFixed {
			continue
		}
		if item.OccurredAt.Year() == now.Year() && item.OccurredAt.Month() == now.Month() {
			currentMonthSpent += float64(item.Amount)
		}
	}

	daysInMonth := time.Date(now.Year(), now.Month()+1, 0, 0, 0, 0, 0, time.UTC).Day()
	remainingDays := max(1, daysInMonth-now.Day()+1)
	stsValue := (monthlyVariableBudget - currentMonthSpent) / float64(remainingDays)
	if stsValue < 0 {
		stsValue = 0
	}

	progress := int(math.Round((stsValue / (monthlyVariableBudget / float64(daysInMonth))) * 100))
	progress = min(100, max(0, progress))

	return MetricValue{
		Label:    "STS Today",
		Value:    compactCurrency(int64(stsValue)),
		Caption:  "Daily spend allowance based on remaining monthly variable budget.",
		Progress: progress,
		Status:   statusFromProgress(progress),
	}
}

func calculateAnomaly(items []transactions.Transaction, now time.Time) MetricValue {
	todaySpend := 0.0
	history := make([]float64, 0)

	for _, item := range items {
		if item.Status == transactions.StatusReverted || item.Type != transactions.TypeExpense || item.IsFixed {
			continue
		}

		if sameDay(item.OccurredAt, now) {
			todaySpend += float64(item.Amount)
		}

		if item.OccurredAt.Before(now) && item.OccurredAt.After(now.AddDate(0, 0, -30)) {
			history = append(history, float64(item.Amount))
		}
	}

	mean := average(history)
	stddev := standardDeviation(history, mean)
	zScore := 0.0
	if stddev > 0 {
		zScore = (todaySpend - mean) / stddev
	}

	progress := min(100, max(0, int(math.Round((math.Abs(zScore)/2.5)*100))))
	return MetricValue{
		Label:    "Anomaly Score",
		Value:    fmt.Sprintf("%.2f", zScore),
		Caption:  "Variable-spend pacing versus your recent baseline.",
		Progress: progress,
		Status:   anomalyStatus(zScore),
	}
}

func calculateGoalPace(items []transactions.Transaction, goalsList []goals.Goal, now time.Time) (MetricValue, string, string) {
	if len(goalsList) == 0 {
		return MetricValue{
			Label:    "Goal Pace",
			Value:    "0%",
			Caption:  "No active goals yet.",
			Progress: 0,
			Status:   "idle",
		}, "0/mo", "N/A"
	}

	activeGoal := goalsList[0]
	totalTransferred := int64(0)
	recentTransferred := int64(0)

	for _, item := range items {
		if item.Status == transactions.StatusReverted || item.Type != transactions.TypeTransfer {
			continue
		}
		if item.GoalName != activeGoal.Name {
			continue
		}

		totalTransferred += item.Amount
		if item.OccurredAt.After(now.AddDate(0, -3, 0)) {
			recentTransferred += item.Amount
		}
	}

	progress := 0
	if activeGoal.TargetAmount > 0 {
		progress = min(100, max(0, int(math.Round((float64(totalTransferred)/float64(activeGoal.TargetAmount))*100))))
	}

	monthlyVelocity := float64(recentTransferred) / 3.0
	eta := "N/A"
	if monthlyVelocity > 0 && activeGoal.TargetAmount > totalTransferred {
		monthsRemaining := math.Ceil(float64(activeGoal.TargetAmount-totalTransferred) / monthlyVelocity)
		eta = now.AddDate(0, int(monthsRemaining), 0).Format("Jan 2006")
	}

	return MetricValue{
			Label:    "Goal Pace",
			Value:    fmt.Sprintf("%d%%", progress),
			Caption:  "Current savings velocity relative to target timeline.",
			Progress: progress,
			Status:   statusFromProgress(progress),
		},
		compactCurrency(int64(monthlyVelocity)) + "/mo",
		eta
}

func calculateOperatingMetrics(items []transactions.Transaction, rulesList []rules.FixedCostRule, now time.Time) (int, float64) {
	fixedSpent := 0.0
	income := 0.0
	liquid := 0.0

	for _, item := range items {
		if item.Status == transactions.StatusReverted {
			continue
		}

		if item.Type == transactions.TypeExpense && item.IsFixed && item.OccurredAt.Year() == now.Year() && item.OccurredAt.Month() == now.Month() {
			fixedSpent += float64(item.Amount)
		}

		if item.Type == transactions.TypeIncome && item.OccurredAt.After(now.AddDate(0, -3, 0)) {
			income += float64(item.Amount)
			liquid += float64(item.Amount) * 0.3
		}
	}

	if fixedSpent == 0 {
		for _, rule := range rulesList {
			if rule.IsActive {
				fixedSpent += float64(rule.ExpectedAmount)
			}
		}
	}

	avgMonthlyIncome := income / 3
	fixedCostLoad := 0
	if avgMonthlyIncome > 0 {
		fixedCostLoad = int(math.Round((fixedSpent / avgMonthlyIncome) * 100))
	}

	runwayMonths := 0.0
	if fixedSpent > 0 {
		runwayMonths = liquid / fixedSpent
	}

	return fixedCostLoad, runwayMonths
}

func buildBaselines(items []transactions.Transaction, goalsList []goals.Goal, rulesList []rules.FixedCostRule, now time.Time) []BaselineSeries {
	variableSpendSeries := make([]int, 0, 12)
	fixedCostSeries := make([]int, 0, 12)
	goalVelocitySeries := make([]int, 0, 12)

	for monthOffset := 11; monthOffset >= 0; monthOffset-- {
		monthTime := time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, time.UTC).AddDate(0, -monthOffset, 0)
		variableSpendSeries = append(variableSpendSeries, int(monthlyVariableSpend(items, monthTime)))
		fixedCostSeries = append(fixedCostSeries, int(monthlyFixedSpend(items, rulesList, monthTime, now)))
		goalVelocitySeries = append(goalVelocitySeries, int(monthlyGoalTransfers(items, goalsList, monthTime)))
	}

	return []BaselineSeries{
		{
			Label:       "Variable spend",
			Description: "Rolling monthly pace for variable expenses.",
			Values:      normalizeSeries(variableSpendSeries),
			Current:     compactCurrency(int64(variableSpendSeries[len(variableSpendSeries)-1])),
			Delta:       seriesDelta(variableSpendSeries),
			ColorToken:  "var(--tp-danger)",
		},
		{
			Label:       "Fixed-cost load",
			Description: "Monthly fixed obligations against current operating structure.",
			Values:      normalizeSeries(fixedCostSeries),
			Current:     compactCurrency(int64(fixedCostSeries[len(fixedCostSeries)-1])),
			Delta:       seriesDelta(fixedCostSeries),
			ColorToken:  "var(--tp-accent)",
		},
		{
			Label:       "Goal velocity",
			Description: "Monthly transfer momentum toward active goals.",
			Values:      normalizeSeries(goalVelocitySeries),
			Current:     compactCurrency(int64(goalVelocitySeries[len(goalVelocitySeries)-1])),
			Delta:       seriesDelta(goalVelocitySeries),
			ColorToken:  "var(--tp-danger-soft)",
		},
	}
}

func monthlyVariableSpend(items []transactions.Transaction, month time.Time) float64 {
	total := 0.0
	for _, item := range items {
		if item.Status == transactions.StatusReverted || item.Type != transactions.TypeExpense || item.IsFixed {
			continue
		}
		if item.OccurredAt.Year() == month.Year() && item.OccurredAt.Month() == month.Month() {
			total += float64(item.Amount)
		}
	}
	return total
}

func monthlyFixedSpend(items []transactions.Transaction, rulesList []rules.FixedCostRule, month time.Time, now time.Time) float64 {
	total := 0.0
	for _, item := range items {
		if item.Status == transactions.StatusReverted || item.Type != transactions.TypeExpense || !item.IsFixed {
			continue
		}
		if item.OccurredAt.Year() == month.Year() && item.OccurredAt.Month() == month.Month() {
			total += float64(item.Amount)
		}
	}
	if total == 0 && month.Year() == now.Year() && month.Month() == now.Month() {
		for _, rule := range rulesList {
			if rule.IsActive {
				total += float64(rule.ExpectedAmount)
			}
		}
	}
	return total
}

func monthlyGoalTransfers(items []transactions.Transaction, goalsList []goals.Goal, month time.Time) float64 {
	if len(goalsList) == 0 {
		return 0
	}
	total := 0.0
	for _, item := range items {
		if item.Status == transactions.StatusReverted || item.Type != transactions.TypeTransfer {
			continue
		}
		if item.OccurredAt.Year() == month.Year() && item.OccurredAt.Month() == month.Month() {
			total += float64(item.Amount)
		}
	}
	return total
}

func normalizeSeries(values []int) []int {
	if len(values) == 0 {
		return values
	}
	minValue, maxValue := values[0], values[0]
	for _, value := range values[1:] {
		if value < minValue {
			minValue = value
		}
		if value > maxValue {
			maxValue = value
		}
	}
	if maxValue == minValue {
		out := make([]int, len(values))
		for i := range out {
			out[i] = 50
		}
		return out
	}
	out := make([]int, len(values))
	for i, value := range values {
		out[i] = int(math.Round((float64(value-minValue) / float64(maxValue-minValue)) * 100))
	}
	return out
}

func seriesDelta(values []int) string {
	if len(values) < 2 {
		return "0% vs previous"
	}
	current := values[len(values)-1]
	previous := values[len(values)-2]
	if previous == 0 {
		return "0% vs previous"
	}
	delta := ((float64(current) - float64(previous)) / float64(previous)) * 100
	return fmt.Sprintf("%+.0f%% vs previous", delta)
}

func compactCurrency(value int64) string {
	if value >= 1000000 {
		return fmt.Sprintf("%.1fm", float64(value)/1000000)
	}
	if value >= 1000 {
		return fmt.Sprintf("%.0fk", float64(value)/1000)
	}
	return fmt.Sprintf("%d", value)
}

func statusFromProgress(progress int) string {
	switch {
	case progress >= 80:
		return "healthy"
	case progress >= 50:
		return "warning"
	default:
		return "critical"
	}
}

func anomalyStatus(z float64) string {
	switch {
	case math.Abs(z) > 1.96:
		return "critical"
	case math.Abs(z) > 1.0:
		return "warning"
	default:
		return "healthy"
	}
}

func postureStatus(stsProgress, fixedCostLoad int) string {
	switch {
	case stsProgress < 40 || fixedCostLoad > 60:
		return "High alert"
	case stsProgress < 70 || fixedCostLoad > 40:
		return "Moderate risk"
	default:
		return "Stable"
	}
}

func average(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	total := 0.0
	for _, value := range values {
		total += value
	}
	return total / float64(len(values))
}

func standardDeviation(values []float64, mean float64) float64 {
	if len(values) == 0 {
		return 0
	}
	sum := 0.0
	for _, value := range values {
		diff := value - mean
		sum += diff * diff
	}
	return math.Sqrt(sum / float64(len(values)))
}

func sameDay(a, b time.Time) bool {
	return a.Year() == b.Year() && a.Month() == b.Month() && a.Day() == b.Day()
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

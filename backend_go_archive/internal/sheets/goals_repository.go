package sheets

import (
	"context"
	"fmt"
	"strconv"
	"time"

	"github.com/admin/turbo-potato/backend/internal/domain/goals"
)

const goalsRange = "Goals!A:E"

type GoogleGoalsRepository struct {
	client        ValuesAPI
	spreadsheetID string
}

func NewGoogleGoalsRepository(client ValuesAPI, spreadsheetID string) *GoogleGoalsRepository {
	return &GoogleGoalsRepository{
		client:        client,
		spreadsheetID: spreadsheetID,
	}
}

func (r *GoogleGoalsRepository) CreateGoal(ctx context.Context, goal goals.Goal) (goals.Goal, error) {
	if err := r.client.Append(ctx, r.spreadsheetID, goalsRange, [][]interface{}{goalToRow(goal)}); err != nil {
		return goals.Goal{}, err
	}
	return goal, nil
}

func (r *GoogleGoalsRepository) ListGoals(ctx context.Context) ([]goals.Goal, error) {
	rows, err := r.client.Get(ctx, r.spreadsheetID, "Goals!A2:E")
	if err != nil {
		return nil, err
	}

	items := make([]goals.Goal, 0, len(rows))
	for _, row := range rows {
		if len(row) == 0 {
			continue
		}

		item, err := goalFromRow(row)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}

	return items, nil
}

func goalToRow(goal goals.Goal) []interface{} {
	targetDate := ""
	if !goal.TargetDate.IsZero() {
		targetDate = goal.TargetDate.UTC().Format(time.RFC3339)
	}

	return []interface{}{
		goal.Name,
		goal.TargetAmount,
		goal.StartDate.UTC().Format(time.RFC3339),
		targetDate,
		string(goal.Status),
	}
}

func goalFromRow(row []interface{}) (goals.Goal, error) {
	if len(row) < 5 {
		return goals.Goal{}, fmt.Errorf("goal row has %d columns, expected at least 5", len(row))
	}

	targetAmount, err := strconv.ParseInt(stringify(row[1]), 10, 64)
	if err != nil {
		return goals.Goal{}, fmt.Errorf("parse goal targetAmount: %w", err)
	}

	startDate, err := time.Parse(time.RFC3339, stringify(row[2]))
	if err != nil {
		return goals.Goal{}, fmt.Errorf("parse goal startDate: %w", err)
	}

	var targetDate time.Time
	if stringify(row[3]) != "" {
		targetDate, err = time.Parse(time.RFC3339, stringify(row[3]))
		if err != nil {
			return goals.Goal{}, fmt.Errorf("parse goal targetDate: %w", err)
		}
	}

	return goals.Goal{
		Name:         stringify(row[0]),
		TargetAmount: targetAmount,
		StartDate:    startDate,
		TargetDate:   targetDate,
		Status:       goals.Status(stringify(row[4])),
	}, nil
}

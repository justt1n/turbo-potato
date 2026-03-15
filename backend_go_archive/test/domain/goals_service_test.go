package domain_test

import (
	"context"
	"testing"

	"github.com/admin/turbo-potato/backend/internal/domain/goals"
)

type fakeGoalsRepository struct {
	items []goals.Goal
}

func (r *fakeGoalsRepository) CreateGoal(_ context.Context, goal goals.Goal) (goals.Goal, error) {
	r.items = append(r.items, goal)
	return goal, nil
}

func (r *fakeGoalsRepository) ListGoals(_ context.Context) ([]goals.Goal, error) {
	return append([]goals.Goal(nil), r.items...), nil
}

func TestCreateGoalDefaults(t *testing.T) {
	repo := &fakeGoalsRepository{}
	service := goals.NewService(repo)

	goal, err := service.Create(context.Background(), goals.CreateInput{
		Name:         "Mua xe SH",
		TargetAmount: 100000000,
	})
	if err != nil {
		t.Fatalf("Create() error = %v", err)
	}

	if goal.Status != goals.StatusActive {
		t.Fatalf("expected active status, got %q", goal.Status)
	}
}

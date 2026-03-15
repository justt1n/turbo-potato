package goals

import (
	"context"
	"fmt"
	"strings"
	"time"
)

type Repository interface {
	CreateGoal(ctx context.Context, goal Goal) (Goal, error)
	ListGoals(ctx context.Context) ([]Goal, error)
}

type Service struct {
	repo Repository
}

func NewService(repo Repository) *Service {
	return &Service{repo: repo}
}

func (s *Service) Create(ctx context.Context, input CreateInput) (Goal, error) {
	name := strings.TrimSpace(input.Name)
	if name == "" {
		return Goal{}, fmt.Errorf("name is required")
	}

	if input.TargetAmount <= 0 {
		return Goal{}, fmt.Errorf("targetAmount must be greater than zero")
	}

	startDate := input.StartDate.UTC()
	if startDate.IsZero() {
		startDate = time.Now().UTC()
	}

	status := input.Status
	if status == "" {
		status = StatusActive
	}

	goal := Goal{
		Name:         name,
		TargetAmount: input.TargetAmount,
		StartDate:    startDate,
		TargetDate:   input.TargetDate.UTC(),
		Status:       status,
	}

	return s.repo.CreateGoal(ctx, goal)
}

func (s *Service) List(ctx context.Context) ([]Goal, error) {
	return s.repo.ListGoals(ctx)
}

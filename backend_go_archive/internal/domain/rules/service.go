package rules

import (
	"context"
	"fmt"
	"strings"
)

type Repository interface {
	CreateFixedCostRule(ctx context.Context, rule FixedCostRule) (FixedCostRule, error)
	ListFixedCostRules(ctx context.Context) ([]FixedCostRule, error)
}

type Service struct {
	repo Repository
}

func NewService(repo Repository) *Service {
	return &Service{repo: repo}
}

func (s *Service) CreateFixedCostRule(ctx context.Context, input CreateFixedCostRuleInput) (FixedCostRule, error) {
	name := strings.TrimSpace(input.Name)
	if name == "" {
		return FixedCostRule{}, fmt.Errorf("name is required")
	}

	if input.ExpectedAmount <= 0 {
		return FixedCostRule{}, fmt.Errorf("expectedAmount must be greater than zero")
	}

	if input.WindowStartDay < 1 || input.WindowStartDay > 31 {
		return FixedCostRule{}, fmt.Errorf("windowStartDay must be between 1 and 31")
	}

	if input.WindowEndDay < input.WindowStartDay || input.WindowEndDay > 31 {
		return FixedCostRule{}, fmt.Errorf("windowEndDay must be between windowStartDay and 31")
	}

	rule := FixedCostRule{
		Name:           name,
		ExpectedAmount: input.ExpectedAmount,
		WindowStartDay: input.WindowStartDay,
		WindowEndDay:   input.WindowEndDay,
		LinkedJarCode:  strings.TrimSpace(input.LinkedJarCode),
		IsActive:       input.IsActive,
	}

	return s.repo.CreateFixedCostRule(ctx, rule)
}

func (s *Service) ListFixedCostRules(ctx context.Context) ([]FixedCostRule, error) {
	return s.repo.ListFixedCostRules(ctx)
}

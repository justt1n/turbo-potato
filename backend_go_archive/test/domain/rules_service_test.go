package domain_test

import (
	"context"
	"testing"

	"github.com/admin/turbo-potato/backend/internal/domain/rules"
)

type fakeRulesRepository struct {
	items []rules.FixedCostRule
}

func (r *fakeRulesRepository) CreateFixedCostRule(_ context.Context, rule rules.FixedCostRule) (rules.FixedCostRule, error) {
	r.items = append(r.items, rule)
	return rule, nil
}

func (r *fakeRulesRepository) ListFixedCostRules(_ context.Context) ([]rules.FixedCostRule, error) {
	return append([]rules.FixedCostRule(nil), r.items...), nil
}

func TestCreateFixedCostRuleRejectsInvalidWindow(t *testing.T) {
	repo := &fakeRulesRepository{}
	service := rules.NewService(repo)

	_, err := service.CreateFixedCostRule(context.Background(), rules.CreateFixedCostRuleInput{
		Name:           "Bad Rule",
		ExpectedAmount: 1000000,
		WindowStartDay: 10,
		WindowEndDay:   5,
	})
	if err == nil {
		t.Fatal("expected validation error")
	}
}

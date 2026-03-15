package sheets

import (
	"context"
	"fmt"
	"strconv"
	"strings"

	"github.com/admin/turbo-potato/backend/internal/domain/rules"
)

const fixedCostRulesRange = "Fixed_Cost_Rules!A:F"

type GoogleRulesRepository struct {
	client        ValuesAPI
	spreadsheetID string
}

func NewGoogleRulesRepository(client ValuesAPI, spreadsheetID string) *GoogleRulesRepository {
	return &GoogleRulesRepository{
		client:        client,
		spreadsheetID: spreadsheetID,
	}
}

func (r *GoogleRulesRepository) CreateFixedCostRule(ctx context.Context, rule rules.FixedCostRule) (rules.FixedCostRule, error) {
	if err := r.client.Append(ctx, r.spreadsheetID, fixedCostRulesRange, [][]interface{}{fixedCostRuleToRow(rule)}); err != nil {
		return rules.FixedCostRule{}, err
	}

	return rule, nil
}

func (r *GoogleRulesRepository) ListFixedCostRules(ctx context.Context) ([]rules.FixedCostRule, error) {
	rows, err := r.client.Get(ctx, r.spreadsheetID, "Fixed_Cost_Rules!A2:F")
	if err != nil {
		return nil, err
	}

	items := make([]rules.FixedCostRule, 0, len(rows))
	for _, row := range rows {
		if len(row) == 0 {
			continue
		}

		item, err := fixedCostRuleFromRow(row)
		if err != nil {
			return nil, err
		}

		items = append(items, item)
	}

	return items, nil
}

func fixedCostRuleToRow(rule rules.FixedCostRule) []interface{} {
	return []interface{}{
		rule.Name,
		rule.ExpectedAmount,
		rule.WindowStartDay,
		rule.WindowEndDay,
		rule.LinkedJarCode,
		rule.IsActive,
	}
}

func fixedCostRuleFromRow(row []interface{}) (rules.FixedCostRule, error) {
	if len(row) < 6 {
		return rules.FixedCostRule{}, fmt.Errorf("fixed cost rule row has %d columns, expected at least 6", len(row))
	}

	expectedAmount, err := strconv.ParseInt(stringify(row[1]), 10, 64)
	if err != nil {
		return rules.FixedCostRule{}, fmt.Errorf("parse expectedAmount: %w", err)
	}

	windowStartDay, err := strconv.Atoi(stringify(row[2]))
	if err != nil {
		return rules.FixedCostRule{}, fmt.Errorf("parse windowStartDay: %w", err)
	}

	windowEndDay, err := strconv.Atoi(stringify(row[3]))
	if err != nil {
		return rules.FixedCostRule{}, fmt.Errorf("parse windowEndDay: %w", err)
	}

	isActive, err := strconv.ParseBool(strings.ToLower(stringify(row[5])))
	if err != nil {
		return rules.FixedCostRule{}, fmt.Errorf("parse isActive: %w", err)
	}

	return rules.FixedCostRule{
		Name:           stringify(row[0]),
		ExpectedAmount: expectedAmount,
		WindowStartDay: windowStartDay,
		WindowEndDay:   windowEndDay,
		LinkedJarCode:  stringify(row[4]),
		IsActive:       isActive,
	}, nil
}

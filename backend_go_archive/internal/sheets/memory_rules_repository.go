package sheets

import (
	"context"
	"sync"

	"github.com/admin/turbo-potato/backend/internal/domain/rules"
)

type MemoryRulesRepository struct {
	mu    sync.RWMutex
	items []rules.FixedCostRule
}

func NewMemoryRulesRepository() *MemoryRulesRepository {
	return &MemoryRulesRepository{items: make([]rules.FixedCostRule, 0)}
}

func (r *MemoryRulesRepository) CreateFixedCostRule(_ context.Context, rule rules.FixedCostRule) (rules.FixedCostRule, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.items = append(r.items, rule)
	return rule, nil
}

func (r *MemoryRulesRepository) ListFixedCostRules(_ context.Context) ([]rules.FixedCostRule, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]rules.FixedCostRule, len(r.items))
	copy(items, r.items)
	return items, nil
}

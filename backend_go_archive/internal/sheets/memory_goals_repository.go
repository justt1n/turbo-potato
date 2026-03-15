package sheets

import (
	"context"
	"sync"

	"github.com/admin/turbo-potato/backend/internal/domain/goals"
)

type MemoryGoalsRepository struct {
	mu    sync.RWMutex
	items []goals.Goal
}

func NewMemoryGoalsRepository() *MemoryGoalsRepository {
	return &MemoryGoalsRepository{items: make([]goals.Goal, 0)}
}

func (r *MemoryGoalsRepository) CreateGoal(_ context.Context, goal goals.Goal) (goals.Goal, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.items = append(r.items, goal)
	return goal, nil
}

func (r *MemoryGoalsRepository) ListGoals(_ context.Context) ([]goals.Goal, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]goals.Goal, len(r.items))
	copy(items, r.items)
	return items, nil
}

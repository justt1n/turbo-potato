package transactions

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

type Repository interface {
	CreateTransaction(ctx context.Context, tx Transaction) (Transaction, error)
	GetTransaction(ctx context.Context, id string) (Transaction, error)
	UpdateTransaction(ctx context.Context, tx Transaction) (Transaction, error)
	ListTransactions(ctx context.Context) ([]Transaction, error)
}

type AuditLogger interface {
	Log(ctx context.Context, entry AuditEntry) error
}

type IDGenerator interface {
	NewTransactionID() string
}

type Clock interface {
	Now() time.Time
}

type Service struct {
	repo  Repository
	audit AuditLogger
	ids   IDGenerator
	clock Clock
}

func NewService(repo Repository, audit AuditLogger, ids IDGenerator, clock Clock) *Service {
	return &Service{
		repo:  repo,
		audit: audit,
		ids:   ids,
		clock: clock,
	}
}

func (s *Service) Create(ctx context.Context, input CreateInput) (Transaction, error) {
	if input.Amount <= 0 {
		return Transaction{}, fmt.Errorf("amount must be greater than zero")
	}

	if input.Type != TypeIncome && input.Type != TypeExpense && input.Type != TypeTransfer {
		return Transaction{}, fmt.Errorf("type must be one of IN, OUT, TRANSFER")
	}

	if input.Type == TypeTransfer && strings.TrimSpace(input.GoalName) == "" && strings.TrimSpace(input.JarCode) == "" {
		return Transaction{}, fmt.Errorf("transfer must target a goal or jar")
	}

	now := s.clock.Now().UTC()
	occurredAt := input.OccurredAt
	if occurredAt.IsZero() {
		occurredAt = now
	}

	currency := strings.TrimSpace(input.Currency)
	if currency == "" {
		currency = "VND"
	}

	status := input.Status
	if status == "" {
		status = StatusConfirmed
	}

	source := strings.TrimSpace(input.Source)
	if source == "" {
		source = "manual"
	}

	transaction := Transaction{
		ID:         s.ids.NewTransactionID(),
		OccurredAt: occurredAt,
		Type:       input.Type,
		Amount:     input.Amount,
		Currency:   currency,
		JarCode:    strings.TrimSpace(input.JarCode),
		GoalName:   strings.TrimSpace(input.GoalName),
		Account:    strings.TrimSpace(input.Account),
		IsFixed:    input.IsFixed,
		Note:       strings.TrimSpace(input.Note),
		Source:     source,
		Status:     status,
		CreatedAt:  now,
		UpdatedAt:  now,
	}

	return s.repo.CreateTransaction(ctx, transaction)
}

func (s *Service) List(ctx context.Context) ([]Transaction, error) {
	return s.repo.ListTransactions(ctx)
}

func (s *Service) Correct(ctx context.Context, id string, input UpdateInput, reason, actor string) (Transaction, error) {
	current, err := s.repo.GetTransaction(ctx, id)
	if err != nil {
		return Transaction{}, err
	}

	updated, err := s.applyUpdate(current, input)
	if err != nil {
		return Transaction{}, err
	}

	saved, err := s.repo.UpdateTransaction(ctx, updated)
	if err != nil {
		return Transaction{}, err
	}

	if err := s.logAudit(ctx, "corrected", current, saved, reason, actor); err != nil {
		return Transaction{}, err
	}

	return saved, nil
}

func (s *Service) Undo(ctx context.Context, id, reason, actor string) (Transaction, error) {
	current, err := s.repo.GetTransaction(ctx, id)
	if err != nil {
		return Transaction{}, err
	}

	previous := current
	current.Status = StatusReverted
	current.UpdatedAt = s.clock.Now().UTC()

	saved, err := s.repo.UpdateTransaction(ctx, current)
	if err != nil {
		return Transaction{}, err
	}

	if err := s.logAudit(ctx, "undone", previous, saved, reason, actor); err != nil {
		return Transaction{}, err
	}

	return saved, nil
}

func (s *Service) applyUpdate(current Transaction, input UpdateInput) (Transaction, error) {
	if input.Amount <= 0 {
		return Transaction{}, fmt.Errorf("amount must be greater than zero")
	}

	if input.Type != TypeIncome && input.Type != TypeExpense && input.Type != TypeTransfer {
		return Transaction{}, fmt.Errorf("type must be one of IN, OUT, TRANSFER")
	}

	if input.Type == TypeTransfer && strings.TrimSpace(input.GoalName) == "" && strings.TrimSpace(input.JarCode) == "" {
		return Transaction{}, fmt.Errorf("transfer must target a goal or jar")
	}

	current.OccurredAt = input.OccurredAt
	current.Type = input.Type
	current.Amount = input.Amount
	current.Currency = strings.TrimSpace(input.Currency)
	current.JarCode = strings.TrimSpace(input.JarCode)
	current.GoalName = strings.TrimSpace(input.GoalName)
	current.Account = strings.TrimSpace(input.Account)
	current.IsFixed = input.IsFixed
	current.Note = strings.TrimSpace(input.Note)
	if input.Status != "" {
		current.Status = input.Status
	}
	current.UpdatedAt = s.clock.Now().UTC()
	return current, nil
}

func (s *Service) logAudit(ctx context.Context, action string, previous, next Transaction, reason, actor string) error {
	previousJSON, err := json.Marshal(previous)
	if err != nil {
		return fmt.Errorf("marshal previous transaction: %w", err)
	}
	nextJSON, err := json.Marshal(next)
	if err != nil {
		return fmt.Errorf("marshal next transaction: %w", err)
	}

	return s.audit.Log(ctx, AuditEntry{
		ID:            fmt.Sprintf("AUD-%s-%d", next.ID, s.clock.Now().UTC().UnixNano()),
		TransactionID: next.ID,
		Action:        action,
		PreviousValue: string(previousJSON),
		NewValue:      string(nextJSON),
		Reason:        strings.TrimSpace(reason),
		Actor:         strings.TrimSpace(actor),
		CreatedAt:     s.clock.Now().UTC(),
	})
}

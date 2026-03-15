package transactions

import "time"

type Type string

const (
	TypeIncome   Type = "IN"
	TypeExpense  Type = "OUT"
	TypeTransfer Type = "TRANSFER"
)

type Status string

const (
	StatusDraft     Status = "draft"
	StatusConfirmed Status = "confirmed"
	StatusReverted  Status = "reverted"
)

type Transaction struct {
	ID         string    `json:"id"`
	OccurredAt time.Time `json:"occurredAt"`
	Type       Type      `json:"type"`
	Amount     int64     `json:"amount"`
	Currency   string    `json:"currency"`
	JarCode    string    `json:"jarCode,omitempty"`
	GoalName   string    `json:"goalName,omitempty"`
	Account    string    `json:"accountName,omitempty"`
	IsFixed    bool      `json:"isFixed"`
	Note       string    `json:"note"`
	Source     string    `json:"source"`
	Status     Status    `json:"status"`
	CreatedAt  time.Time `json:"createdAt"`
	UpdatedAt  time.Time `json:"updatedAt"`
}

type CreateInput struct {
	OccurredAt time.Time `json:"occurredAt"`
	Type       Type      `json:"type"`
	Amount     int64     `json:"amount"`
	Currency   string    `json:"currency"`
	JarCode    string    `json:"jarCode"`
	GoalName   string    `json:"goalName"`
	Account    string    `json:"accountName"`
	IsFixed    bool      `json:"isFixed"`
	Note       string    `json:"note"`
	Source     string    `json:"source"`
	Status     Status    `json:"status"`
}

type UpdateInput struct {
	OccurredAt time.Time `json:"occurredAt"`
	Type       Type      `json:"type"`
	Amount     int64     `json:"amount"`
	Currency   string    `json:"currency"`
	JarCode    string    `json:"jarCode"`
	GoalName   string    `json:"goalName"`
	Account    string    `json:"accountName"`
	IsFixed    bool      `json:"isFixed"`
	Note       string    `json:"note"`
	Status     Status    `json:"status"`
}

type AuditEntry struct {
	ID            string    `json:"id"`
	TransactionID string    `json:"transactionId"`
	Action        string    `json:"action"`
	PreviousValue string    `json:"previousValue"`
	NewValue      string    `json:"newValue"`
	Reason        string    `json:"reason"`
	Actor         string    `json:"actor"`
	CreatedAt     time.Time `json:"createdAt"`
}

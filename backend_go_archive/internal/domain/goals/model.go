package goals

import "time"

type Status string

const (
	StatusActive    Status = "active"
	StatusCompleted Status = "completed"
	StatusPaused    Status = "paused"
)

type Goal struct {
	Name         string    `json:"name"`
	TargetAmount int64     `json:"targetAmount"`
	StartDate    time.Time `json:"startDate"`
	TargetDate   time.Time `json:"targetDate,omitempty"`
	Status       Status    `json:"status"`
}

type CreateInput struct {
	Name         string    `json:"name"`
	TargetAmount int64     `json:"targetAmount"`
	StartDate    time.Time `json:"startDate"`
	TargetDate   time.Time `json:"targetDate"`
	Status       Status    `json:"status"`
}

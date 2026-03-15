package reports

import "time"

type Kind string

const (
	KindDaily   Kind = "daily"
	KindMonthly Kind = "monthly"
)

type Report struct {
	ID           string    `json:"id"`
	Kind         Kind      `json:"kind"`
	PeriodKey    string    `json:"periodKey"`
	Title        string    `json:"title"`
	Summary      string    `json:"summary"`
	Body         string    `json:"body"`
	Verdict      string    `json:"verdict"`
	Status       string    `json:"status"`
	Model        string    `json:"model"`
	PromptSource string    `json:"promptSource"`
	Trigger      string    `json:"trigger"`
	CreatedAt    time.Time `json:"createdAt"`
}

type Snapshot struct {
	Daily   Report  `json:"daily"`
	Monthly *Report `json:"monthly,omitempty"`
}

type GenerateInput struct {
	Trigger string `json:"trigger"`
	Actor   string `json:"actor"`
}

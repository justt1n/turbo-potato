package ingestion

import "time"

type ParsedReceipt struct {
	ID             string    `json:"id"`
	TransactionID  string    `json:"transactionId"`
	RawInput       string    `json:"rawInput"`
	RegexAmount    int64     `json:"regexAmount"`
	RegexTags      []string  `json:"regexTags"`
	LLMModel       string    `json:"llmModel"`
	LLMOutputJSON  string    `json:"llmOutputJson"`
	ValidationNote string    `json:"validationNote"`
	Confidence     string    `json:"confidence"`
	PromptSource   string    `json:"promptSource"`
	CreatedAt      time.Time `json:"createdAt"`
}

type IngestInput struct {
	RawInput string `json:"rawInput"`
	Source   string `json:"source"`
	Actor    string `json:"actor"`
}

type Result struct {
	TransactionID string        `json:"transactionId"`
	Receipt       ParsedReceipt `json:"receipt"`
}

package ingestion

import (
	"context"
	"encoding/json"
	"fmt"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/admin/turbo-potato/backend/internal/ai"
	"github.com/admin/turbo-potato/backend/internal/domain/transactions"
)

var (
	amountPattern = regexp.MustCompile(`(?i)(\d[\d\.,]*)(k)?`)
	tagPattern    = regexp.MustCompile(`#([[:alnum:]_]+)`)
)

type TransactionCreator interface {
	Create(ctx context.Context, input transactions.CreateInput) (transactions.Transaction, error)
}

type ReceiptRepository interface {
	SaveParsedReceipt(ctx context.Context, receipt ParsedReceipt) (ParsedReceipt, error)
}

type Clock interface {
	Now() time.Time
}

type Service struct {
	transactions TransactionCreator
	receipts     ReceiptRepository
	aiClient     ai.Client
	clock        Clock
	model        string
	prompt       string
	promptSource string
}

func NewService(transactions TransactionCreator, receipts ReceiptRepository, aiClient ai.Client, clock Clock, model, prompt, promptSource string) *Service {
	return &Service{
		transactions: transactions,
		receipts:     receipts,
		aiClient:     aiClient,
		clock:        clock,
		model:        model,
		prompt:       prompt,
		promptSource: promptSource,
	}
}

func (s *Service) IngestChat(ctx context.Context, input IngestInput) (Result, error) {
	raw := strings.TrimSpace(input.RawInput)
	if raw == "" {
		return Result{}, fmt.Errorf("rawInput is required")
	}

	regexAmount := extractAmount(raw)
	regexTags := extractTags(raw)

	suggestion, llmPayload := s.buildSuggestion(ctx, raw, regexAmount, regexTags)
	txType := coalesceType(suggestion.Action, fallbackType(raw))
	jarCode := firstNonEmptyString(suggestion.JarCategory, guessJar(raw))
	cleanNote := buildCleanNote(raw, regexTags, suggestion.CleanNote)
	currency := firstNonEmptyString(suggestion.Currency, "VND")
	goalName := strings.TrimSpace(suggestion.GoalName)
	accountName := strings.TrimSpace(suggestion.AccountName)
	isFixed := suggestion.IsFixed || looksFixed(raw)
	finalAmount := max64(1, regexAmount)
	if regexAmount == 0 && suggestion.Amount > 0 {
		finalAmount = suggestion.Amount
	}

	tx, err := s.transactions.Create(ctx, transactions.CreateInput{
		OccurredAt: s.clock.Now().UTC(),
		Type:       txType,
		Amount:     finalAmount,
		Currency:   currency,
		JarCode:    jarCode,
		GoalName:   goalName,
		Account:    accountName,
		IsFixed:    isFixed,
		Note:       cleanNote,
		Source:     defaultString(input.Source, "chat"),
		Status:     transactions.StatusDraft,
	})
	if err != nil {
		return Result{}, err
	}

	receipt, err := s.receipts.SaveParsedReceipt(ctx, ParsedReceipt{
		ID:             fmt.Sprintf("RCPT-%d", s.clock.Now().UTC().UnixNano()),
		TransactionID:  tx.ID,
		RawInput:       raw,
		RegexAmount:    regexAmount,
		RegexTags:      regexTags,
		LLMModel:       defaultString(s.model, "configurable-parser"),
		LLMOutputJSON:  string(llmPayload),
		ValidationNote: validationNote(regexAmount, suggestion),
		Confidence:     confidenceLabel(regexAmount, suggestion),
		PromptSource:   defaultString(s.promptSource, "none"),
		CreatedAt:      s.clock.Now().UTC(),
	})
	if err != nil {
		return Result{}, err
	}

	return Result{
		TransactionID: tx.ID,
		Receipt:       receipt,
	}, nil
}

type parseSuggestion struct {
	Action      string   `json:"action"`
	Amount      int64    `json:"amount"`
	JarCategory string   `json:"jar_category"`
	IsFixed     bool     `json:"is_fixed"`
	CleanNote   string   `json:"clean_note"`
	Tags        []string `json:"tags"`
	Currency    string   `json:"currency"`
	GoalName    string   `json:"goal_name"`
	AccountName string   `json:"account_name"`
}

func (s *Service) buildSuggestion(ctx context.Context, raw string, regexAmount int64, regexTags []string) (parseSuggestion, []byte) {
	fallback := parseSuggestion{
		Action:      string(fallbackType(raw)),
		Amount:      regexAmount,
		JarCategory: guessJar(raw),
		IsFixed:     looksFixed(raw),
		CleanNote:   strings.TrimSpace(raw),
		Tags:        regexTags,
		Currency:    "VND",
	}

	if len(regexTags) > 0 {
		fallback.CleanNote = buildCleanNote(raw, regexTags, fallback.CleanNote)
	}

	prompt := s.renderPrompt(raw, regexAmount, regexTags)
	if s.aiClient != nil {
		output, err := s.aiClient.Complete(ctx, ai.CompletionInput{
			Model:  s.model,
			Prompt: prompt,
		})
		if err == nil {
			if parsed, parseErr := parseSuggestionFromText(output.Text); parseErr == nil {
				merged := mergeSuggestion(fallback, parsed)
				payload, _ := json.Marshal(map[string]any{
					"provider_used": true,
					"model":         defaultString(output.Model, s.model),
					"suggestion":    merged,
				})
				return merged, payload
			}
		}
	}

	payload, _ := json.Marshal(map[string]any{
		"provider_used": false,
		"model":         defaultString(s.model, "configurable-parser"),
		"suggestion":    fallback,
	})
	return fallback, payload
}

func (s *Service) renderPrompt(raw string, regexAmount int64, regexTags []string) string {
	template := strings.TrimSpace(s.prompt)
	replaced := strings.NewReplacer(
		"{{raw_input}}", raw,
		"{{regex_amount}}", strconv.FormatInt(regexAmount, 10),
		"{{regex_tags_json}}", formatTagsJSON(regexTags),
	).Replace(template)
	if strings.TrimSpace(replaced) != "" {
		return replaced
	}

	return fmt.Sprintf(`You are a transaction parser.
Return strict JSON with keys:
action, amount, jar_category, is_fixed, clean_note, tags, currency, goal_name, account_name.

Raw input: %s
Regex amount: %d
Regex tags: %s`, raw, regexAmount, formatTagsJSON(regexTags))
}

func parseSuggestionFromText(raw string) (parseSuggestion, error) {
	var parsed parseSuggestion
	if err := json.Unmarshal([]byte(strings.TrimSpace(raw)), &parsed); err == nil {
		return parsed, nil
	}

	start := strings.Index(raw, "{")
	end := strings.LastIndex(raw, "}")
	if start >= 0 && end > start {
		if err := json.Unmarshal([]byte(raw[start:end+1]), &parsed); err == nil {
			return parsed, nil
		}
	}

	return parseSuggestion{}, fmt.Errorf("could not parse llm suggestion")
}

func mergeSuggestion(base, override parseSuggestion) parseSuggestion {
	base.Action = firstNonEmptyString(override.Action, base.Action)
	if override.Amount > 0 {
		base.Amount = override.Amount
	}
	base.JarCategory = firstNonEmptyString(override.JarCategory, base.JarCategory)
	base.IsFixed = base.IsFixed || override.IsFixed
	base.CleanNote = firstNonEmptyString(override.CleanNote, base.CleanNote)
	if len(override.Tags) > 0 {
		base.Tags = override.Tags
	}
	base.Currency = firstNonEmptyString(override.Currency, base.Currency)
	base.GoalName = firstNonEmptyString(override.GoalName, base.GoalName)
	base.AccountName = firstNonEmptyString(override.AccountName, base.AccountName)
	return base
}

func fallbackType(raw string) transactions.Type {
	txType := transactions.TypeExpense
	if strings.Contains(strings.ToLower(raw), "thu") {
		txType = transactions.TypeIncome
	}
	return txType
}

func buildCleanNote(raw string, regexTags []string, suggested string) string {
	cleanNote := strings.TrimSpace(firstNonEmptyString(suggested, raw))
	if len(regexTags) > 0 && !strings.Contains(cleanNote, "#") {
		cleanNote = strings.TrimSpace(cleanNote + " " + strings.Join(prefixTags(regexTags), " "))
	}
	return cleanNote
}

func extractAmount(raw string) int64 {
	matches := amountPattern.FindStringSubmatch(strings.ReplaceAll(raw, " ", ""))
	if len(matches) < 2 {
		return 0
	}

	cleaned := strings.ReplaceAll(matches[1], ".", "")
	cleaned = strings.ReplaceAll(cleaned, ",", "")
	value, err := strconv.ParseInt(cleaned, 10, 64)
	if err != nil {
		return 0
	}
	if len(matches) > 2 && strings.EqualFold(matches[2], "k") {
		value *= 1000
	}
	return value
}

func extractTags(raw string) []string {
	matches := tagPattern.FindAllStringSubmatch(raw, -1)
	out := make([]string, 0, len(matches))
	for _, match := range matches {
		if len(match) > 1 {
			out = append(out, match[1])
		}
	}
	return out
}

func guessJar(raw string) string {
	lowered := strings.ToLower(raw)
	switch {
	case strings.Contains(lowered, "qua"), strings.Contains(lowered, "dam cuoi"):
		return "ChoDi"
	case strings.Contains(lowered, "khoa hoc"), strings.Contains(lowered, "sach"):
		return "GiaoDuc"
	case strings.Contains(lowered, "vang"), strings.Contains(lowered, "co phieu"):
		return "TuDoTaiChinh"
	case strings.Contains(lowered, "xe"), strings.Contains(lowered, "tiet kiem"):
		return "TietKiem"
	case strings.Contains(lowered, "an"), strings.Contains(lowered, "uong"), strings.Contains(lowered, "nha hang"), strings.Contains(lowered, "nhau"):
		return "HuongThu"
	default:
		return "ThietYeu"
	}
}

func looksFixed(raw string) bool {
	lowered := strings.ToLower(raw)
	return strings.Contains(lowered, "tien nha") ||
		strings.Contains(lowered, "rent") ||
		strings.Contains(lowered, "spotify") ||
		strings.Contains(lowered, "netflix")
}

func validationNote(regexAmount int64, suggestion parseSuggestion) string {
	switch {
	case regexAmount > 0 && suggestion.Amount > 0 && suggestion.Amount != regexAmount:
		return "amount overridden by regex after llm mismatch"
	case regexAmount > 0:
		return "amount validated by regex"
	case suggestion.Amount > 0:
		return "amount supplied by llm fallback"
	default:
		return "amount missing, fallback minimum applied"
	}
}

func confidenceLabel(regexAmount int64, suggestion parseSuggestion) string {
	if regexAmount > 0 && suggestion.JarCategory != "" {
		return "high"
	}
	if regexAmount > 0 || suggestion.Amount > 0 {
		return "medium"
	}
	return "low"
}

func prefixTags(tags []string) []string {
	out := make([]string, 0, len(tags))
	for _, tag := range tags {
		out = append(out, "#"+tag)
	}
	return out
}

func defaultString(value, fallback string) string {
	if strings.TrimSpace(value) == "" {
		return fallback
	}
	return value
}

func firstNonEmptyString(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return strings.TrimSpace(value)
		}
	}
	return ""
}

func formatTagsJSON(tags []string) string {
	payload, _ := json.Marshal(tags)
	return string(payload)
}

func max64(a, b int64) int64 {
	if a > b {
		return a
	}
	return b
}

func coalesceType(raw string, fallback transactions.Type) transactions.Type {
	switch strings.ToUpper(strings.TrimSpace(raw)) {
	case string(transactions.TypeIncome):
		return transactions.TypeIncome
	case string(transactions.TypeTransfer):
		return transactions.TypeTransfer
	case string(transactions.TypeExpense):
		return transactions.TypeExpense
	default:
		return fallback
	}
}

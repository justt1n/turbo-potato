package ai

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/admin/turbo-potato/backend/internal/config"
)

var ErrNotConfigured = errors.New("ai client is not configured")

type CompletionInput struct {
	Model  string
	Prompt string
}

type CompletionOutput struct {
	Text  string
	Model string
}

type Client interface {
	Complete(ctx context.Context, input CompletionInput) (CompletionOutput, error)
}

type NoopClient struct{}

func (NoopClient) Complete(context.Context, CompletionInput) (CompletionOutput, error) {
	return CompletionOutput{}, ErrNotConfigured
}

type HTTPDoer interface {
	Do(req *http.Request) (*http.Response, error)
}

func NewClient(cfg config.Config) Client {
	provider := strings.ToLower(strings.TrimSpace(cfg.AI.Provider))
	if provider == "" || provider == "none" || cfg.AI.APIKey == "" {
		return NoopClient{}
	}

	httpClient := &http.Client{Timeout: 30 * time.Second}
	switch provider {
	case "openai":
		return NewOpenAIClient(httpClient, cfg.AI.APIKey, cfg.AI.BaseURL)
	case "gemini", "google":
		return NewGeminiClient(httpClient, cfg.AI.APIKey, cfg.AI.BaseURL)
	default:
		return NoopClient{}
	}
}

type OpenAIClient struct {
	httpClient HTTPDoer
	apiKey     string
	baseURL    string
}

func NewOpenAIClient(httpClient HTTPDoer, apiKey, baseURL string) *OpenAIClient {
	return &OpenAIClient{
		httpClient: httpClient,
		apiKey:     apiKey,
		baseURL:    firstNonEmpty(baseURL, "https://api.openai.com"),
	}
}

func (c *OpenAIClient) Complete(ctx context.Context, input CompletionInput) (CompletionOutput, error) {
	payload := map[string]any{
		"model": input.Model,
		"input": input.Prompt,
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return CompletionOutput{}, fmt.Errorf("marshal openai request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, strings.TrimRight(c.baseURL, "/")+"/v1/responses", bytes.NewReader(body))
	if err != nil {
		return CompletionOutput{}, fmt.Errorf("build openai request: %w", err)
	}
	req.Header.Set("Authorization", "Bearer "+c.apiKey)
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return CompletionOutput{}, fmt.Errorf("call openai: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		raw, _ := io.ReadAll(resp.Body)
		return CompletionOutput{}, fmt.Errorf("openai returned %s: %s", resp.Status, strings.TrimSpace(string(raw)))
	}

	var parsed struct {
		Model      string `json:"model"`
		OutputText string `json:"output_text"`
		Output     []struct {
			Content []struct {
				Type string `json:"type"`
				Text string `json:"text"`
			} `json:"content"`
		} `json:"output"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&parsed); err != nil {
		return CompletionOutput{}, fmt.Errorf("decode openai response: %w", err)
	}

	text := strings.TrimSpace(parsed.OutputText)
	if text == "" {
		parts := make([]string, 0)
		for _, item := range parsed.Output {
			for _, content := range item.Content {
				if strings.TrimSpace(content.Text) != "" {
					parts = append(parts, content.Text)
				}
			}
		}
		text = strings.TrimSpace(strings.Join(parts, "\n"))
	}
	if text == "" {
		return CompletionOutput{}, fmt.Errorf("openai response contained no text output")
	}

	return CompletionOutput{
		Text:  text,
		Model: firstNonEmpty(parsed.Model, input.Model),
	}, nil
}

type GeminiClient struct {
	httpClient HTTPDoer
	apiKey     string
	baseURL    string
}

func NewGeminiClient(httpClient HTTPDoer, apiKey, baseURL string) *GeminiClient {
	return &GeminiClient{
		httpClient: httpClient,
		apiKey:     apiKey,
		baseURL:    firstNonEmpty(baseURL, "https://generativelanguage.googleapis.com"),
	}
}

func (c *GeminiClient) Complete(ctx context.Context, input CompletionInput) (CompletionOutput, error) {
	payload := map[string]any{
		"contents": []map[string]any{
			{
				"parts": []map[string]string{
					{"text": input.Prompt},
				},
			},
		},
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return CompletionOutput{}, fmt.Errorf("marshal gemini request: %w", err)
	}

	endpoint := fmt.Sprintf(
		"%s/v1beta/models/%s:generateContent?key=%s",
		strings.TrimRight(c.baseURL, "/"),
		input.Model,
		c.apiKey,
	)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, bytes.NewReader(body))
	if err != nil {
		return CompletionOutput{}, fmt.Errorf("build gemini request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return CompletionOutput{}, fmt.Errorf("call gemini: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		raw, _ := io.ReadAll(resp.Body)
		return CompletionOutput{}, fmt.Errorf("gemini returned %s: %s", resp.Status, strings.TrimSpace(string(raw)))
	}

	var parsed struct {
		Candidates []struct {
			Content struct {
				Parts []struct {
					Text string `json:"text"`
				} `json:"parts"`
			} `json:"content"`
		} `json:"candidates"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&parsed); err != nil {
		return CompletionOutput{}, fmt.Errorf("decode gemini response: %w", err)
	}

	parts := make([]string, 0)
	for _, candidate := range parsed.Candidates {
		for _, part := range candidate.Content.Parts {
			if strings.TrimSpace(part.Text) != "" {
				parts = append(parts, part.Text)
			}
		}
	}
	text := strings.TrimSpace(strings.Join(parts, "\n"))
	if text == "" {
		return CompletionOutput{}, fmt.Errorf("gemini response contained no text output")
	}

	return CompletionOutput{
		Text:  text,
		Model: input.Model,
	}, nil
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return value
		}
	}
	return ""
}

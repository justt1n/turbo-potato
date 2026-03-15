package ai_test

import (
	"context"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/admin/turbo-potato/backend/internal/ai"
	"github.com/admin/turbo-potato/backend/internal/config"
)

func TestNewClientReturnsNoopWhenMissingConfig(t *testing.T) {
	client := ai.NewClient(config.Config{})
	if _, ok := client.(ai.NoopClient); !ok {
		t.Fatal("expected noop client")
	}
}

func TestOpenAIClientComplete(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/responses" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		if got := r.Header.Get("Authorization"); got != "Bearer test-key" {
			t.Fatalf("unexpected authorization header: %s", got)
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = io.WriteString(w, `{"model":"gpt-5-mini","output_text":"{\"action\":\"OUT\",\"amount\":500000}"}`)
	}))
	defer server.Close()

	client := ai.NewOpenAIClient(server.Client(), "test-key", server.URL)
	result, err := client.Complete(context.Background(), ai.CompletionInput{
		Model:  "gpt-5-mini",
		Prompt: "prompt",
	})
	if err != nil {
		t.Fatalf("Complete() error = %v", err)
	}
	if !strings.Contains(result.Text, `"amount":500000`) {
		t.Fatalf("unexpected text: %s", result.Text)
	}
}

func TestGeminiClientComplete(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !strings.Contains(r.URL.Path, "/v1beta/models/gemini-2.5-flash:generateContent") {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		if got := r.URL.Query().Get("key"); got != "test-key" {
			t.Fatalf("unexpected api key: %s", got)
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = io.WriteString(w, `{"candidates":[{"content":{"parts":[{"text":"{\"action\":\"IN\",\"amount\":1000000}"}]}}]}`)
	}))
	defer server.Close()

	client := ai.NewGeminiClient(server.Client(), "test-key", server.URL)
	result, err := client.Complete(context.Background(), ai.CompletionInput{
		Model:  "gemini-2.5-flash",
		Prompt: "prompt",
	})
	if err != nil {
		t.Fatalf("Complete() error = %v", err)
	}
	if !strings.Contains(result.Text, `"amount":1000000`) {
		t.Fatalf("unexpected text: %s", result.Text)
	}
}

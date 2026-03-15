package config_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/admin/turbo-potato/backend/internal/config"
)

func TestLoadDefaults(t *testing.T) {
	t.Setenv("APP_ENV", "")
	t.Setenv("APP_PORT", "")
	t.Setenv("APP_CONFIG_FILE", "")

	cfg, err := config.Load()
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}

	if cfg.App.Env != "development" {
		t.Fatalf("expected default app env, got %q", cfg.App.Env)
	}

	if cfg.App.Port != "8080" {
		t.Fatalf("expected default app port, got %q", cfg.App.Port)
	}
}

func TestLoadFromYAMLFileAndSecretFiles(t *testing.T) {
	dir := t.TempDir()
	serviceAccountPath := filepath.Join(dir, "service-account.json")
	apiKeyPath := filepath.Join(dir, "api-key.txt")
	promptPath := filepath.Join(dir, "prompt.txt")
	configPath := filepath.Join(dir, "app.yaml")

	if err := os.WriteFile(serviceAccountPath, []byte("{\"type\":\"service_account\"}"), 0o600); err != nil {
		t.Fatalf("WriteFile() error = %v", err)
	}
	if err := os.WriteFile(apiKeyPath, []byte("secret-key\n"), 0o600); err != nil {
		t.Fatalf("WriteFile() error = %v", err)
	}
	if err := os.WriteFile(promptPath, []byte("prompt body\n"), 0o600); err != nil {
		t.Fatalf("WriteFile() error = %v", err)
	}
	configContent := `
app:
  port: "9090"
sheets:
  spreadsheet_id: sheet-123
  service_account_file: ` + serviceAccountPath + `
ai:
  provider: gemini
  api_key_file: ` + apiKeyPath + `
  model: gemini-2.0-flash
  prompt_file: ` + promptPath + `
`
	if err := os.WriteFile(configPath, []byte(configContent), 0o600); err != nil {
		t.Fatalf("WriteFile() error = %v", err)
	}

	t.Setenv("APP_CONFIG_FILE", configPath)

	cfg, err := config.Load()
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}

	if cfg.App.Port != "9090" {
		t.Fatalf("expected config file port, got %q", cfg.App.Port)
	}
	if cfg.Sheets.ServiceAccountJSON == "" {
		t.Fatal("expected sheets service account json to be loaded from file")
	}
	if cfg.AI.APIKey != "secret-key" {
		t.Fatalf("expected ai key from file, got %q", cfg.AI.APIKey)
	}
	if cfg.AI.Prompt != "prompt body" {
		t.Fatalf("expected prompt from file, got %q", cfg.AI.Prompt)
	}
}

func TestEnvOverridesConfigFile(t *testing.T) {
	dir := t.TempDir()
	configPath := filepath.Join(dir, "app.yaml")

	if err := os.WriteFile(configPath, []byte("app:\n  port: \"9090\"\n"), 0o600); err != nil {
		t.Fatalf("WriteFile() error = %v", err)
	}

	t.Setenv("APP_CONFIG_FILE", configPath)
	t.Setenv("APP_PORT", "9191")

	cfg, err := config.Load()
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}

	if cfg.App.Port != "9191" {
		t.Fatalf("expected env override port, got %q", cfg.App.Port)
	}
}

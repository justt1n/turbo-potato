package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"
)

type Config struct {
	App    AppConfig    `yaml:"app"`
	Sheets SheetsConfig `yaml:"sheets"`
	AI     AIConfig     `yaml:"ai"`
}

type AppConfig struct {
	Env      string `yaml:"env"`
	Port     string `yaml:"port"`
	Timezone string `yaml:"timezone"`
}

type SheetsConfig struct {
	SpreadsheetID      string `yaml:"spreadsheet_id"`
	ServiceAccountJSON string `yaml:"service_account_json"`
	ServiceAccountFile string `yaml:"service_account_file"`
}

type AIConfig struct {
	Provider                string `yaml:"provider"`
	BaseURL                 string `yaml:"base_url"`
	APIKey                  string `yaml:"api_key"`
	APIKeyFile              string `yaml:"api_key_file"`
	Model                   string `yaml:"model"`
	Prompt                  string `yaml:"prompt"`
	PromptFile              string `yaml:"prompt_file"`
	DailyReportPrompt       string `yaml:"daily_report_prompt"`
	DailyReportPromptFile   string `yaml:"daily_report_prompt_file"`
	MonthlyReportPrompt     string `yaml:"monthly_report_prompt"`
	MonthlyReportPromptFile string `yaml:"monthly_report_prompt_file"`
}

func Load() (Config, error) {
	cfg := defaultConfig()

	if configFile := strings.TrimSpace(os.Getenv("APP_CONFIG_FILE")); configFile != "" {
		fileCfg, err := loadFromFile(configFile)
		if err != nil {
			return Config{}, err
		}
		cfg = mergeConfig(cfg, fileCfg)
	}

	applyEnvOverrides(&cfg)

	if cfg.App.Port == "" {
		return Config{}, fmt.Errorf("app.port is required")
	}

	if cfg.Sheets.ServiceAccountJSON == "" && cfg.Sheets.ServiceAccountFile != "" {
		content, err := readFile(cfg.Sheets.ServiceAccountFile)
		if err != nil {
			return Config{}, fmt.Errorf("read sheets.service_account_file: %w", err)
		}
		cfg.Sheets.ServiceAccountJSON = content
	}

	if cfg.AI.APIKey == "" && cfg.AI.APIKeyFile != "" {
		content, err := readFile(cfg.AI.APIKeyFile)
		if err != nil {
			return Config{}, fmt.Errorf("read ai.api_key_file: %w", err)
		}
		cfg.AI.APIKey = strings.TrimSpace(content)
	}

	if cfg.AI.Prompt == "" && cfg.AI.PromptFile != "" {
		content, err := readFile(cfg.AI.PromptFile)
		if err != nil {
			return Config{}, fmt.Errorf("read ai.prompt_file: %w", err)
		}
		cfg.AI.Prompt = strings.TrimSpace(content)
	}

	if cfg.AI.DailyReportPrompt == "" && cfg.AI.DailyReportPromptFile != "" {
		content, err := readFile(cfg.AI.DailyReportPromptFile)
		if err != nil {
			return Config{}, fmt.Errorf("read ai.daily_report_prompt_file: %w", err)
		}
		cfg.AI.DailyReportPrompt = strings.TrimSpace(content)
	}

	if cfg.AI.MonthlyReportPrompt == "" && cfg.AI.MonthlyReportPromptFile != "" {
		content, err := readFile(cfg.AI.MonthlyReportPromptFile)
		if err != nil {
			return Config{}, fmt.Errorf("read ai.monthly_report_prompt_file: %w", err)
		}
		cfg.AI.MonthlyReportPrompt = strings.TrimSpace(content)
	}

	return cfg, nil
}

func (c Config) UseGoogleSheets() bool {
	return c.Sheets.SpreadsheetID != "" && c.Sheets.ServiceAccountJSON != ""
}

func defaultConfig() Config {
	return Config{
		App: AppConfig{
			Env:      "development",
			Port:     "8080",
			Timezone: "UTC",
		},
	}
}

func loadFromFile(path string) (Config, error) {
	content, err := os.ReadFile(filepath.Clean(path))
	if err != nil {
		return Config{}, fmt.Errorf("read config file: %w", err)
	}

	var cfg Config
	if err := yaml.Unmarshal(content, &cfg); err != nil {
		return Config{}, fmt.Errorf("parse config file: %w", err)
	}

	return cfg, nil
}

func mergeConfig(base, override Config) Config {
	if override.App.Env != "" {
		base.App.Env = override.App.Env
	}
	if override.App.Port != "" {
		base.App.Port = override.App.Port
	}
	if override.App.Timezone != "" {
		base.App.Timezone = override.App.Timezone
	}
	if override.Sheets.SpreadsheetID != "" {
		base.Sheets.SpreadsheetID = override.Sheets.SpreadsheetID
	}
	if override.Sheets.ServiceAccountJSON != "" {
		base.Sheets.ServiceAccountJSON = override.Sheets.ServiceAccountJSON
	}
	if override.Sheets.ServiceAccountFile != "" {
		base.Sheets.ServiceAccountFile = override.Sheets.ServiceAccountFile
	}
	if override.AI.Provider != "" {
		base.AI.Provider = override.AI.Provider
	}
	if override.AI.BaseURL != "" {
		base.AI.BaseURL = override.AI.BaseURL
	}
	if override.AI.APIKey != "" {
		base.AI.APIKey = override.AI.APIKey
	}
	if override.AI.APIKeyFile != "" {
		base.AI.APIKeyFile = override.AI.APIKeyFile
	}
	if override.AI.Model != "" {
		base.AI.Model = override.AI.Model
	}
	if override.AI.Prompt != "" {
		base.AI.Prompt = override.AI.Prompt
	}
	if override.AI.PromptFile != "" {
		base.AI.PromptFile = override.AI.PromptFile
	}
	if override.AI.DailyReportPrompt != "" {
		base.AI.DailyReportPrompt = override.AI.DailyReportPrompt
	}
	if override.AI.DailyReportPromptFile != "" {
		base.AI.DailyReportPromptFile = override.AI.DailyReportPromptFile
	}
	if override.AI.MonthlyReportPrompt != "" {
		base.AI.MonthlyReportPrompt = override.AI.MonthlyReportPrompt
	}
	if override.AI.MonthlyReportPromptFile != "" {
		base.AI.MonthlyReportPromptFile = override.AI.MonthlyReportPromptFile
	}

	return base
}

func applyEnvOverrides(cfg *Config) {
	cfg.App.Env = getEnv("APP_ENV", cfg.App.Env)
	cfg.App.Port = getEnv("APP_PORT", cfg.App.Port)
	cfg.App.Timezone = getEnv("APP_TIMEZONE", cfg.App.Timezone)

	cfg.Sheets.SpreadsheetID = getEnv("GOOGLE_SHEETS_SPREADSHEET_ID", cfg.Sheets.SpreadsheetID)
	cfg.Sheets.ServiceAccountJSON = getEnv("GOOGLE_SERVICE_ACCOUNT_JSON", cfg.Sheets.ServiceAccountJSON)
	cfg.Sheets.ServiceAccountFile = getEnv("GOOGLE_SERVICE_ACCOUNT_FILE", cfg.Sheets.ServiceAccountFile)

	cfg.AI.Provider = getEnv("AI_PROVIDER", cfg.AI.Provider)
	cfg.AI.BaseURL = getEnv("AI_BASE_URL", cfg.AI.BaseURL)
	cfg.AI.APIKey = getEnv("AI_API_KEY", cfg.AI.APIKey)
	cfg.AI.APIKeyFile = getEnv("AI_API_KEY_FILE", cfg.AI.APIKeyFile)
	cfg.AI.Model = getEnv("AI_MODEL", cfg.AI.Model)
	cfg.AI.Prompt = getEnv("AI_PROMPT", cfg.AI.Prompt)
	cfg.AI.PromptFile = getEnv("AI_PROMPT_FILE", cfg.AI.PromptFile)
	cfg.AI.DailyReportPrompt = getEnv("AI_DAILY_REPORT_PROMPT", cfg.AI.DailyReportPrompt)
	cfg.AI.DailyReportPromptFile = getEnv("AI_DAILY_REPORT_PROMPT_FILE", cfg.AI.DailyReportPromptFile)
	cfg.AI.MonthlyReportPrompt = getEnv("AI_MONTHLY_REPORT_PROMPT", cfg.AI.MonthlyReportPrompt)
	cfg.AI.MonthlyReportPromptFile = getEnv("AI_MONTHLY_REPORT_PROMPT_FILE", cfg.AI.MonthlyReportPromptFile)
}

func readFile(path string) (string, error) {
	content, err := os.ReadFile(filepath.Clean(path))
	if err != nil {
		return "", err
	}

	return string(content), nil
}

func getEnv(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}

	return fallback
}

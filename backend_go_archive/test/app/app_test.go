package app_test

import (
	"testing"

	"github.com/admin/turbo-potato/backend/internal/app"
	"github.com/admin/turbo-potato/backend/internal/config"
)

func TestNewUsesMemoryFallbackWithoutSheetsConfig(t *testing.T) {
	application, err := app.New(config.Config{
		App: config.AppConfig{
			Port: "8080",
		},
	})
	if err != nil {
		t.Fatalf("app.New() error = %v", err)
	}

	if application == nil {
		t.Fatal("expected app instance")
	}
}

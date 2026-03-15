package sheets

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/admin/turbo-potato/backend/internal/domain/reports"
)

const reportsRange = "Reports!A:L"

type GoogleReportsRepository struct {
	client        ValuesAPI
	spreadsheetID string
}

func NewGoogleReportsRepository(client ValuesAPI, spreadsheetID string) *GoogleReportsRepository {
	return &GoogleReportsRepository{
		client:        client,
		spreadsheetID: spreadsheetID,
	}
}

func (r *GoogleReportsRepository) Save(ctx context.Context, report reports.Report) (reports.Report, error) {
	row := [][]interface{}{{
		report.ID,
		string(report.Kind),
		report.PeriodKey,
		report.Title,
		report.Summary,
		report.Body,
		report.Verdict,
		report.Status,
		report.Model,
		report.PromptSource,
		report.Trigger,
		report.CreatedAt.UTC().Format(time.RFC3339),
	}}
	if err := r.client.Append(ctx, r.spreadsheetID, reportsRange, row); err != nil {
		return reports.Report{}, err
	}
	return report, nil
}

func (r *GoogleReportsRepository) FindByKindAndPeriod(ctx context.Context, kind reports.Kind, periodKey string) (*reports.Report, error) {
	items, err := r.list(ctx)
	if err != nil {
		return nil, err
	}
	for index := len(items) - 1; index >= 0; index-- {
		if items[index].Kind == kind && items[index].PeriodKey == periodKey {
			item := items[index]
			return &item, nil
		}
	}
	return nil, nil
}

func (r *GoogleReportsRepository) LatestByKind(ctx context.Context, kind reports.Kind) (*reports.Report, error) {
	items, err := r.list(ctx)
	if err != nil {
		return nil, err
	}
	for index := len(items) - 1; index >= 0; index-- {
		if items[index].Kind == kind {
			item := items[index]
			return &item, nil
		}
	}
	return nil, nil
}

func (r *GoogleReportsRepository) list(ctx context.Context) ([]reports.Report, error) {
	rows, err := r.client.Get(ctx, r.spreadsheetID, "Reports!A2:L")
	if err != nil {
		return nil, err
	}

	items := make([]reports.Report, 0, len(rows))
	for _, row := range rows {
		if len(row) == 0 {
			continue
		}
		item, err := reportFromRow(row)
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, nil
}

type MemoryReportsRepository struct {
	mu    sync.Mutex
	items []reports.Report
}

func NewMemoryReportsRepository() *MemoryReportsRepository {
	return &MemoryReportsRepository{
		items: make([]reports.Report, 0),
	}
}

func (r *MemoryReportsRepository) Save(_ context.Context, report reports.Report) (reports.Report, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.items = append(r.items, report)
	return report, nil
}

func (r *MemoryReportsRepository) FindByKindAndPeriod(_ context.Context, kind reports.Kind, periodKey string) (*reports.Report, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	for index := len(r.items) - 1; index >= 0; index-- {
		if r.items[index].Kind == kind && r.items[index].PeriodKey == periodKey {
			item := r.items[index]
			return &item, nil
		}
	}
	return nil, nil
}

func (r *MemoryReportsRepository) LatestByKind(_ context.Context, kind reports.Kind) (*reports.Report, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	for index := len(r.items) - 1; index >= 0; index-- {
		if r.items[index].Kind == kind {
			item := r.items[index]
			return &item, nil
		}
	}
	return nil, nil
}

func reportFromRow(row []interface{}) (reports.Report, error) {
	if len(row) < 12 {
		return reports.Report{}, fmt.Errorf("report row has %d columns, expected at least 12", len(row))
	}

	createdAt, err := time.Parse(time.RFC3339, stringify(row[11]))
	if err != nil {
		return reports.Report{}, fmt.Errorf("parse report createdAt: %w", err)
	}

	return reports.Report{
		ID:           stringify(row[0]),
		Kind:         reports.Kind(stringify(row[1])),
		PeriodKey:    stringify(row[2]),
		Title:        stringify(row[3]),
		Summary:      stringify(row[4]),
		Body:         stringify(row[5]),
		Verdict:      stringify(row[6]),
		Status:       stringify(row[7]),
		Model:        stringify(row[8]),
		PromptSource: stringify(row[9]),
		Trigger:      stringify(row[10]),
		CreatedAt:    createdAt,
	}, nil
}

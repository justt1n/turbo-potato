package sheets

import (
	"context"
	"fmt"
	"slices"
)

type Bootstrapper interface {
	Bootstrap(ctx context.Context) error
}

type SpreadsheetBootstrapper struct {
	admin         SpreadsheetAdminAPI
	values        ValuesAPI
	spreadsheetID string
}

type SheetSpec struct {
	Title   string
	Headers []interface{}
}

func NewSpreadsheetBootstrapper(admin SpreadsheetAdminAPI, values ValuesAPI, spreadsheetID string) *SpreadsheetBootstrapper {
	return &SpreadsheetBootstrapper{
		admin:         admin,
		values:        values,
		spreadsheetID: spreadsheetID,
	}
}

func (b *SpreadsheetBootstrapper) Bootstrap(ctx context.Context) error {
	existingTitles, err := b.admin.GetSheetTitles(ctx, b.spreadsheetID)
	if err != nil {
		return err
	}

	missingTitles := make([]string, 0)
	for _, spec := range requiredSheets() {
		if !slices.Contains(existingTitles, spec.Title) {
			missingTitles = append(missingTitles, spec.Title)
		}
	}

	if err := b.admin.AddSheets(ctx, b.spreadsheetID, missingTitles); err != nil {
		return err
	}

	for _, spec := range requiredSheets() {
		readRange := fmt.Sprintf("%s!1:1", spec.Title)
		values, err := b.values.Get(ctx, b.spreadsheetID, readRange)
		if err != nil {
			return err
		}

		if headersMatch(values, spec.Headers) {
			continue
		}

		updateRange := fmt.Sprintf("%s!A1", spec.Title)
		if err := b.values.Update(ctx, b.spreadsheetID, updateRange, [][]interface{}{spec.Headers}); err != nil {
			return err
		}
	}

	return nil
}

type noopBootstrapper struct{}

func NewNoopBootstrapper() Bootstrapper {
	return noopBootstrapper{}
}

func (noopBootstrapper) Bootstrap(context.Context) error {
	return nil
}

func requiredSheets() []SheetSpec {
	return []SheetSpec{
		{
			Title: "Transactions",
			Headers: []interface{}{
				"Tx_ID", "Occurred_At", "Type", "Amount", "Currency", "Jar_Code", "Goal_Name",
				"Account_Name", "Is_Fixed", "Note", "Source", "Status", "Created_At", "Updated_At",
			},
		},
		{
			Title:   "Goals",
			Headers: []interface{}{"Goal_Name", "Target_Amount", "Start_Date", "Target_Date", "Status"},
		},
		{
			Title:   "NW_Snapshots",
			Headers: []interface{}{"Month_Year", "Total_NW", "Liquid_NW", "Created_At"},
		},
		{
			Title:   "Fixed_Cost_Rules",
			Headers: []interface{}{"Rule_Name", "Expected_Amount", "Window_Start_Day", "Window_End_Day", "Linked_Jar_Code", "Is_Active"},
		},
		{
			Title:   "Audit_Log",
			Headers: []interface{}{"Audit_ID", "Tx_ID", "Action", "Previous_Value", "New_Value", "Reason", "Actor", "Created_At"},
		},
		{
			Title:   "Parsed_Receipts",
			Headers: []interface{}{"Receipt_ID", "Tx_ID", "Raw_Input", "Regex_Amount", "Regex_Tags", "LLM_Model", "LLM_Output_JSON", "Validation_Notes", "Confidence", "Prompt_Source", "Created_At"},
		},
		{
			Title:   "Settings",
			Headers: []interface{}{"Key", "Value", "Description"},
		},
		{
			Title:   "Reports",
			Headers: []interface{}{"Report_ID", "Kind", "Period_Key", "Title", "Summary", "Body", "Verdict", "Status", "Model", "Prompt_Source", "Trigger", "Created_At"},
		},
	}
}

func headersMatch(rows [][]interface{}, expected []interface{}) bool {
	if len(rows) == 0 || len(rows[0]) < len(expected) {
		return false
	}

	for index, value := range expected {
		if stringify(rows[0][index]) != stringify(value) {
			return false
		}
	}

	return true
}

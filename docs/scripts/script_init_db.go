package main

import (
	"context"
	"fmt"
	"log"

	"google.golang.org/api/option"
	"google.golang.org/api/sheets/v4"
)

// Khởi tạo Google Sheets Service (Giả định bạn đã có file credentials.json từ Google Cloud)
func InitSheetsService() *sheets.Service {
	ctx := context.Background()
	srv, err := sheets.NewService(ctx, option.WithCredentialsFile("credentials.json"))
	if err != nil {
		log.Fatalf("Không thể khởi tạo Sheets client: %v", err)
	}
	return srv
}

func SetupDatabaseSchema(spreadsheetId string) {
	srv := InitSheetsService()

	// 1. Tạo các Sheets (Tabs) mới
	requests := []*sheets.Request{
		{AddSheet: &sheets.AddSheetRequest{Properties: &sheets.SheetProperties{Title: "Transactions"}}},
		{AddSheet: &sheets.AddSheetRequest{Properties: &sheets.SheetProperties{Title: "NW_Snapshots"}}},
		{AddSheet: &sheets.AddSheetRequest{Properties: &sheets.SheetProperties{Title: "Goals"}}},
		{AddSheet: &sheets.AddSheetRequest{Properties: &sheets.SheetProperties{Title: "Metrics_Engine"}}},
	}

	batchReq := &sheets.BatchUpdateSpreadsheetRequest{Requests: requests}
	_, err := srv.Spreadsheets.BatchUpdate(spreadsheetId, batchReq).Do()
	if err != nil {
		log.Printf("Lưu ý: Sheet có thể đã tồn tại (%v). Tiếp tục format headers...", err)
	}

	// 2. Setup Headers và Data thô cho các cột (Sử dụng ValueRange)
	// Setup sheet Transactions
	txHeaders := &sheets.ValueRange{
		Values: [][]interface{}{{"Tx_ID", "Date", "Type", "Amount", "Jar", "Is_Fixed", "Note"}},
	}
	srv.Spreadsheets.Values.Update(spreadsheetId, "Transactions!A1:G1", txHeaders).ValueInputOption("RAW").Do()

	// Setup sheet Goals
	goalHeaders := &sheets.ValueRange{
		Values: [][]interface{}{{"Goal_Name", "Target_Amount", "Start_Date"}},
	}
	srv.Spreadsheets.Values.Update(spreadsheetId, "Goals!A1:C1", goalHeaders).ValueInputOption("RAW").Do()

	// 3. Inject các hàm Toán học (Formulas) phức tạp vào sheet Metrics_Engine
	metricsFormulas := &sheets.ValueRange{
		Values: [][]interface{}{
			// Headers
			{"Budget_Var", "Day", "Days_Total", "Var_Spent", "STS_Daily"},
			// Giá trị và Hàm tính toán Hạn mức STS (Đã định nghĩa ở phần trước)
			{10000000, "=DAY(TODAY())", "=DAY(EOMONTH(TODAY(), 0))", 
			"=SUMIFS(Transactions!D:D, Transactions!C:C, \"OUT\", Transactions!F:F, FALSE, Transactions!B:B, \">=\"&EOMONTH(TODAY(), -1)+1)", 
			"=IF(C2-B2+1 > 0, (A2 - D2) / (C2 - B2 + 1), 0)"},
		},
	}
	// Dùng USER_ENTERED để Google Sheets hiểu đây là công thức tính toán (Formulas) chứ không phải text thô
	_, err = srv.Spreadsheets.Values.Update(spreadsheetId, "Metrics_Engine!A1:E2", metricsFormulas).ValueInputOption("USER_ENTERED").Do()
	if err != nil {
		log.Fatalf("Lỗi khi inject Formulas: %v", err)
	}

	fmt.Println("✅ Setup Database Schema và Formulas thành công!")
}
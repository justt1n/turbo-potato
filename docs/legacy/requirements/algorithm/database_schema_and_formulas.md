# Cấu trúc Database & Hàm Tính Toán Cốt Lõi (Google Sheets Schema)

**Triết lý thiết kế:**
1. **Raw Data (Dữ liệu thô):** Nơi Backend Go liên tục `INSERT` dữ liệu từ tin nhắn chat. Không chứa hàm tính toán để tránh lỗi.
2. **Aggregated Data (Dữ liệu tổng hợp):** Nơi Google Sheets tự động dùng `QUERY` và `SUMIFS` để nhào nặn data thô thành các Metrics phục vụ cho 5 Thuật toán. Backend Go chỉ việc `GET` dữ liệu từ đây.

---

## PHẦN 1: CÁC BẢNG DỮ LIỆU THÔ (RAW DATA SHEETS)

### 1. Sheet `Transactions` (Nhật ký Giao dịch)
Đây là trái tim của hệ thống. Mọi luồng tiền đều chảy qua đây.

| Cột | Tên Cột | Kiểu Dữ Liệu | Ví dụ | Giải thích |
| :--- | :--- | :--- | :--- | :--- |
| A | `Tx_ID` | String | `TX-1710432000` | ID tự sinh từ Backend (Timestamp). |
| B | `Date` | Date | `15/03/2026` | Ngày phát sinh giao dịch. |
| C | `Type` | Enum | `OUT` | `IN` (Thu), `OUT` (Chi), `TRANSFER` (Chuyển hũ). |
| D | `Amount` | Number | `500000` | Số tiền (VNĐ). |
| E | `Jar` | String | `ThietYeu` | Hũ ngân sách hoặc Tên Mục tiêu. |
| F | `Is_Fixed` | Boolean | `FALSE` | **Quan trọng:** `TRUE` = Định phí (Tiền nhà), `FALSE` = Biến phí (Ăn uống). |
| G | `Note` | String | `Ăn tối nhà hàng` | Ghi chú (Parse từ Chat). |

### 2. Sheet `NW_Snapshots` (Lịch sử Tài sản Ròng)
Chốt sổ vào 23:59 ngày cuối cùng mỗi tháng để phục vụ thuật toán TAR.

| Cột | Tên Cột | Kiểu Dữ Liệu | Ví dụ | Giải thích |
| :--- | :--- | :--- | :--- | :--- |
| A | `Month_Year` | String | `02/2026` | Tháng chốt sổ. |
| B | `Total_NW` | Number | `150000000` | Tổng tài sản ròng chốt tại thời điểm đó. |
| C | `Liquid_NW` | Number | `120000000` | Tài sản thanh khoản (Tiền mặt + Vàng/Cổ phiếu) phục vụ tính Runway. |

### 3. Sheet `Goals` (Mục tiêu Tích lũy)
| Cột | Tên Cột | Kiểu Dữ Liệu | Ví dụ | Giải thích |
| :--- | :--- | :--- | :--- | :--- |
| A | `Goal_Name` | String | `Mua xe SH` | Tên mục tiêu. |
| B | `Target_Amount`| Number | `100000000` | Số tiền đích. |
| C | `Start_Date` | Date | `01/01/2026` | Ngày bắt đầu gom tiền. |

---

## PHẦN 2: BẢNG TÍNH TOÁN CHỈ SỐ (ANALYTICS & ENGINE SHEETS)

Đây là Sheet `Metrics_Engine`. Nó không dành cho việc nhập liệu, nó chỉ chứa các ô chứa hàm tính toán (Formulas) để tổng hợp ra 5 chỉ số cốt lõi. Backend Go sẽ gọi API đọc vùng dữ liệu (Range) của Sheet này để trả về Dashboard.

*(Lưu ý: Các hàm dưới đây sử dụng cú pháp chuẩn của Google Sheets).*

### Metric 1: Tính toán Biến phí & Hạn mức STS (Thuật toán 2)
**Biến số cần setup ở góc Sheet:**
* `B1` (Ngân sách Biến phí tháng này): `10000000` (10 triệu)
* `B2` (Ngày hiện tại trong tháng): `=DAY(TODAY())`
* `B3` (Tổng số ngày của tháng): `=DAY(EOMONTH(TODAY(), 0))`

**Công thức tính toán:**
1. **Đã tiêu Biến phí (Variable Spent):** Tính tổng các giao dịch `OUT` trong tháng hiện tại và có `Is_Fixed = FALSE`.
   `B4 =SUMIFS(Transactions!D:D, Transactions!C:C, "OUT", Transactions!F:F, FALSE, Transactions!B:B, ">="&EOMONTH(TODAY(), -1)+1, Transactions!B:B, "<="&EOMONTH(TODAY(), 0))`

2. **Chỉ số STS (Safe-To-Spend hằng ngày):** (Ngân sách - Đã tiêu) / Số ngày còn lại.
   `B5 =IF(B3-B2+1 > 0, (B1 - B4) / (B3 - B2 + 1), 0)`
   *Kết quả trả về sẽ là số tiền bạn được phép tiêu hôm nay. Backend chỉ việc đọc ô `B5`.*

### Metric 2: Z-Score Pacing (Thuật toán 1 - Cảnh báo Bất thường)
Để tính Z-Score, chúng ta cần Trung bình ($\mu$) và Độ lệch chuẩn ($\sigma$) của Biến phí theo ngày trong lịch sử.
*Thay vì làm phức tạp, ta dùng hàm `AVERAGE` của 90 ngày qua làm chuẩn.*

1. **Trung bình Biến phí/Ngày (Historical Daily Mean - $\mu$):**
   `C1 =SUMIFS(Transactions!D:D, Transactions!C:C, "OUT", Transactions!F:F, FALSE, Transactions!B:B, ">="&TODAY()-90, Transactions!B:B, "<"&TODAY()) / 90`
2. **Độ lệch chuẩn (Standard Deviation - $\sigma$):** (Cần tạo một Pivot Table ẩn tính tổng chi theo ngày, giả sử cột đó là `Daily_Agg!B:B`).
   `C2 =STDEV(Daily_Agg!B:B)`
3. **Biến phí Hôm nay (Today's Variable Spend - $X$):**
   `C3 =SUMIFS(Transactions!D:D, Transactions!B:B, TODAY(), Transactions!F:F, FALSE)`
4. **Z-Score Hôm nay:**
   `C4 =IF(C2=0, 0, (C3 - C1) / C2)`
   *Backend đọc ô `C4`. Nếu > 1.96, kích hoạt báo động gửi tin nhắn Chat.*

### Metric 3: POL - Personal Operating Leverage (Thuật toán 3)
Đo lường cấu trúc rủi ro: Định phí / Thu nhập trung bình.

1. **Tổng Định phí Tháng này (Total Fixed Costs):**
   `D1 =SUMIFS(Transactions!D:D, Transactions!C:C, "OUT", Transactions!F:F, TRUE, Transactions!B:B, ">="&EOMONTH(TODAY(), -1)+1)`
2. **Thu nhập Trung bình 3 tháng (Avg Income):**
   `D2 =SUMIFS(Transactions!D:D, Transactions!C:C, "IN", Transactions!B:B, ">="&EDATE(EOMONTH(TODAY(),-1)+1, -3)) / 3`
3. **Chỉ số POL (%):**
   `D3 =IF(D2>0, D1 / D2, 0)`

### Metric 4: TAR - True Accumulation Rate (Thuật toán 4)
So sánh tốc độ phình to của Tài sản ròng so với Thu nhập tháng này.

1. **Tài sản Ròng Hiện Tại (Current NW):** (Giả sử bạn cập nhật giá trị các ví ở sheet `Accounts_NW`).
   `E1 =SUM(Accounts_NW!B:B)`
2. **Tài sản Ròng Tháng Trước (Last Month NW):** (Lấy từ bảng Snapshots).
   `E2 =VLOOKUP(TEXT(EOMONTH(TODAY(), -1), "MM/YYYY"), NW_Snapshots!A:B, 2, FALSE)`
3. **Thu nhập Tháng này (This Month Income):**
   `E3 =SUMIFS(Transactions!D:D, Transactions!C:C, "IN", Transactions!B:B, ">="&EOMONTH(TODAY(), -1)+1)`
4. **Chỉ số TAR (%):**
   `E4 =IF(E3>0, (E1 - E2) / E3, 0)`

### Metric 5: Goal Velocity & ETA (Thuật toán 5)
Tính toán thời gian hoàn thành cho 1 mục tiêu cụ thể (Ví dụ: Đọc dòng 2 của sheet `Goals` - Mua xe).

1. **Target (Mục tiêu):** `F1 =Goals!B2`
2. **Current (Đã có):** Tổng tiền chuyển vào hũ `Mua xe`.
   `F2 =SUMIFS(Transactions!D:D, Transactions!C:C, "TRANSFER", Transactions!E:E, Goals!A2)`
3. **Velocity (Vận tốc - Trung bình 3 tháng qua):**
   `F3 =SUMIFS(Transactions!D:D, Transactions!C:C, "TRANSFER", Transactions!E:E, Goals!A2, Transactions!B:B, ">="&EDATE(TODAY(), -3)) / 3`
4. **ETA (Thời gian dự kiến hoàn thành):**
   `F4 =IF(F3>0, EDATE(TODAY(), ROUNDUP((F1-F2)/F3, 0)), "Never")`
   *Hàm `EDATE` sẽ cộng số tháng còn lại vào ngày hôm nay để trả ra chính xác Tháng/Năm bạn mua được xe.*
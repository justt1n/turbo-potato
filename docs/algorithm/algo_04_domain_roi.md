# Thuật toán 4: Domain ROI (Tỷ suất Sinh lời của Thời gian & Tiền bạc)

**Mục tiêu:** Định lượng chính xác giá trị sinh lời của từng giờ đồng hồ bạn bỏ ra cho các mảng khác nhau (đặc biệt là `#sidehustle` hoặc `#master`). Giúp bạn thoát khỏi "bẫy bận rộn" (làm nhiều nhưng không hiệu quả).
**Thang đo:** ROTI (Return on Time Invested - VNĐ/Giờ) và ROI Tài chính (%).

## 1. Cơ sở Khoa học (The Science)
Thuật toán này được thiết kế để chống lại 2 cái bẫy tâm lý kinh điển trong Kinh tế học Hành vi:
* **Ngụy biện Chi phí Chìm (Sunk Cost Fallacy - Kahneman & Tversky):** Con người có xu hướng tiếp tục đâm đầu vào một dự án thất bại chỉ vì họ đã lỡ đầu tư quá nhiều thời gian/tiền bạc vào đó trước đây. Hệ thống ROI sẽ dùng những con số tàn nhẫn để cắt đứt sự luyến tiếc này.
* **Nguyên lý Pareto (Quy tắc 80/20):** 80% kết quả thường đến từ 20% nỗ lực. Nếu bạn đo lường được ROTI của từng dự án nhỏ trong mảng `#sidehustle`, bạn sẽ biết đâu là "con gà đẻ trứng vàng" (20% đó) để dồn lực, và đâu là thứ đang hút máu thời gian của bạn.
* **Lý thuyết Vốn nhân lực (Human Capital - Gary Becker):** Thời gian của bạn có một "Đơn giá cơ sở" (Base Hourly Rate). Bất kỳ việc làm thêm nào sinh ra đơn giá thấp hơn mức cơ sở này (mà không mang lại giá trị kiến thức) đều là một khoản đầu tư lỗ.

## 2. Ứng dụng Thực tiễn (Real-life Translation)
Giả sử bạn đang có 2 dự án làm thêm:
* **Dự án A:** Bạn mất 50 giờ trong tháng để làm, thu về 2.000.000 VNĐ.
  -> *Thuật toán tính:* ROTI = 40.000 VNĐ/Giờ. (Thấp hơn cả đi chạy xe ôm công nghệ).
* **Dự án B:** Bạn chỉ tốn 10 giờ setup ban đầu, thu về 3.000.000 VNĐ.
  -> *Thuật toán tính:* ROTI = 300.000 VNĐ/Giờ.

**Phản ứng của Hệ thống:** Cuối tháng, Bot sẽ chỉ ra sự chênh lệch này. Nó sẽ khuyên bạn mạnh dạn "khai tử" Dự án A để lấy 50 giờ đó đắp vào Dự án B hoặc dùng để nghỉ ngơi (tăng Life Battery), thay vì tự huyễn hoặc bản thân là "mình đang rất nỗ lực chăm chỉ".

## 3. Logic Thuật toán & Tích hợp Hệ thống (Go Backend)

**A. Các biến số đầu vào (Inputs):**
* `Base_Hourly_Rate`: Mức lương giờ chuẩn của bạn (VD: Lương chính 15tr / 160 giờ = 93.000 VNĐ/Giờ). Đây là Baseline.
* `Total_Hours_Invested`: Tổng số giờ dự kiến (`Estimated_Hours`) từ các task có gắn tag tương ứng (VD: `#sidehustle`). Tính tổng bằng Google Sheets.
* `Total_Expense`: Số tiền chi ra cho mảng đó (VD: Tiền chạy quảng cáo, mua tool).
* `Total_Income`: Thu nhập thực tế mang lại từ mảng đó (`/income 500k #sidehustle`).

**B. Công thức tính toán (Chạy vào ngày cuối tháng):**
1. **Lợi nhuận ròng (Net Profit):** `Net_Profit = Total_Income - Total_Expense`
2. **ROI Tài chính (%):** `Financial_ROI = (Net_Profit / Total_Expense) * 100` *(Tính xem bỏ 1 đồng vốn thu được mấy đồng lời)*.
3. **ROTI (Hiệu suất Thời gian):** `ROTI = Net_Profit / Total_Hours_Invested` *(Tính xem 1 giờ công đáng giá bao nhiêu tiền)*.

**C. Phân tích & Đánh giá (Evaluation):**
Hệ thống sẽ so sánh ROTI của mảng đó với `Base_Hourly_Rate`:
* `ROTI < Base_Hourly_Rate`: Báo động (Làm thêm mà bèo bọt hơn làm chính).
* `ROTI >= Base_Hourly_Rate * 1.5`: Tốt (Đáng để đầu tư thêm thời gian).
* `ROTI >= Base_Hourly_Rate * 3`: Xuất sắc (Scale up ngay lập tức).

*(Lưu ý: Với mảng `#master` (Học tập), ROI không tính bằng tiền ngay lập tức, mà tính bằng Tỷ lệ Hoàn thành Khóa học / Số giờ. Hệ thống sẽ có logic ngoại lệ cho các tag phi lợi nhuận này).*

## 4. Kịch bản Kích hoạt (Triggers & Actions)

Thuật toán này chủ yếu kích hoạt vào kỳ **Đánh giá Cuối tháng (Monthly Review)**.

| Phân tích ROTI | Phản ứng của Bot (Google Chat) |
| :--- | :--- |
| **ROTI < Base Rate (Lỗ thời gian)** | *"📊 Báo cáo Tháng: Mảng #sidehustle tháng này ngốn của sếp 40 giờ nhưng chỉ tạo ra 30k/giờ. Tỷ suất này đang phá hủy Vốn nhân lực của sếp. Gợi ý: Tạm ngưng dự án này tháng sau để dồn sức học #master."* |
| **ROTI Cao (Win)** | *"📈 Đỉnh chóp! Dự án #sidehustle tháng này mang lại ROTI 450k/giờ. Đây là con gà đẻ trứng vàng. Tháng tới hãy thử giảm bớt việc #work để ưu tiên đẩy mạnh mảng này nhé!"* |
| **Chi phí ẩn cao (Lỗ tài chính)** | *"⚠️ Cảnh báo ROI: Sếp thu được 5 củ từ việc làm thêm, nhưng lại vung 4 củ để mua phần mềm và chạy Ads (ROI tài chính chỉ đạt 25%). Làm nông dân cày chay thôi sếp, cẩn thận làm bù lỗ!"* |
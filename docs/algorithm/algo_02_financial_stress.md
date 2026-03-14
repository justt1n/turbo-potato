# Thuật toán 2: Financial Stress Score (Chỉ số Căng thẳng Tài chính / Tốc độ Đốt tiền)

**Mục tiêu:** Phát hiện sớm rủi ro thâm hụt ngân sách trước khi nó thực sự xảy ra bằng cách so sánh tốc độ tiêu tiền (Burn Rate) với tốc độ trôi qua của thời gian trong tháng.
**Thang đo:** Tỷ lệ phần trăm (%) Burn Rate Index. Mức lý tưởng là xoay quanh 100%.

## 1. Cơ sở Khoa học (The Science)
Thuật toán này được phát triển dựa trên 2 nền tảng của Kinh tế học Hành vi:
* **Kế toán Tâm lý (Mental Accounting - Richard Thaler):** Con người chia tiền vào các "ngăn kéo" (hũ/jars) khác nhau. Tuy nhiên, điểm mù của não bộ là chúng ta thường đánh giá sai lượng tiền còn lại trong từng ngăn kéo so với thời gian.
* **Định luật Parkinson & Vòng lặp Phản hồi (Feedback Loops):** "Chi tiêu luôn có xu hướng tăng lên để triệt tiêu hết thu nhập". Nếu bạn chỉ nhận báo cáo tài chính vào cuối tháng (phản hồi trễ), bạn không thể thay đổi hành vi của tháng đó nữa. Thuật toán này cung cấp *Phản hồi Thời gian thực (Real-time Feedback)* dựa trên "Tốc độ" thay vì "Số lượng".

## 2. Ứng dụng Thực tiễn (Real-life Translation)
Giả sử hũ "Thiết yếu" của bạn có ngân sách (hoặc Baseline 3 tháng) là 6.000.000 VNĐ.
* Hôm nay là ngày 10 của tháng (tức là tháng đã trôi qua 33%).
* Bạn kiểm tra số dư và thấy mình đã tiêu 3.000.000 VNĐ.
* **Tư duy thông thường:** "Mình vẫn còn tận 3 triệu, một nửa tiền cơ mà, thoải mái đi!".
* **Tư duy của Hệ thống:** Bạn đã tiêu mất 50% ngân sách trong khi thời gian mới trôi qua 33%. Tốc độ đốt tiền của bạn đang nhanh gấp 1.5 lần mức an toàn. Nếu tiếp tục tốc độ này, ngày 20 bạn sẽ sạch túi. Hệ thống sẽ phát cảnh báo Đỏ ngay lập tức.

## 3. Logic Thuật toán & Tích hợp Hệ thống (Go Backend)

**A. Các biến số đầu vào (Inputs):**
* `Day_Current`: Ngày hiện tại trong tháng.
* `Day_Total`: Tổng số ngày của tháng đó (28, 30 hoặc 31).
* `Jar_Baseline`: Mức chi tiêu trung bình 3 tháng gần nhất của hũ đó (Lấy từ Google Sheets `AVERAGEIFS`).
* `Jar_Spent`: Số tiền đã chi của hũ đó tính đến hiện tại trong tháng.

**B. Công thức tính toán (Burn Rate Index - BRI):**
* Tỷ lệ Thời gian: `Time_Ratio = Day_Current / Day_Total`
* Tỷ lệ Chi tiêu: `Spent_Ratio = Jar_Spent / Jar_Baseline`
* Chỉ số Đốt tiền: `BRI = (Spent_Ratio / Time_Ratio) * 100`

*(Ví dụ: Tháng có 30 ngày. Hôm nay ngày 15 -> Time_Ratio = 0.5. Ngân sách 10tr, đã tiêu 6tr -> Spent_Ratio = 0.6. BRI = (0.6 / 0.5) * 100 = 120%. Bạn đang tiêu lố 20% so với tốc độ chuẩn).*

**C. Phân loại Trạng thái Căng thẳng (Stress Levels):**
* `BRI <= 90%`: **Vùng Xanh (An toàn/Tiết kiệm).** Tốc độ tiêu chậm hơn thời gian.
* `90% < BRI <= 110%`: **Vùng Vàng (Cân bằng).** Đi đúng tiến độ.
* `BRI > 110%`: **Vùng Đỏ (Báo động/Stress).** Tốc độ đốt tiền quá nhanh.

## 4. Kịch bản Kích hoạt (Triggers & Actions)

Thuật toán này được chạy ngầm mỗi khi bạn gõ lệnh `/spend` hoặc chạy tự động vào Cronjob 8:00 PM hằng ngày.

| Trạng thái BRI | Phản ứng của Bot (Google Chat) |
| :--- | :--- |
| **BRI < 80% (Quá tiết kiệm)** | *(Cuối tuần)* "Tuần này sếp kiểm soát hũ Thiết yếu cực tốt (Burn Rate 75%). Pin cũng đang thấp, cho phép sếp trích 200k đi cafe chill #life cuối tuần nhé!" |
| **BRI ~ 100%** | "Đã ghi nhận khoản chi. Ngân sách đang đi đúng quỹ đạo (Burn Rate 101%)." |
| **BRI > 115% (Cảnh báo sớm)** | "⚠️ BÁO ĐỘNG TỐC ĐỘ: Mới đi được 1/3 tháng mà sếp đã bào hết 50% hũ Hưởng thụ (Burn Rate 150%). Từ giờ đến cuối tuần cấm la cà quán xá nhé!" |
| **BRI > 150% (Đóng băng)** | "🛑 TÀI CHÍNH BÁO ĐỘNG ĐỎ: Tốc độ đốt tiền của hũ này đang vượt ngưỡng an toàn nghiêm trọng. Bot tạm thời khóa các lệnh chi tiêu không thiết yếu để bảo vệ tài sản của sếp!" |
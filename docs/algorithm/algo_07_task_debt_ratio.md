# Thuật toán 7: Task Debt Ratio (Chỉ số Nợ Công việc & Mức độ Trì hoãn)

**Mục tiêu:** Đo lường sự thực tế trong việc lập kế hoạch hằng ngày. Ngăn chặn hiện tượng "Quả cầu tuyết" (Snowball effect) - khi các công việc bị trì hoãn dồn lại thành một núi nợ, gây ra sự tê liệt và căng thẳng tột độ.
**Thang đo:** Tỷ lệ phần trăm (%) giữa số lượng việc bị dời lịch (Rescheduled) trên tổng số việc đã lên kế hoạch trong ngày.

## 1. Cơ sở Khoa học (The Science)
Thuật toán này bắt thóp 2 hiện tượng tâm lý học kinh điển:
* **Ngụy biện Lập kế hoạch (Planning Fallacy - Daniel Kahneman):** Con người luôn có xu hướng đánh giá quá cao khả năng của mình và đánh giá quá thấp thời gian cần thiết để hoàn thành một công việc. Chúng ta lập kế hoạch cho "phiên bản lý tưởng nhất" của bản thân, chứ không phải phiên bản thực tế.
* **Hiệu ứng Zeigarnik (Zeigarnik Effect):** Não bộ ghi nhớ những việc *chưa hoàn thành* tốt hơn gấp nhiều lần những việc *đã làm xong*. Mỗi task bạn dời sang ngày mai sẽ treo lơ lửng trong tâm trí bạn như một ứng dụng chạy ngầm trên điện thoại, ngốn sạch RAM (Life Battery) của bạn dù bạn đang nghỉ ngơi.

## 2. Ứng dụng Thực tiễn (Real-life Translation)
* **Sáng Thứ 2:** Sếp hừng hực khí thế, dùng lệnh `/task` nhét 8 việc vào lịch hôm nay. 
* **Tối Thứ 2:** Sếp chỉ làm được 3 việc. 5 việc còn lại, sếp dùng lệnh `/reschedule` (hoặc sửa ngày trên Sheet) đẩy sang Thứ 3.
* **Sáng Thứ 3:** Sếp lại thêm 3 việc mới của ngày Thứ 3. Tổng cộng sếp có 8 việc (5 nợ cũ + 3 mới). Vòng lặp lặp lại, sếp lại nợ 6 việc sang Thứ 4.
* **Đánh giá của Hệ thống:** Sếp không hề lười (sếp vẫn làm 3 việc/ngày). Vấn đề là sếp lập kế hoạch quá viển vông. Chỉ số Nợ Công việc (Task Debt) đang phình to, gây ra stress không đáng có.

## 3. Logic Thuật toán & Tích hợp Hệ thống (Go Backend)

**A. Các biến số đầu vào (Inputs - Tính toán cuối mỗi ngày):**
* `Tasks_Planned`: Tổng số task có `Date` là ngày hôm nay.
* `Tasks_Done`: Số task được chuyển `Status` thành `DONE` trong ngày hôm nay.
* `Tasks_Rolled_Over`: Số task có `Date` là hôm nay nhưng bị người dùng đổi sang một ngày trong tương lai, hoặc để nguyên trạng thái `PENDING` khi ngày đã qua (Overdue).

**B. Công thức tính toán (Chạy vào Cronjob lúc 23:59 hằng ngày):**
* `TDR (Task Debt Ratio) = (Tasks_Rolled_Over / Tasks_Planned) * 100`

**C. Phân loại Cấp độ Nợ (Debt Levels):**
* `TDR <= 15%`: **Lý tưởng (Thực tế).** Kế hoạch sát với năng lực thực thi.
* `15% < TDR <= 30%`: **Chấp nhận được (Cần chú ý).** Có sự cố phát sinh khiến kế hoạch bị lệch nhẹ.
* `TDR > 30%`: **Báo động (Ngụy biện Lập kế hoạch).** Đang nhét quá nhiều việc vào một ngày.

## 4. Kịch bản Kích hoạt (Triggers & Actions)

Thuật toán này liên kết chặt chẽ với **Life Battery** (Nợ task càng nhiều, sáng hôm sau dậy điểm Life Battery khởi điểm càng thấp do áp lực tâm lý).

| Tỷ lệ Nợ (TDR) | Phản ứng của Bot (Google Chat) |
| :--- | :--- |
| **TDR > 40% (Đóng băng Task mới)** | *"🛑 LỆNH CẤM: Sếp đang mang một đống nợ từ hôm qua. TDR chạm mốc 50%. Bot từ chối nhận thêm task mới cho ngày hôm nay. Đề nghị sếp dọn sạch nợ cũ trước khi đẻ thêm việc!"* |
| **20% < TDR <= 40% (Cảnh báo Kế hoạch)** | *"⚠️ Nhắc nhở: Sếp lại dời 3 việc sang ngày mai. Mắc bệnh 'lạc quan tếu' khi lên lịch rồi. Ngày mai hãy giảm khối lượng việc xuống một nửa để xem sức mình tới đâu nhé."* |
| **TDR = 0% (Clear the Board)** | *"🎯 XUẤT SẮC: Bảng công việc hôm nay đã được clear 100%. Không có nợ nần gì sang ngày mai. Đêm nay sếp sẽ có một giấc ngủ cực sâu (Hiệu ứng Zeigarnik đã được vô hiệu hóa)!"* |
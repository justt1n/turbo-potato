# Thuật toán 3: Productivity VO2 Max (Chỉ số Sức bền Thực thi & Gamification)

**Mục tiêu:** Định lượng khả năng duy trì sự tập trung cường độ cao trong thời gian dài (Consistency) mà không bị sập nguồn (Burnout). Thúc đẩy động lực thông qua hệ thống phần thưởng tài chính tự động.
**Thang đo:** Cấp độ (Level) từ 10 - 80 (Tương tự chỉ số VO2 Max trong thể thao).

## 1. Cơ sở Khoa học (The Science)
Thuật toán này là sự kết hợp của 2 lý thuyết tâm lý học hành vi hàng đầu:
* **Grit (Sự Bền bỉ) của Angela Duckworth:** Thành công không đến từ cường độ (Intensity - làm 15 tiếng/ngày rồi nghỉ cả tuần), mà đến từ sự ổn định (Consistency - làm 2 tiếng/ngày trong suốt 3 năm). Hệ thống phải phạt việc "làm cố" và thưởng cho sự "đều đặn".
* **Vòng lặp Thói quen & Tưởng thưởng (Habit Loop & Dopamine) của James Clear/Charles Duhigg:** Não bộ chỉ hình thành thói quen khi có phần thưởng (Reward) đi kèm. Nếu bạn học Thạc sĩ (`#master`) ròng rã nhưng không thấy niềm vui tức thì, bạn sẽ bỏ cuộc. Bằng cách biến "chuỗi ngày cố gắng" thành "tiền tiêu vặt hợp lý trí", hệ thống tạo ra một cú hack Dopamine cực mạnh.

## 2. Ứng dụng Thực tiễn (Real-life Translation)
* **Người dùng A (Tập luyện sai cách):** Thứ 7 cày 10 tasks `#sidehustle` liên tục, Life Battery tụt xuống 5% (kiệt sức). Chủ nhật, Thứ 2, Thứ 3 nằm ườn không làm gì. -> *VO2 Max giảm vì thiếu bền bỉ và vắt kiệt sức khỏe.*
* **Người dùng B (Tập luyện chuẩn):** Mỗi ngày từ Thứ 2 đến Chủ nhật đều hoàn thành 1 task `#sidehustle` và 1 task `#master`, đồng thời giữ Life Battery luôn trên 40%. -> *VO2 Max tăng đều đặn. Khi đạt mốc (Streak 7 ngày), hệ thống tự động thưởng 200k vào quỹ đi chơi.*

## 3. Logic Thuật toán & Tích hợp Hệ thống (Go Backend)

**A. Các biến số đầu vào (Inputs):**
* `Streak_Days`: Số ngày liên tiếp hoàn thành ít nhất 1 task thuộc nhóm khó (`#master`, `#sidehustle`).
* `Daily_Battery_Min`: Mức pin thấp nhất trong ngày hôm đó.
* `Current_VO2_Max`: Chỉ số sức bền hiện tại của bạn.

**B. Công thức tính toán (Daily Update lúc 23:59):**
Hệ thống Go sẽ chạy Cronjob cuối ngày để tính toán:

1. **Kiểm tra Streak (Chuỗi):**
   * Nếu có task khó DONE: `Streak_Days += 1`.
   * Nếu KHÔNG có task khó DONE: `Streak_Days = 0` (Mất chuỗi).

2. **Chấm điểm VO2 Max:**
   * **Tăng điểm (+):** Nếu `Streak_Days > 0` VÀ `Daily_Battery_Min > 20` (Làm việc đều nhưng không vắt kiệt sức) -> `VO2_Max += 0.5`.
   * **Phạt điểm (-):** Nếu mất chuỗi (`Streak_Days = 0`) -> `VO2_Max -= 1.0`.
   * **Phạt Over-training (-):** Nếu làm task khó nhưng để `Daily_Battery_Min < 15` (Cày cuốc độc hại) -> `VO2_Max -= 0.5` (Dù có làm việc vẫn bị trừ điểm sức bền vì cách làm không bền vững).

**C. Gamification (Hệ thống Tự động Thưởng - Auto Reward):**
Khi bạn đạt được các Cột mốc Sức bền (Milestones), Backend sẽ tự động gọi API của Google Sheets để thực hiện một lệnh `TRANSFER` ngầm:
* Trích X% từ `Hũ Tiết Kiệm` (hoặc một Quỹ thưởng riêng thiết lập sẵn).
* Cộng vào `Hũ Hưởng Thụ`.
* *Lý do:* Tiền này bạn hoàn toàn xứng đáng được tiêu mà không có cảm giác tội lỗi (Guilt-free spending) vì bạn đã nỗ lực đủ lâu.

## 4. Kịch bản Kích hoạt (Triggers & Actions)

| Điều kiện | Phản ứng của Bot (Google Chat) |
| :--- | :--- |
| **Mất Streak (Streak = 0)** | *"Chà, sếp đã bỏ trống task #master hôm nay. Chuỗi 5 ngày đã đứt, VO2 Max giảm nhẹ. Mai làm lại nhé, đừng nản!"* |
| **Warning (Over-training)** | *"Sếp cày cuốc tốt, nhưng pin hôm nay chạm đáy 10%. Hệ thống không khuyến khích làm việc bán mạng. VO2 Max bị trừ 0.5 điểm răn đe. Nghỉ ngơi đi!"* |
| **Streak = 7 ngày (Reward)** | *"🎉 FIRE! Chuỗi 7 ngày năng suất duy trì cực đỉnh. Sức bền (VO2 Max) tăng lên mức 45. Đã tự động chuyển 300k sang Hũ Hưởng Thụ. Thưởng nóng cho bản thân đi sếp!"* |
| **VO2 Max đạt mốc mới** | *"Đỉnh cao mới! Sức bền thực thi của sếp đã vượt 90% user bình thường. Kỷ luật đã thực sự trở thành hơi thở."* |
# Yêu Cầu Backend (Backend Requirements)
**Ngôn ngữ:** Golang (Fiber framework)

## 1. Cấu Trúc Module Cốt Lõi (Core Modules)
* **Webhook & AI Parser:** Bóc tách text thành JSON. *Nâng cấp:* Bắt buộc nhận diện và gán thẻ Domain (`#work`, `#master`, `#sidehustle`, `#life`) cho mọi khoản chi hoặc task.
* **Finance Core:** Ghi chép thu/chi, chia hũ tự động, cập nhật Net Worth (VND & Vàng).
* **Gamification Engine (MỚI):** Xử lý logic Thưởng/Phạt tự động dựa trên Streak và hiệu suất.

## 2. Hệ Thống Thuật Toán Chỉ Số (Metrics Engine - "Garmin Style")
Backend phải tính toán và cập nhật các chỉ số sau mỗi ngày:
* **Life Battery (0-100):** Cân bằng Năng lượng.
  * Trừ điểm: Làm task khó, tiêu lố ngân sách.
  * Cộng điểm: Tiêu tiền hũ Hưởng thụ, nghỉ ngơi, ngủ đủ (nếu có tracking).
* **Financial Stress (Tốc độ đốt tiền):** So sánh `Tốc độ chi tiêu hiện tại` với `Chuẩn Baseline 3 tháng`. Nếu vượt > 20% -> Kích hoạt Cảnh báo.
* **Productivity VO2 Max:** Thể hiện "sức bền". Tăng lên nếu duy trì chuỗi ngày (Streak) làm task `#master` hoặc `#sidehustle` mà Life Battery không bị rớt xuống dưới 20.
* **Domain ROI (Tỷ suất lợi nhuận mảng):** So sánh (Số giờ task `#sidehustle`) với (Thu nhập `#sidehustle`). Kích hoạt warning nếu tốn quá nhiều thời gian nhưng không sinh lời.

## 3. Hệ Thống Cảnh Báo & Phần Thưởng (Cronjobs & Triggers)
| Loại | Điều kiện Kích hoạt (Trigger) | Hành động của Bot (Action) |
| :--- | :--- | :--- |
| **Warning** | Life Battery < 20 | Báo động đỏ: *"Pin cuộc đời cạn kiệt. Cấm làm thêm #sidehustle tối nay!"* |
| **Warning** | Bỏ task #master 3 ngày liền | Khóa hũ Hưởng thụ (từ chối mọi lệnh chi tiêu giải trí cho đến khi làm bù task). |
| **Reward** | Đạt Streak 7 ngày Productivity | Bắn pháo hoa. Tự động chuyển 5% quỹ Tiết kiệm sang hũ Hưởng thụ kèm tin nhắn: *"Thưởng nóng 500k cho sự kỷ luật!"* |
| **System** | Ngày 1 hằng tháng (00:00) | Chạy hàm `CalculateBaseline()` - Quét data 90 ngày để thiết lập "Đường cơ sở chuẩn" cho tháng mới. |

## 4. API Endpoints (Giao tiếp Frontend)
* `GET /api/v1/metrics/current`: Trả về Life Battery, Financial Stress, VO2 Max realtime.
* `GET /api/v1/metrics/roi?domain=sidehustle`: Lấy dữ liệu phân tích ROI của một mảng cụ thể.
* *(Giữ nguyên các API về Finance và Tasks đã định nghĩa trước đó).*
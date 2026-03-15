# Yêu Cầu Frontend (Frontend Requirements)
**Công nghệ:** ReactJS (Vite/Next.js), Tailwind CSS, Recharts/Echarts.
**Concept UI:** Lấy cảm hứng từ Dashboard của các App Thể thao (Garmin Connect, Strava) - Đen nhám (Dark Mode), số to, biểu đồ trực quan, mang tính kích thích thị giác.

## 1. Màn Hình Tổng Quan: Trung Tâm Chỉ Huy (The God-Eye Dashboard)
* **Vùng Chỉ số Sinh tồn (Vital Metrics):**
  * **Gauge Chart (Đồng hồ đo) cho Life Battery:** Hiển thị từ 0-100. Đổi màu Xanh lá (Khỏe) -> Vàng (Mệt) -> Đỏ (Kiệt sức).
  * **Sparkline (Biểu đồ đường nhỏ) cho VO2 Max:** Thể hiện xu hướng sức bền làm việc tăng hay giảm trong 7 ngày qua.
  * **Thanh cảnh báo Financial Stress:** Trạng thái tốc độ tiêu tiền (Bình thường / Nhanh / Nguy hiểm).
* **Vùng Gamification:**
  * Khoe các "Huy hiệu" (Badges) đã đạt được (VD: *Chuỗi 10 ngày không tiêu hoang*, *Thợ săn #sidehustle*).
  * Thông báo động: Nếu có Reward, kích hoạt hiệu ứng Confetti (pháo hoa giấy) toàn màn hình khi mở Web.

## 2. Màn Hình Phân Tích Nhóm (Domain Analysis Page)
Giao diện phân tích sâu theo từng `#tag` (Công việc, Học tập, Làm thêm, Cuộc sống).
* **Biểu đồ Scatter / Bar Chart cho Domain ROI:** Trục X là "Thời gian bỏ ra (Tasks)", trục Y là "Tiền thu về hoặc Tiền chi ra". Giúp user nhìn ngay ra mảng nào đang "hút máu" thời gian mà không sinh lời.
* **Time Allocation Pie Chart:** Tỉ lệ phân bổ thời gian (dựa trên số task) cho các mảng trong tuần qua.

## 3. Màn Hình Tài Chính & Kế Hoạch (Finance & Simulator)
* **Net Worth Widget:** "15.2 Chỉ Vàng SJC ~ 125,000,000 VNĐ" (Cập nhật realtime mỗi sáng).
* **Cỗ Máy Thời Gian (Goals Simulator):** Thanh Slider giả lập phần trăm quỹ Tiết kiệm để tính ngày mua xe/laptop.
* **Jars Status:** Các thanh Progress bar thể hiện lượng tiền còn lại trong 6 chiếc lọ. Nếu hũ Hưởng thụ bị "khóa" (do Warning), hiển thị icon 🔒 màu xám.

## 4. Tương Tác Nhanh (Quick Actions)
* Mặc dù thao tác chính qua Google Chat, Web App vẫn có một nút "+" trôi (Floating Action Button) để ghi nhận chi tiêu hoặc task thủ công đề phòng trường hợp không mở được Chat.
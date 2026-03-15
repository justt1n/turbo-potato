# Thuật toán 5: Vận tốc Mục tiêu & Dự phóng Tương lai (Goal Velocity & ETA)

**Mục tiêu:** Tính toán vận tốc gom tiền thực tế của bạn, từ đó dự phóng chính xác ngày bạn đạt được mục tiêu (mua xe, mua nhà, quỹ hưu trí). Cung cấp công cụ "Cỗ máy thời gian" để giả lập các kịch bản tương lai.
**Thang đo:** Vận tốc (VNĐ/Tháng) và Thời gian (Ngày tháng năm - ETA).

## 1. Cơ sở Khoa học & Phương pháp Tham chiếu

* **Biểu đồ Burn-up (Burn-up Chart - Agile Project Management):**  Trong quản lý dự án, thay vì chỉ đếm số việc đã làm, người ta vẽ 2 đường thẳng: Đường mục tiêu (có thể thay đổi) và Đường thực tế đã làm. Điểm giao nhau của 2 đường này ở tương lai chính là ETA (Estimated Time of Arrival). Thuật toán này đưa cơ chế Agile vào việc gom tiền.
* **Trung bình Trượt (Moving Average - MA):** Để tính vận tốc, hệ thống không lấy trung bình từ lúc bắt đầu (sẽ bị nhiễu bởi những tháng quá khứ làm ăn kém), mà dùng Moving Average 3 tháng gần nhất. Nó phản ánh đúng "động lượng" (Momentum) hiện tại của bạn.

## 2. Logic Thuật toán (Go Backend)

Hệ thống sẽ quét sheet `Goals` và các lệnh `/spend` (vào hũ mục tiêu) để tính toán.

**A. Các biến số đầu vào:**
* $Target$: Tổng số tiền cần đạt (VD: 100.000.000đ mua SH).
* $Current$: Số tiền đã gom được hiện tại (VD: 40.000.000đ).
* $R$ (Remaining): Số tiền còn thiếu ($Target - Current = 60.000.000đ$).

**B. Công thức tính toán (Cập nhật Real-time):**
1. **Tính Vận tốc ($V$):** Tính trung bình số tiền bạn nạp vào mục tiêu này trong 3 tháng qua. 
   *(VD: Tháng 1 nạp 4tr, Tháng 2 nạp 6tr, Tháng 3 nạp 5tr -> $V$ = 5.000.000đ/tháng).*
2. **Tính số tháng còn lại ($M$):** $M = \frac{R}{V}$
   *(VD: $60.000.000 / 5.000.000 = 12$ tháng).*
3. **Tính ETA (Ngày hoàn thành):** `Current_Date + M` tháng.
   *(Hôm nay là Tháng 3/2026 -> ETA = Tháng 3/2027).*

## 3. Giao diện Màn hình Dashboard (Visual Data Representation)

Không cần Bot chat dài dòng. Dữ liệu này sẽ được render trực tiếp lên Frontend (React/Next.js) thành các Widget cực kỳ sắc bén:

### Component 1: The Goal Card (Thẻ Mục tiêu)
* **Tiêu đề:** Mua xe Honda SH.
* **Progress Bar:** Một thanh ngang dài. 40% đã tô màu Xanh lá, 60% còn lại màu xám.
* **Chỉ số (Metrics Text):** * `Đã đạt: 40.000.000 / 100.000.000`
  * `Vận tốc hiện tại: 5.000.000đ / tháng (🔥 Đang tăng)`
  * `ETA: Tháng 03/2027 (Còn 12 tháng)`

### Component 2: The Time Machine Slider (Thanh trượt Giả lập Tương lai)
Đây là tính năng "ăn tiền" nhất và tạo ra Dopamine mạnh nhất cho người dùng.
* Bên dưới Goal Card có một thanh trượt (Slider) có tên: **"Điều gì xảy ra nếu sếp nhịn ăn chơi để tăng vận tốc?"**
* Khi sếp dùng chuột kéo thanh trượt từ `5.000.000đ/tháng` lên `8.000.000đ/tháng`.
* **Hiệu ứng tức thì:** Cỗ máy Frontend lập tức tính toán lại toán học. Con số `ETA: Tháng 03/2027` trên màn hình sẽ nhảy số lùi dần về `ETA: Tháng 10/2026`. 
* **Tác động Tâm lý:** Bạn nhìn thấy rõ ràng: Chỉ cần bớt 3 triệu tiền nhậu/mua sắm mỗi tháng, bạn sẽ lấy được xe sớm hơn nửa năm. Con số trực quan này đè bẹp mọi cám dỗ tiêu xài bốc đồng.
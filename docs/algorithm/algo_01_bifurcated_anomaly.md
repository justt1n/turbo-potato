# Thuật toán 1: Phân nhánh Ngân sách & Nhận diện Bất thường (Bifurcated Budgeting & Z-Score Anomaly Detection)

**Mục tiêu:** Loại bỏ hoàn toàn nhiễu thống kê do các khoản chi lớn xê dịch ngày (như tiền nhà, trả góp). Chỉ theo dõi và cảnh báo tốc độ đốt tiền đối với các khoản chi biến đổi (ăn uống, mua sắm) - nơi thực sự xảy ra rủi ro thất thoát tài sản.
**Thang đo:** Trạng thái Nhị phân (Thanh toán / Quá hạn) cho Định phí; và Điểm chuẩn Z (Z-Score) cho Biến phí.

## 1. Cơ sở Khoa học & Phương pháp Tham chiếu
* **Kế toán Quản trị (Managerial Accounting - Phân tích Hành vi Chi phí):** Mọi doanh nghiệp đều chia tách rạch ròi giữa **Định phí** (Fixed Costs - Chi phí không đổi theo quy mô, VD: Mặt bằng) và **Biến phí** (Variable Costs - Chi phí thay đổi liên tục, VD: Nguyên vật liệu). Việc gộp chung hai loại này để tính tốc độ tiêu hao hằng ngày là một sai lầm thống kê cơ bản.
* **Kiểm soát Quá trình Thống kê (Statistical Process Control - SPC):** Thay vì so sánh dữ liệu hiện tại với một đường trung bình tuyến tính ngây ngô, hệ thống sử dụng **Điểm chuẩn Z (Z-Score)**  để phát hiện các điểm ngoại lai (Outliers). Nó so sánh tốc độ tiêu tiền của ngày $t$ tháng này với chính thói quen của bạn vào ngày $t$ của các tháng trước.

## 2. Phân tách Luồng Dữ liệu (Data Bifurcation)
Hệ thống bắt buộc chia mọi khoản chi ra làm 2 luồng xử lý độc lập ngay từ bước nhập liệu.

### Nhánh A: Xử lý Định phí (Fixed Costs - Tiền nhà, Trả góp, Đăng ký mạng)
* **Đặc tính:** Số tiền cố định, nhưng ngày thanh toán có thể dao động trong một cửa sổ thời gian (Window).
* **Setup Database:**
  * `Item`: Tiền Thuê Nhà
  * `Amount_Target`: 5.000.000 VNĐ
  * `Valid_Window`: `[Ngày 01 - Ngày 05]` hàng tháng.
* **Logic Thuật toán (Window Tracking):**
  * Trong khoảng từ ngày 1 đến ngày 5, hệ thống chờ đợi lệnh `/spend 5000k #tiennha`.
  * Nếu lệnh xuất hiện: Đánh dấu trạng thái `CLEARED` (Đã thanh toán). Số tiền này **không** được cộng vào biểu đồ "Tốc độ đốt tiền hằng ngày".
  * Nếu sang ngày 6 (hết cửa sổ thời gian) mà chưa có lệnh: Đánh dấu trạng thái `DEFAULT` (Vi phạm) và kích hoạt cảnh báo Nợ.

### Nhánh B: Xử lý Biến phí (Variable Costs - Sinh hoạt, Mua sắm, Đi lại)
* **Đặc tính:** Phát sinh hằng ngày, số tiền vô chừng. Đây là mục tiêu giám sát chính.
* **Logic Thuật toán (Z-Score Pacing):**
  * Gọi $X_t$ là tổng số tiền Biến phí lũy kế từ ngày 1 đến ngày hiện tại $t$ của tháng này.
  * Lấy dữ liệu 3 tháng gần nhất, tính giá trị Lũy kế Biến phí trung bình tính đến ngày $t$ (gọi là $\mu_t$) và Độ lệch chuẩn (gọi là $\sigma_t$).
  * Tính điểm Z-Score: 
    $$Z_t = \frac{X_t - \mu_t}{\sigma_t}$$

## 3. Phân tích Các ngưỡng Z-Score (Z-Score Thresholds)
* $Z_t \le 1.0$: **An toàn.** Tốc độ tiêu tiền nằm trong phạm vi thói quen lịch sử.
* $1.0 < Z_t \le 1.96$: **Cảnh báo sớm.** Tốc độ đang cao hơn mức trung bình (Nằm ở top 5% những tháng tiêu hao nhanh nhất lịch sử).
* $Z_t > 1.96$: **Ngoại lai (Anomaly).** Dòng tiền đang thất thoát với tốc độ bất thường. Chắc chắn có sự cố vung tay quá trán.

## 4. Kịch bản Kích hoạt (Triggers & Actions)

Hệ thống hoạt động như một kiểm toán viên máu lạnh, không quan tâm đến cảm xúc, chỉ quan tâm đến sự sai lệch dữ liệu.

| Tình huống Dữ liệu | Phản ứng của Trợ lý (Bot) |
| :--- | :--- |
| **Nhánh A: Trễ Định phí** (Ngày 6, chưa đóng tiền nhà) | *"⚠️ VI PHẠM KHOẢN CỐ ĐỊNH: Đã qua cửa sổ thanh toán (Ngày 1-5). Khoản 'Tiền Thuê Nhà' (5.000.000đ) vẫn chưa được ghi nhận. Yêu cầu thanh toán ngay để tránh phát sinh lãi phạt hoặc rủi ro pháp lý."* |
| **Nhánh A: Thanh toán Định phí** | *(Im lặng ghi nhận, chuyển status sang CLEARED. Không làm nhiễu biểu đồ chi tiêu).* |
| **Nhánh B: Z-Score = 0.5** (Quẹt 300k ăn tối) | *"Đã ghi nhận 300k Biến phí. Tốc độ chi tiêu lũy kế đến hôm nay hoàn toàn khớp với dữ liệu lịch sử (Z-Score: 0.5)."* |
| **Nhánh B: Z-Score = 2.1** (Quẹt 2 triệu mua đồ công nghệ vào giữa tháng) | *"🚨 CẢNH BÁO KIỂM TOÁN DÒNG TIỀN: Z-Score hiện tại là 2.1 (Mức độ Ngoại lai). Tốc độ đốt Biến phí tính đến ngày hôm nay đang phá vỡ dữ liệu lịch sử 3 tháng qua. Thu hẹp ngay ngân sách sinh hoạt các ngày còn lại để kéo Z-Score về dưới 1.0!"* |
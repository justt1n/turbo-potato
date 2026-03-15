# Thuật toán 2: Hạn mức Chi tiêu An toàn Động (Dynamic Safe-to-Spend - STS)

**Mục tiêu:** Tính toán ra **một con số duy nhất** mà bạn được phép tiêu trong ngày hôm nay mà không phá vỡ kế hoạch tài chính của cả tháng. Con số này biến thiên (dynamic) mỗi ngày dựa trên hành vi chi tiêu của các ngày trước đó.
**Thang đo:** Số tiền tuyệt đối (VNĐ/Ngày).

## 1. Cơ sở Khoa học & Phương pháp Tham chiếu

Thuật toán này được thiết kế để triệt tiêu các điểm mù tâm lý và áp dụng chuẩn mực của hệ thống điều khiển tự động:

* **Thiên kiến Hiện tại & Chiết khấu Hyperbolic (Present Bias & Hyperbolic Discounting):**  Theo kinh tế học hành vi, con người luôn định giá phần thưởng ngay lập tức cao hơn phần thưởng trong tương lai. Một ngân sách 30 ngày là quá dài để não bộ cảm nhận rủi ro. Việc xé nhỏ ngân sách thành *Hạn mức theo ngày* giúp kéo hậu quả của tương lai về ngay thì hiện tại. Quẹt thẻ quá tay hôm nay, hạn mức ngày mai lập tức sụt giảm.
* **Hệ thống Điều khiển Vòng kín (Closed-loop Feedback Control System - Cybernetics):** Trong kỹ thuật điều khiển, hệ thống vòng kín liên tục đo lường "Đầu ra thực tế" (Tiền đã tiêu), so sánh với "Tín hiệu chuẩn" (Ngân sách), và ngay lập tức tính toán "Độ lệch" (Error) để điều chỉnh "Đầu vào" (Hạn mức ngày mai). Thuật toán STS chính là bộ điều khiển (Controller) tự động nắn lại quỹ đạo dòng tiền của bạn mỗi ngày.
* **Phương pháp Ngân sách Phong bì (Envelope Method):** Số hóa phương pháp quản lý tài chính cổ điển. Khi tiền trong "phong bì biến phí" vơi đi, số tiền chia đều cho các ngày còn lại bắt buộc phải mỏng đi tương ứng.

## 2. Logic Thuật toán & Tích hợp Hệ thống (Go Backend)

Hệ thống sẽ chỉ áp dụng thuật toán này cho **Biến phí (Variable Costs)** (như ăn uống, đi lại, giải trí), hoàn toàn tách biệt khỏi Định phí (tiền nhà, trả góp) đã được xử lý ở Thuật toán 1.

**A. Các biến số đầu vào (Inputs - Cập nhật lúc 00:00 hằng ngày):**
* $B_v$: Tổng ngân sách Biến phí cho cả tháng (Variable Budget).
* $\sum V_{i}$: Tổng số Biến phí thực tế đã tiêu từ ngày 1 đến ngày hôm qua.
* $D$: Tổng số ngày trong tháng.
* $t$: Ngày hiện tại (Ví dụ: mùng 5 thì $t = 5$).

**B. Công thức tính toán Hạn mức STS:**
$$STS_t = \frac{B_v - \sum_{i=1}^{t-1} V_i}{D - t + 1}$$

**C. Ví dụ Mô phỏng Hậu quả (The Consequence Simulation):**
* Ngân sách Biến phí tháng 3 (31 ngày) là 9.300.000đ.
* **Ngày 1:** $STS_1 = \frac{9.300.000 - 0}{31} = 300.000đ/ngày$. 
* **Ngày 2:** Bạn quẹt thẻ đi ăn nhà hàng hết 1.500.000đ (Tiêu lố 1.200.000đ).
* **Ngày 3:** Hệ thống tính toán lại một cách lạnh lùng:
  $$STS_3 = \frac{9.300.000 - 1.500.000}{31 - 3 + 1} = \frac{7.800.000}{29} \approx 268.965đ/ngày$$
* *Kết luận:* Chỉ vì một bữa ăn vung tay, hạn mức của **29 ngày còn lại** bị ép giảm hơn 10%. Khổ cực kéo dài cả tháng.

## 3. Phân loại Cấp độ STS (STS Thresholds)

Hệ thống thiết lập một ranh giới sinh tồn (Survival Minimum) do bạn cấu hình (Ví dụ: 150.000đ/ngày là mức tối thiểu để đổ xăng và ăn cơm bình dân).

* $STS_t \ge$ Hạn mức ban đầu: **Dư dả.** Bạn đang tích lũy tốt, thậm chí có thể nâng STS cho các ngày sau.
* Sinh tồn $< STS_t <$ Hạn mức ban đầu: **Suy giảm.** Bạn đang phải trả giá cho việc tiêu lố trước đó bằng cách thắt lưng buộc bụng.
* $STS_t \le$ Sinh tồn: **Khủng hoảng (Báo động Đỏ).** Bạn không còn đủ tiền để duy trì mức sống cơ bản cho đến cuối tháng.

## 4. Kịch bản Kích hoạt (Triggers & Actions)

Bảng điều khiển duy nhất bạn cần nhìn vào mỗi buổi sáng là con số STS này. Không cần nhớ tổng ngân sách là bao nhiêu, chỉ cần biết hôm nay được tiêu bao nhiêu.

| Tình huống Dữ liệu | Phản ứng của Trợ lý (Bot) |
| :--- | :--- |
| **07:00 AM (Báo cáo đầu ngày)** | *"📊 Hạn mức STS hôm nay: 268.000đ. Đã sụt giảm 10% do bữa nhậu tối qua. Sếp tự cân đối chi tiêu hôm nay để không kéo STS ngày mai xuống thấp hơn nữa."* |
| **Khi STS chạm mức Sinh tồn** | *"🛑 CẢNH BÁO THANH KHOẢN: STS đã tụt xuống 150.000đ/ngày. Đây là ranh giới sinh tồn. Bot sẽ tự động reject (đóng băng) mọi lệnh ghi nhận Biến phí thuộc nhóm Hưởng thụ. Từ giờ đến cuối tháng chỉ được phép đổ xăng và ăn cơm hộp!"* |
| **Khi STS < 0 (Vỡ nợ cục bộ)** | *"🚨 VỠ TRẬN NGÂN SÁCH: Sếp đã tiêu sạch toàn bộ Biến phí của cả tháng dù hôm nay mới là mùng 20. STS đang âm. Lựa chọn duy nhất: Chấp nhận thâm hụt tài sản (rút từ quỹ Tiết kiệm bù vào) và ghi nhận Penalty (Phạt điểm Kỷ luật) vào hồ sơ tháng."* |
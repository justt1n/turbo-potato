# Thuật toán 8: Stress-Spending Correlation (Tương quan Tâm trạng & Chi tiêu)

**Mục tiêu:** Nhận diện, chặn đứng và phân tích các khoản "Mua sắm giải tỏa" (Emotional Spending/Retail Therapy) - thứ bào mòn tài sản nhanh nhất mà không mang lại giá trị bền vững.
**Thang đo:** Tỷ lệ % các khoản chi tiêu Hưởng thụ diễn ra trong trạng thái "Pin yếu" (Low Battery) hoặc "Nợ task cao" (High Task Debt).

## 1. Cơ sở Khoa học (The Science)
Thuật toán này là sự kết hợp của 2 hiện tượng thần kinh và tâm lý học:
* **Mệt mỏi Quyết định (Decision Fatigue):** Khi Life Battery của bạn cạn kiệt về cuối ngày, Vỏ não trước trán (Prefrontal Cortex - vùng kiểm soát logic) sẽ "đình công". Quyền điều khiển được trao lại cho Hạch hạnh nhân (Amygdala - vùng cảm xúc). Lúc này, sức đề kháng trước những cám dỗ giảm xuống mức thấp nhất.
* **Tiêu dùng Bù đắp (Compensatory Consumption):** Khi bạn thất bại trong một việc (VD: bỏ lỡ 3 task `#sidehustle` và cảm thấy bản thân kém cỏi), não bộ sinh ra cảm giác thiếu hụt giá trị. Để lập tức "vá" lại lòng tự trọng, bạn sẽ có xu hướng mua một món đồ xịn (thưởng cho bản thân) để tạo ra ảo giác kiểm soát và thành công.

## 2. Ứng dụng Thực tiễn (Real-life Translation)
* **Ngày bình thường (Pin 80%):** Sếp thấy cái áo 500k trên Shopee. Sếp nghĩ: *"Cũng đẹp, nhưng ở nhà còn nhiều áo, thôi không mua nữa"*. (Logic hoạt động tốt).
* **Ngày tồi tệ (Pin 15%, Nợ 4 task):** Sếp cày bực dọc, sếp bị sếp la, sếp bỏ dở đống task `#master`. Khuya 11h, sếp mở Shopee thấy đúng cái áo đó. Sếp chốt đơn ngay lập tức với suy nghĩ: *"Nay mình mệt mỏi quá rồi, mình xứng đáng được bù đắp"*.
* **Sự thật phũ phàng:** Sáng hôm sau sếp tỉnh dậy, thấy Life Battery đã hồi 100%, sếp nhìn lại cái đơn hàng và tự hỏi *"Mua cái này làm gì trời?"* - nhưng tiền thì đã trừ.

## 3. Logic Thuật toán & Tích hợp Hệ thống (Go Backend)

**A. Các biến số đầu vào (Inputs - Tracking Real-time):**
* `Time_of_Spend`: Khung giờ phát sinh lệnh `/spend` (VD: 23:30).
* `Amount_Spent`: Số tiền chi ra.
* `Current_Battery`: Mức Life Battery ngay tại thời điểm quẹt thẻ.
* `Current_TDR`: Chỉ số Nợ công việc (Task Debt Ratio) của ngày hôm đó.

**B. Cơ chế Can thiệp Tức thời (Cooling-off Period):**
Hệ thống sẽ đặt một "Chốt chặn tâm lý" (Trigger) khi phát hiện dấu hiệu bốc đồng:
* **Dấu hiệu:** Nếu `Current_Battery < 30` HOẶC `Current_TDR > 30%` (Đang stress/kiệt sức) **VÀ** Lệnh `/spend` rơi vào hũ `Hưởng thụ` với số tiền > X (VD: 500k).
* **Hành động:** Bot không từ chối, nhưng nó yêu cầu **"Thời gian chờ 12 tiếng"**.

**C. Phân tích Tương quan (Monthly Review):**
Cuối tháng, hệ thống rà soát lại tất cả các khoản chi Hưởng thụ và đối chiếu với biểu đồ Tâm trạng (Life Battery / TDR) của những ngày đó.
* `Stress_Spending_Ratio = (Tổng tiền Hưởng thụ tiêu lúc Pin < 30%) / (Tổng tiền Hưởng thụ cả tháng) * 100`.

## 4. Kịch bản Kích hoạt (Triggers & Actions)

| Tình huống | Phản ứng của Bot (Google Chat) |
| :--- | :--- |
| **Can thiệp tức thời (Khuya, Pin yếu)** | *"🛑 KHOAN ĐÃ SẾP: 11h đêm rồi, Life Battery đang ở mức 15% (Đỏ). 90% các quyết định mua sắm lúc này là do não bộ thèm Dopamine chứ không phải sếp thực sự cần. Bot tạm treo khoản 800k Shopee này. Nếu sáng mai ngủ dậy (Pin 100%) sếp vẫn muốn mua, hãy gõ `/confirm`."* |
| **Báo cáo Phân tích Tháng (Insight)** | *"🧠 Bắt thóp Tâm lý: Dữ liệu tháng này cho thấy 75% số tiền sếp tiêu vào hũ Hưởng thụ rơi đúng vào 4 ngày sếp bỏ lỡ task #sidehustle. Sếp đang dùng tiền để mua cảm giác an ủi khi bản thân trì hoãn. Đừng để 'Retail Therapy' đánh lừa sếp nữa!"* |
| **Tiêu dùng Tỉnh thức (Pin cao)** | *"✅ Đã duyệt: Sếp tiêu 1 triệu đi ăn ngon vào lúc sáng sớm cuối tuần, Pin 90%, không nợ task. Đây là sự tự thưởng hoàn toàn hợp lý trí. Chúc sếp ngon miệng!"* |
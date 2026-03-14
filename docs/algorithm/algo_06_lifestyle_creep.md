# Thuật toán 6: Lifestyle Creep Rate (Hệ số Lạm phát Lối sống)

**Mục tiêu:** Phát hiện sớm cái bẫy "thu nhập tăng, chi tiêu tăng theo" để đảm bảo rằng mỗi khi bạn được tăng lương hoặc kiếm được nhiều tiền hơn từ `#sidehustle`, phần lớn số tiền đó đi vào Tài sản thay vì Tiêu sản.
**Thang đo:** Tỷ lệ tương quan (Ratio) giữa Tốc độ tăng Chi tiêu và Tốc độ tăng Thu nhập.

## 1. Cơ sở Khoa học (The Science)
Thuật toán này bắt bệnh dựa trên 2 quy luật tâm lý và kinh tế học:
* **Định luật Parkinson thứ 2 (Parkinson's Second Law):** "Chi tiêu luôn có xu hướng giãn nở để triệt tiêu hết thu nhập". Nếu bạn không có ý thức kiểm soát, não bộ sẽ tự động tìm cách "nâng cấp" các nhu cầu cơ bản (từ uống cafe vỉa hè sang cafe máy lạnh, từ đi xe máy sang đi taxi) ngay khi thấy có nhiều tiền hơn.
* **Vòng xoáy Khoái lạc (Hedonic Treadmill):** Con người có xu hướng nhanh chóng quay về mức độ hạnh phúc ổn định sau khi có một sự thay đổi tích cực (như tăng lương). Việc nâng cấp lối sống chỉ mang lại niềm vui ngắn hạn, sau đó nó trở thành "bình thường mới" (new normal) và bạn lại tiếp tục khao khát mức cao hơn, dẫn đến vòng lặp kẹt tiền vô tận.

## 2. Ứng dụng Thực tiễn (Real-life Translation)
* **Năm ngoái:** Sếp kiếm được 15.000.000đ/tháng. Tiêu Thiết yếu + Hưởng thụ là 10.000.000đ. Dư 5.000.000đ.
* **Năm nay:** Sếp cày thêm `#sidehustle`, tổng thu nhập lên 25.000.000đ (Tăng 66%).
* **Thực tế:** Sếp đổi điện thoại trả góp, dọn ra căn hộ xịn hơn, ăn nhà hàng nhiều hơn. Tổng chi tiêu lên 20.000.000đ (Tăng 100%). Sếp vẫn chỉ dư 5.000.000đ.
* **Đánh giá của Hệ thống:** Sếp cày cuốc cực nhọc hơn, rủi ro cao hơn, nhưng khả năng làm giàu (Wealth Building) không hề tăng lên. Sếp đang dính bẫy Lạm phát lối sống cực nặng.

## 3. Logic Thuật toán & Tích hợp Hệ thống (Go Backend)

**A. Các biến số đầu vào (Inputs tính theo chu kỳ Quý - 3 tháng):**
* `Income_Growth_Rate`: % Tăng trưởng Thu nhập trung bình (Quý này so với Quý trước).
* `Lifestyle_Growth_Rate`: % Tăng trưởng Chi tiêu trung bình của 2 hũ `Thiết yếu` và `Hưởng thụ` (Quý này so với Quý trước).

**B. Công thức tính toán (Lifestyle Creep Ratio - LCR):**
* `LCR = Lifestyle_Growth_Rate / Income_Growth_Rate`
*(Lưu ý: Chỉ kích hoạt tính toán nếu Thu nhập của bạn đang tăng lên. Nếu thu nhập giảm mà chi tiêu vẫn tăng, hệ thống sẽ xếp vào dạng Báo động Đỏ của thuật toán Financial Stress).*

**C. Phân loại Cấp độ Lạm phát (Creep Levels):**
* `LCR < 0.3`: **Tuyệt vời (Kháng lạm phát).** Thu nhập tăng mạnh nhưng chi tiêu gần như giữ nguyên. Bạn đang tối ưu hóa tỷ lệ tiết kiệm.
* `0.3 <= LCR <= 0.7`: **Hợp lý (Tận hưởng thành quả).** Lương tăng 10 đồng, bạn cho phép bản thân tiêu thêm 3-7 đồng. Rất con người và bền vững.
* `LCR > 1.0`: **Báo động (Làm nô lệ cho lối sống).** Chi tiêu đang tăng nhanh hơn cả tốc độ kiếm tiền.

## 4. Kịch bản Kích hoạt (Triggers & Actions)

Thuật toán này cần một độ lùi thời gian để đánh giá, thường được Bot tổng hợp và báo cáo vào **Ngày đầu tiên của mỗi Quý** (Monthly/Quarterly Review).

| Tỷ lệ LCR | Phản ứng của Bot (Google Chat) |
| :--- | :--- |
| **LCR > 1.0 (Lạm phát nặng)** | *"🚨 BÁO CÁO QUÝ: Sếp à, Quý này thu nhập tăng 15%, nhưng mức chi tiêu Thiết yếu và Hưởng thụ lại tăng vọt 25%. Sếp đang rơi vào bẫy Lạm phát lối sống. Cày nhiều hơn nhưng không giàu hơn đâu. Tháng này siết chặt lại ngay!"* |
| **0.3 <= LCR <= 0.7 (Cân bằng)** | *"📊 BÁO CÁO QUÝ: Thu nhập Quý này tăng 20%, chi tiêu chỉ nhích lên 10% (LCR = 0.5). Sếp đang nâng cấp chất lượng sống rất chừng mực mà vẫn giữ được đà tích lũy. Keep it up!"* |
| **LCR < 0 (Thu nhập tăng, Chi tiêu giảm)** | *"👑 CHÚA TỂ KỶ LUẬT: Thu nhập tăng nhưng sếp thậm chí còn tiêu ít đi so với Quý trước. Tốc độ làm giàu đang ở mức tối đa. Đừng quên trích một ít ra thưởng cho Life Battery nhé, đừng khắc khổ quá!"* |
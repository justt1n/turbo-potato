## 3. Ma trận Đánh giá Đa chiều (Cross-Metric Correlation)
*Triết lý: Rủi ro của Định phí phụ thuộc hoàn toàn vào Độ dày của Vốn dự phòng.*

Hệ thống sẽ lấy giá trị **POL (Tỷ trọng Định phí)** đối chiếu với giá trị **Runway (Đường băng sinh tồn từ Hũ Tiết Kiệm/Dự phòng)** để đưa ra nhận định cuối cùng.

**Các góc phần tư của Ma trận:**
1. **Góc Tuyệt đối an toàn (Low POL + High Runway):** Định phí thấp, tiền dự trữ nhiều. Bạn là "vua" của sự linh hoạt.
2. **Góc Tích lũy (Low POL + Low Runway):** Định phí thấp nhưng chưa có tiền phòng thân. Cần dồn lực bơm tiền vào hũ Tiết kiệm.
3. **Góc Chấp nhận Rủi ro (High POL + High Runway):** Định phí cao (có thể do đang vay mua nhà/đầu tư) nhưng quỹ dự phòng dày. Hệ thống **không báo động đỏ**, chỉ nhắc nhở theo dõi.
4. **Góc Tử thần (High POL + Low Runway):** Định phí cao, tiền dự phòng < 3 tháng. Chỉ cần 1 tháng giảm lương là vỡ nợ. Đây là lúc Bot phải can thiệp mạnh nhất.

## 4. Kịch bản Kích hoạt (Triggers & Actions - Cập nhật chống Bias)

Thay vì chỉ nhìn vào con số POL một cách tuyến tính, Trợ lý (Bot) sẽ kết hợp dữ liệu từ các Hũ để đưa ra lời khuyên sát sườn nhất.

| Tình huống Ma trận | Phản ứng của Trợ lý (Bot) |
| :--- | :--- |
| **Góc Tử thần** <br> *(POL > 60% & Runway < 3 tháng)* | *"🚨 BÁO ĐỘNG VỠ NỢ CẤU TRÚC: Định phí của sếp đang chiếm tới 65% thu nhập, trong khi Hũ Tiết Kiệm chỉ đủ sống 2 tháng. Sếp đang đi trên dây không có lưới bảo vệ! Đề nghị: Đóng băng hoàn toàn Hũ Hưởng Thụ tháng này, cấm nhận thêm trả góp, dồn 100% dòng tiền dư vào Quỹ Dự Phòng!"* |
| **Góc Chấp nhận Rủi ro** <br> *(POL > 60% & Runway > 12 tháng)* | *"📊 LƯU Ý CHIẾN LƯỢC: POL của sếp đang khá cao (65%), nhưng dữ liệu cho thấy Quỹ Khẩn Cấp của sếp đủ sức gánh vác trong 14 tháng (Runway rất tốt). Sếp đang kiểm soát đòn bẩy hiệu quả. Hãy duy trì mức thu nhập hiện tại và hạn chế xài phạm vào Quỹ Dự Phòng nhé."* |
| **Thẩm định khoản vay mới** <br> *(Giả lập mua trả góp)* | *"Thẩm định: Khoản trả góp laptop 2tr/tháng sẽ đẩy POL lên 55%. Tuy nhiên, Hũ Tiết Kiệm hiện tại đang trống rỗng. Lời khuyên: Khoan mua vội. Sếp hãy build Hũ Tiết Kiệm lên mốc 30 triệu trước, sau đó hệ thống sẽ 'duyệt' cho khoản trả góp này để đảm bảo an toàn."* |
| **Khi lương tăng (Scale up)** | *"📈 Tối ưu hóa: Thu nhập tháng này tăng mạnh, kéo POL xuống chỉ còn 35%. Sếp có 2 lựa chọn: 1. Nâng cấp lối sống (Tăng Định phí thuê nhà xịn hơn). 2. Giữ nguyên lối sống, dồn phần chênh lệch vào Hũ Đầu Tư để gia tăng Tốc độ Tích lũy Thực tế. Sếp chọn hướng nào?"* |
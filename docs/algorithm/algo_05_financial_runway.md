# Thuật toán 5: Financial Runway (Chỉ số Đường băng Sinh tồn / FIRE Index)

**Mục tiêu:** Tính toán chính xác số tháng bạn có thể duy trì mức sống cơ bản nếu đột ngột mất hoàn toàn nguồn thu nhập (thất nghiệp, ốm đau, khủng hoảng kinh tế, hoặc muốn nghỉ ngơi/khởi nghiệp).
**Thang đo:** Đơn vị tính bằng **Tháng** (Months).

## 1. Cơ sở Khoa học (The Science)
Thuật toán này bắt nguồn từ 2 khái niệm cốt lõi trong Tài chính Cá nhân và Phong trào FIRE (Financial Independence, Retire Early):
* **Emergency Fund (Quỹ khẩn cấp):** Lý thuyết tài chính cơ bản luôn khuyến nghị mỗi người phải có một quỹ khẩn cấp tối thiểu từ 3 đến 6 tháng chi phí sinh hoạt thiết yếu. 
* **Liquid Assets (Tài sản thanh khoản cao):** Trong trường hợp khẩn cấp, chỉ những tài sản có thể chuyển thành tiền mặt ngay lập tức (Tiền mặt, Số dư ngân hàng, Vàng) mới có ý nghĩa cứu sống bạn. Bất động sản hay tiền kẹt trong dự án dài hạn không được tính vào đây.

## 2. Ứng dụng Thực tiễn (Real-life Translation)
Thay vì cảm giác mơ hồ "mình đang có 100 triệu, chắc là ổn", thuật toán sẽ gắn con số đó vào thực tế phũ phàng của bạn.
* Bạn đang có 120.000.000 VNĐ (Tổng tiền mặt, thẻ VCB và Vàng).
* Baseline chi tiêu của hũ **Thiết yếu** (Tiền nhà, điện, nước, ăn uống cơ bản) trong 3 tháng qua là 10.000.000 VNĐ/tháng.
* **Hệ thống tính toán:** `120.000.000 / 10.000.000 = 12 tháng`. 
* **Ý nghĩa:** Dù ngày mai công ty phá sản, bạn vẫn có thể sống bình thường đúng 1 năm nữa mà không cần đi làm hay vay mượn ai. Đây chính là "Quyền lực của sự chối từ" (F-you Money) - bạn có quyền từ chối một công việc độc hại hoặc một deadline vô lý.

## 3. Logic Thuật toán & Tích hợp Hệ thống (Go Backend)

**A. Các biến số đầu vào (Inputs):**
* `Total_Liquid_Assets`: Lấy tổng `Current_Balance` từ các ví/tài khoản (Tiền mặt, Ngân hàng, Ví điện tử) + Giá trị Vàng SJC hiện tại (Lấy từ sheet `Accounts_Status` và `Market_Data`).
* `Essential_Baseline`: Mức chi tiêu trung bình 1 tháng của hũ `Thiết yếu` (Lấy từ sheet `Analytics_Baseline`).

**B. Công thức tính toán (Chạy ngầm Realtime mỗi khi gọi lệnh kiểm tra):**
* `Runway_Months = Total_Liquid_Assets / Essential_Baseline`
* *Tùy chọn Nâng cao:* Nếu bạn muốn tính Đường băng cho mức sống "Thoải mái" thay vì "Sinh tồn", công thức có thể mở rộng thành: 
  `Comfort_Runway = Total_Liquid_Assets / (Essential_Baseline + Enjoyment_Baseline)`

**C. Các Cột mốc Hệ thống theo dõi (Milestones):**
* **Level 1 (Nguy hiểm):** Runway < 3 tháng.
* **Level 2 (An tâm):** Runway = 6 tháng (Đạt chuẩn Quỹ Khẩn Cấp).
* **Level 3 (Tự do):** Runway >= 12 tháng.

## 4. Kịch bản Kích hoạt (Triggers & Actions)

Thuật toán này thường được gọi thông qua câu lệnh `/runway` hoặc `/fire`, và tự động xuất hiện trong báo cáo tổng kết tháng.

| Tình trạng Runway | Phản ứng của Bot (Google Chat) |
| :--- | :--- |
| **Runway < 3 tháng (Nguy hiểm)** | *"⚠️ Cảnh báo Sinh tồn: Đường băng của sếp hiện chỉ còn 2.5 tháng. Bất kỳ rủi ro mất việc nào lúc này cũng sẽ dẫn đến nợ nần. Đề nghị phong tỏa hũ Hưởng thụ, dồn toàn lực bơm tiền vào hũ Tiết kiệm tháng này!"* |
| **Đạt mốc 6 tháng (Milestone)** | *"🎉 Chúc mừng! Đường băng sinh tồn vừa cán mốc 6.1 tháng. Sếp đã chính thức xây xong Quỹ Khẩn Cấp. Từ giờ có thể ngủ ngon dù ngoài kia có bão giá hay sa thải."* |
| **Runway > 12 tháng (Quyền lực)** | *"😎 Định giá Tự do: Đường băng hiện tại là 13.5 tháng. Sếp đã có đủ vốn để tự tin đàm phán lương hoặc nghỉ việc 1 năm để theo đuổi dự án #sidehustle mà không phải nhìn sắc mặt ai."* |
| **Runway giảm (Do Baseline tăng)** | *"📉 Chú ý: Tổng tài sản không giảm, nhưng mức chi tiêu Thiết yếu tháng này tăng vọt làm Đường băng tụt từ 7 tháng xuống 6.2 tháng. Cẩn thận lạm phát lối sống nhé sếp!"* |
# Thuật toán 1: Life Battery (Chỉ số Cân bằng Năng lượng)

**Mục tiêu:** Định lượng hóa mức độ hao hụt ý chí và sức lực trong ngày để ngăn chặn tình trạng kiệt sức (Burnout) và những quyết định tài chính sai lầm do căng thẳng.
**Thang đo:** 0 - 100 điểm (Giống thanh HP/Stamina trong game).

## 1. Cơ sở Khoa học (The Science)
Thuật toán này được xây dựng dựa trên **Thuyết Suy giảm Bản ngã (Ego Depletion Theory)** của Giáo sư Tâm lý học Roy Baumeister. 
* Lõi lý thuyết chỉ ra rằng: Ý chí (Willpower) và sự tự chủ của con người là một nguồn tài nguyên hữu hạn. Mỗi quyết định bạn đưa ra, mỗi giờ bạn ép bản thân tập trung code (`#sidehustle`) hay học bài (`#master`), bạn đang rút cạn "nguồn pin" này. 
* Khi pin cạn (Ego Depletion), não bộ rơi vào trạng thái phòng thủ: Bạn dễ cáu gắt, lười biếng, và đặc biệt là **dễ chi tiêu bốc đồng** (mua sắm vô tội vạ để tìm kiếm dopamine bù đắp). 
* Để sạc lại, não bộ cần **Sự tách rời tâm lý (Psychological Detachment)** thông qua các hoạt động giải trí không mang tính áp lực.

## 2. Ứng dụng Thực tiễn (Real-life Translation)
Hệ thống sẽ không ép bạn làm việc như một cỗ máy. Nó hiểu rằng bạn là con người.
* Buổi sáng bạn thức dậy với 100% pin.
* Khi bạn gõ `/task done Viết API cho bot #sidehustle`, hệ thống ghi nhận bạn đã làm việc tốt, nhưng đồng thời trừ đi 15 điểm pin vì nó biết bạn vừa tốn rất nhiều chất xám.
* Đến 8h tối, nếu pin của bạn chỉ còn 15%, bạn định gõ `/task Học thêm 1 chương #master`. Bot sẽ từ chối hoặc cảnh báo gắt gao: *"Sếp đang kiệt sức. Việc nhồi nhét lúc này có ROI = 0. Hãy đi tắm và nghe nhạc!"*
* Nếu bạn gõ `/spend 100k Hưởng_thụ Xem phim #life`, hệ thống trừ tiền trong hũ, nhưng **cộng lại 30 điểm pin** cho bạn.

## 3. Logic Thuật toán & Tích hợp Hệ thống (Go Backend)

**A. Khởi tạo (Daily Reset):**
* Đúng `00:00` mỗi ngày, Cronjob reset `Life_Battery = 100`.
* **Trừ hao (Carry-over penalty):** Nếu ngày hôm qua bạn có task ưu tiên CAO bị bỏ lỡ (Overdue), hệ thống trừ khởi điểm 10 điểm. (VD: Sáng dậy pin chỉ có 90 vì áp lực việc tồn đọng).

**B. Cơ chế Rút cạn (Drainers - Khi gọi Webhook ghi nhận Task):**
* Hoàn thành 1 task `#work` (Công việc thường ngày): `-10 điểm`.
* Hoàn thành 1 task `#sidehustle` hoặc `#master` (Cần tập trung cao độ, làm ngoài giờ): `-15 điểm`.
* Ghi nhận 1 khoản chi tiêu vượt hạn mức (Gây stress tài chính): `-20 điểm`.

**C. Cơ chế Sạc lại (Chargers):**
* Hoàn thành 1 task `#life` (VD: Tập gym, chạy bộ 30p, thiền): `+15 điểm`.
* Chi tiền vào hũ `Hưởng thụ` (Giải trí hợp lý trí): `+25 điểm` (Giới hạn sạc 1 lần/ngày để tránh việc "tiêu nhiều tiền thì tưởng là khỏe").

**D. Ranh giới (Boundaries):**
* Giá trị luôn được kẹp (clamp) trong khoảng `0 <= Life_Battery <= 100`.

## 4. Kịch bản Kích hoạt (Triggers & Actions)

| Điều kiện | Phản ứng của Bot (Google Chat) |
| :--- | :--- |
| **Battery = 100** | *"Sáng nay pin đầy 100%. Quất ngay task #master khó nhất đi sếp!"* |
| **Battery <= 40** | *"Pin xuống dưới 40% rồi. Nhớ uống nước và đứng lên đi lại 5 phút nhé."* |
| **Battery <= 15 (Cảnh báo đỏ)** | *"⚠️ BÁO ĐỘNG TÀI NGUYÊN KIỆT QUỆ: Cấm thêm task #work hay #sidehustle tối nay. Đề nghị kích hoạt mode nghỉ ngơi ngay lập tức nếu không muốn ngày mai sập nguồn!"* |
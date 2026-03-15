# Cơ chế Xác thực Giao dịch (Human-in-the-Loop Validation)

**Mục tiêu:** Cung cấp cho người dùng quyền kiểm soát tuyệt đối đối với kết quả phân loại của LLM. Cho phép sửa chữa (Correction) hoặc hủy bỏ (Undo) ngay lập tức chỉ với 1 thao tác (Zero-Friction), đảm bảo Database luôn sạch 100%.

## 1. Nguyên lý Hoạt động: Soft-Commit & Tự động chốt sổ

Hệ thống sẽ không bắt ép bạn phải gõ "Confirm" cho mọi giao dịch để tránh gây phiền hà. Thay vào đó, nó dùng cơ chế **Soft-Commit**:
1. Ngay khi LLM và Regex xử lý xong, Backend lập tức `INSERT` dòng dữ liệu vào Sheet `Transactions` (Trạng thái ngầm định là đã lưu).
2. Bot phản hồi lại một tin nhắn tóm tắt (Receipt) rõ ràng, kèm theo các "nút bấm" (hoặc lệnh gõ tắt) để sửa sai.
3. Nếu LLM phân loại đúng, sếp **không cần làm gì cả**, tắt màn hình và đi làm việc khác. 
4. Nếu LLM phân loại sai, sếp bấm nút/gõ lệnh sửa. Backend sẽ cập nhật (`UPDATE`) lại chính dòng dữ liệu vừa ghi.

## 2. Giao diện Tương tác trên Chat (Chat UI)

Tùy thuộc vào nền tảng sếp dùng (Telegram có Inline Keyboards, Google Chat có Card Messages), tin nhắn trả về sẽ được thiết kế như một "Hóa đơn siêu tốc".

**Kịch bản ví dụ:**
Sếp chat: `đi nhậu với phòng 500k`
LLM (có thể) phân loại nhầm: Hũ `ThietYeu` (vì nghĩ là ăn uống cơ bản).

**Phản hồi của Bot:**
```text
✅ ĐÃ GHI NHẬN GIAO DỊCH MỚI (Tx: 17104...)
-----------------------------------
💰 Số tiền: 500.000 VNĐ
🏷️ Phân loại: [ThietYeu] ⚠️ (Do AI tự đoán)
📝 Ghi chú: Đi nhậu với phòng
🔄 Loại: Biến phí (Phát sinh)
-----------------------------------
💡 Hạn mức STS hôm nay còn: 250.000 VNĐ.

[LLM phân loại sai? Chọn nhanh để sửa lại:]
[1. Hưởng Thụ]  [2. Cho Đi]  [3. Cố định (Fixed)] 
[❌ HỦY (UNDO)]
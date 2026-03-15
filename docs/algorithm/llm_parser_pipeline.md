Đây là luồng xử lý (Pipeline) mỗi khi Backend nhận được tin nhắn từ Chat.

Bước 1: Trích xuất bằng Regex (Nguồn chân lý cứng)
Trước khi gọi AI, Go rà soát text để tìm các con số và tags.

Input: an_uongg #an_toi 50000 (hoặc 50k, 50.000)

Regex Số tiền: Tìm chuỗi số, nhận diện k = 000. → ExtractedAmount = 50000

Regex Tags: Lấy các cụm bắt đầu bằng #. → ExtractedTags = ["an_toi"]

Bước 2: Gọi Gemini API (Sử dụng JSON Schema)
Gọi Gemini API với cấu hình bắt buộc trả về JSON (response_mime_type: "application/json").

System Prompt Chuẩn:

Plaintext
Bạn là một kế toán viên AI cực kỳ chính xác. Nhiệm vụ của bạn là phân tích tin nhắn người dùng và phân loại vào đúng định dạng JSON. 
Tuyệt đối không giải thích, không thêm text thừa, chỉ trả về chuỗi JSON hợp lệ.

[DANH MỤC 6 HŨ (Jars) HỢP LỆ & NGỮ NGHĨA]: 
1. ThietYeu (Thiết yếu - 55%): Các chi phí sinh hoạt bắt buộc để tồn tại (Tiền thuê nhà, điện nước, siêu thị, đổ xăng, ăn uống cơ bản hàng ngày).
2. HuongThu (Hưởng thụ - 10%): Chi tiêu cho niềm vui, tự thưởng (Ăn nhà hàng xịn, xem phim, du lịch, mua đồ chơi, sở thích cá nhân).
3. TietKiem (Tiết kiệm dài hạn - 10%): Gom tiền cho các mục tiêu lớn hoặc quỹ khẩn cấp (Mua xe, mua điện thoại, gửi tiết kiệm).
4. GiaoDuc (Giáo dục - 10%): Chi phí phát triển bản thân (Mua sách, đóng học phí #master, mua khóa học, hội thảo).
5. TuDoTaiChinh (Tự do tài chính - 10%): Các khoản chi đẻ ra tiền (Mua vàng, mua cổ phiếu, vốn chạy ads #sidehustle).
6. ChoDi (Cho đi - 5%): Tiền dùng cho người khác (Từ thiện, đi đám cưới, mua quà tặng sinh nhật, biếu gia đình).

[QUY TẮC PHÂN LOẠI IS_FIXED (Định phí / Biến phí)]:
- true (Định phí): Các khoản cố định hằng tháng, không đổi hoặc ít đổi (Tiền nhà, trả góp, hóa đơn mạng, phí subscription Netflix/Spotify).
- false (Biến phí): Các khoản phát sinh không cố định (Ăn uống, đi lại, giải trí, mua sắm).

[QUY TẮC XỬ LÝ TAGS ĐẶC BIỆT]:
Nếu người dùng dùng thẻ tag (VD: #sidehustle, #master), hãy giữ nguyên tag này ở cuối trường "clean_note" để phục vụ phân tích ROI sau này.

[FORMAT JSON BẮT BUỘC TRẢ VỀ]:
{
  "action": "OUT", // IN (Thu nhập), OUT (Chi tiêu), TRANSFER (Chuyển giữa các hũ)
  "amount": 50000, // Định dạng số nguyên (VD: 50k -> 50000)
  "jar_category": "HuongThu", // Phải khớp chính xác 1 trong 6 tên hũ ở trên
  "is_fixed": false, // boolean (true/false)
  "clean_note": "Ăn tối nhà hàng" // Viết lại note cho chuẩn chính tả, giữ lại thẻ #tag nếu có
}
end promtp.

User Prompt (Gửi kèm data đã bóc tách):

Plaintext
Tin nhắn gốc: "an_uongg #an_toi 50000"
Gợi ý từ hệ thống (Regex): Số tiền có thể là 50000, Tags bao gồm [#an_toi]. 
Hãy phân tích và trả về JSON.
Bước 3: Validation Logic (Golang)
Sau khi nhận JSON từ Gemini, ta đưa qua trạm kiểm duyệt cuối cùng trước khi ghi vào Google Sheets.

Go
func ValidateAndInsert(userInput string) error {
	// 1. Regex bóc tách
	regexAmount := ExtractAmountWithRegex(userInput) // Kết quả: 50000
	
	// 2. Gọi LLM
	llmResponse := CallGeminiAPI(userInput, regexAmount) 
	/* Giả sử LLM bị ảo giác trả về:
	{
		"action": "OUT",
		"amount": 5000, // Sai số 0
		"jar_category": "AnUong",
		"is_fixed": false,
		"clean_note": "Ăn tối"
	}
	*/

	// 3. Validation Rules (Quy tắc tuyệt tình)
	
	// Rule 1: Đối chiếu số tiền (Tiền bạc không thể sai)
	finalAmount := llmResponse.Amount
	if regexAmount > 0 && llmResponse.Amount != regexAmount {
		log.Printf("CẢNH BÁO: LLM tính sai số tiền (%v). Override bằng Regex (%v)", llmResponse.Amount, regexAmount)
		finalAmount = regexAmount // Luôn tin tưởng Regex cho các con số
	}

	// Rule 2: Kiểm tra Category có nằm trong danh sách cho phép không
	if !IsValidJar(llmResponse.JarCategory) {
		llmResponse.JarCategory = "Uncategorized" // Fallback an toàn
	}

	// 4. Định hình Record cuối cùng
	record := []interface{}{
		GenerateTxID(),
		time.Now().Format("02/01/2006"),
		llmResponse.Action,
		finalAmount,
		llmResponse.JarCategory,
		llmResponse.IsFixed,
		llmResponse.CleanNote,
	}

	// 5. Insert vào Google Sheets (Chỉ ghi data khi đã Valid 100%)
	InsertToSheet("Transactions", record)
	return nil
}
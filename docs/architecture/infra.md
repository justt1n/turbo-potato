# Yêu Cầu Hạ Tầng & Dữ Liệu (Infrastructure & Data)
**Dự án:** Personal Life OS (Trợ lý Tài chính & Năng lượng Cá nhân)
**Phiên bản:** 2.0 (Tích hợp Hệ thống Chỉ số Garmin & Gamification)
**Mô hình triển khai:** Tối ưu chi phí ($0/tháng), độ sẵn sàng cao.

## 1. Máy Chủ Backend (Hosting)
* **Nhà cung cấp:** Oracle Cloud Infrastructure (OCI) - Gói Always Free.
* **Hệ điều hành:** Ubuntu 22.04 LTS hoặc Oracle Linux.
* **Môi trường:** Golang binary chạy ngầm qua `systemd` hoặc Docker Alpine (tiêu thụ < 50MB RAM).

## 2. Cơ Sở Dữ Liệu (Database - Google Sheets)
Sử dụng Google Sheets API. Tận dụng tối đa hàm `QUERY`, `SUMIFS`, `AVERAGEIFS` để tính toán Baseline thô.
**Cấu trúc mở rộng cho Tag/Domain:**
* **Sheet `Transactions`:** Thêm cột `Tags` (VD: `#master`, `#sidehustle`, `#life`).
* **Sheet `Tasks`:** Thêm cột `Tags` và `Estimated_Hours` (Số giờ dự kiến) để tính ROI thời gian.
* **Sheet `Analytics_Baseline`:** Tự động tổng hợp chi tiêu và số lượng task hoàn thành theo từng `#tag` trong 30/90 ngày.
* **Sheet `Metrics_History` (MỚI):** Lưu trữ lịch sử các chỉ số hàng ngày (Life Battery, VO2 Max, Stress Score) để vẽ biểu đồ xu hướng.

## 3. Dịch Vụ API Phụ Trợ (Third-party Services)
* **AI / NLP (Gemini API Free):** Phân tích ngôn ngữ tự nhiên, trích xuất số tiền, hành động và nhận diện các `#tags` từ tin nhắn chat.
* **Web Scraping:** `goquery` cào giá vàng SJC mỗi sáng.
* **Google Chat API:** Webhook nhận lệnh và gửi Notification/Warning/Reward.

## 4. Frontend & Bảo Mật
* **Hosting:** Vercel / Netlify (Free tier) triển khai React/Next.js.
* **Bảo mật:** Biến môi trường `.env` (Backend), xác thực Webhook Google Chat, và Mật khẩu/PIN tĩnh cho Web Dashboard.
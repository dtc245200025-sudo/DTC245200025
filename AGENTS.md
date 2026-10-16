# LinhChat — quy ước tiếp tục công việc

- Đầu mỗi phiên, đọc đầy đủ `MEMORY.md` và các file trong `docs/memory/` mà nó dẫn tới trước khi thay đổi dự án. Đây là hồ sơ yêu cầu và trạng thái, không phải bằng chứng runtime thay thế kiểm tra thật.
- Sau mỗi thay đổi đáng kể, cập nhật tiến trình, kết quả kiểm tra và checklist trong các file trí nhớ. Phân biệt rõ đã viết cấu hình / đã chạy đạt / người dùng đã chụp.
- Làm trên Ubuntu VMware thật qua SSH nếu truy cập được. Không nói đã triển khai khi mới kiểm tra bản Windows hoặc cấu hình tĩnh.
- Thông báo bằng tiếng Việt sau mỗi giai đoạn, hướng dẫn chính xác cần chụp gì và cho đoạn báo cáo ngắn. Báo cáo tổng chỉ 10–15 trang; không tăng ảnh không cần thiết. Chờ người dùng chụp trước khi chuyển giai đoạn tiếp theo làm đổi màn hình.
- Giữ dữ liệu PostgreSQL và thay đổi của người dùng; sao lưu trước nâng cấp. Không dùng `down -v`, reset dữ liệu hoặc xóa thư mục rộng.
- Không đưa `.env`, khóa SSH, mật khẩu, tài khoản demo riêng, backup và dữ liệu người dùng vào Git, file trí nhớ, log hoặc ảnh. `work/` và `outputs/` được ignore.
- Giữ ba mốc commit: (1) ứng dụng + PostgreSQL/pgAdmin + Nginx đã chạy đạt; (2) monitoring đã chạy đạt; (3) logging đã chạy đạt. Không trình bày thành phần chưa chạy là đã hoàn thành.
- Không tự push, tạo repository/PR hoặc gửi tin sang cuộc trò chuyện khác khi chưa được yêu cầu.

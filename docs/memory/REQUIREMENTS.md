# Mục tiêu, ý tưởng và phạm vi

## Mục tiêu gốc

Hoàn thành Đề 32 hệ thống chat nội bộ theo file đề gốc, chạy bằng Docker Compose trên Ubuntu trong VMware, có source thực tế và bằng chứng kiểm thử. Stack đã chốt: Python Flask + Flask-SocketIO, PostgreSQL + pgAdmin, Nginx, Prometheus, Grafana, Loki, Promtail. Windows dùng để cộng tác/trình duyệt; không chia nửa ứng dụng sang Windows.

8 giai đoạn: (1) môi trường Ubuntu/Git/Docker; (2) source/Flask; (3) chat realtime và DB cùng mở rộng; (4) Compose/Nginx; (5) monitoring; (6) logging; (7) hardening; (8) README/demo/báo cáo. Giữ ba mốc commit ứng dụng/Nginx, monitoring, logging. Không commit bí mật `.env`. Không tự giả định có công cụ/VM đang chạy; kiểm tra trước.

Đọc lại toàn bộ nội dung đề gốc16/10: yêu cầu repository GitHub theo mã sinh viên, đủ03commit có ý nghĩa và README; báo cáo tối thiểu10trang, bìa thông tin sinh viên/chủ đề, kiến trúc/cách hoạt động/kết quả có hình. Đề cho chọn HTTPS tự ký **hoặc** security headers cơ bản; ở lab GĐ4 chọn headers, không xem đây là mã hóa HTTP. Monitoring phải có container/web/DB; logging có ít nhất2–3query LogQL; hardening ít nhất3–4biện pháp. Chưa có repo GitHub đích được cung cấp, nên không tự tạo/push; cần chốt trước nộp bài.

## Ý tưởng và yêu cầu người dùng đã chốt

- Tên hiển thị **LinhChat**, không còn De32 Chat ở giao diện. Sáng: trắng và hồng phấn nhạt; tối: tím than, chuyển đổi và ghi nhớ lựa chọn.
- Đăng ký bắt buộc email; đăng nhập bằng username hoặc email và mật khẩu. Tài khoản cũ bổ sung email bằng xác nhận mật khẩu, không gán email giả. Chưa yêu cầu gửi email xác thực/SMTP.
- Trang chủ: “Xin chào đến với LinhChat, hãy bắt đầu tạo phòng chat hoặc tham gia phòng chat nhé!”, hai lựa chọn Tạo phòng Chat / Tìm kiếm phòng Chat.
- Bạn bè: tìm theo tên hoặc email, online/offline realtime; gửi/nhận/chấp nhận/từ chối/thu hồi lời mời và hủy kết bạn. Email riêng tư không lộ qua tìm kiếm. Tài khoản đăng nhập ở góc dưới trái.
- Phòng: tên và Private/Public. Public giới hạn số người; triển khai 2–500 gồm chủ phòng cho phòng mới. Private chọn một cách truy cập: link mời, quản trị viên/người tạo duyệt hoặc mật khẩu. Tìm phòng, tham gia/rời, lịch sử chỉ cho thành viên có quyền. Phòng cũ giữ dữ liệu/thiết lập cũ.
- Hồ sơ: trang cá nhân và trang người khác; avatar chữ viết tắt/ảnh, tên hiển thị được sửa, username cố định, online/offline, bio tối đa 150 ký tự, ngày tham gia, chỉnh public/private và quyền hiện email. Khung hồ sơ căn giữa, hai lề cân đối.
- Menu avatar nhỏ góc trên phải theo mẫu Teams: tên/username/trạng thái, Xem hồ sơ, Đổi mật khẩu, Cài đặt, Đăng xuất; đóng khi bấm ngoài/Escape.
- Tab Bảo mật trong Profile: mật khẩu hiện tại/mới/xác nhận, nút hiện/ẩn, hash và kiểm tra bằng `werkzeug.security`; không lưu plaintext. Đổi mật khẩu thu hồi các phiên cũ.
- Quyết định triển khai khi audit GĐ7: đăng xuất cũng thu hồi mọi phiên HTTP/cookie/Socket.IO của chính tài khoản bằng auth_version; không ảnh hưởng tài khoản khác. Nút Thoát/menu có tooltip giải thích. Đây là bản sửa hardening, không phải yêu cầu thêm giao diện mới.
- Chat riêng từng người từ Bạn bè, chỉ hai tài khoản truy cập; phải còn là bạn bè để gửi mới, vẫn giữ lịch sử sau hủy kết bạn.
- Chung cho nhóm/riêng: đang nhập realtime; đã gửi/nhận/xem realtime, bấm tin xem thời gian từng mốc; tìm tin; emoji có gợi ý; ảnh/file tối đa 10 MB (triển khai 10 MiB = 10,485,760 byte), một tệp mỗi lần. Tệp/preview ở PostgreSQL, tải xuống kiểm tra quyền.
- Tin cũ không bịa thời gian nhận/xem. Nhận là trình duyệt xác nhận, không suy ra từ online; xem là tin hiện trong khung chat có focus, không chứng minh người đọc hiểu. Nhóm chốt danh sách người nhận lúc gửi.
- Bổ sung do người dùng báo lỗi 16/10: thông báo nổi trong LinhChat khi người nhận ở trang khác, nút mở đúng cuộc trò chuyện, badge chưa đọc nhóm/riêng/hộp thư/tab trình duyệt; bền qua reload/offline. Không thông báo của chính mình, không phát lại popup lịch sử khi reconnect. Không tự xin quyền OS, phát âm thanh hay gửi email. Người dùng xác nhận đã thấy thông báo.

## Ý tưởng mở rộng chưa cam kết

Mẫu Profile gợi ý trạng thái Bận/Vắng mặt, số phòng đã tham gia, 2FA, timezone, ngôn ngữ và email notification; đây là tham khảo/khả năng mở rộng, không phải toàn bộ tính năng phải làm. Theme sáng/tối ban đầu gọi mở rộng nhưng đã được người dùng yêu cầu và đã làm. Không tự triển khai 2FA/SMTP/PWA/push OS hoặc nhiều instance khi chưa có yêu cầu.

## Cách làm việc và báo cáo

Làm hộ và kiểm tra trong môi trường sẵn có. Sau từng giai đoạn gửi kết quả kiểm tra, chỉ rõ khi nào chụp/đoạn nào và một đoạn ngắn mô tả tạo bằng công cụ gì. Người dùng chụp trực tiếp trong Ubuntu để viết báo cáo tổng 10–15 trang. Hạn chế ảnh lặp, dùng Hình X khi chưa biết số cuối. Không sửa Demo.docx hoặc tạo nội dung khẳng định hoàn thành trước kiểm thử. Chưa có yêu cầu push GitHub/PR.

Ngày19/10 người dùng xác nhận đã chụp GĐ7, báo cáo đã đến **Hình12**; ảnh mới GĐ8 phải là **Hình13**, không dùng HìnhX hoặc đánh lại các ảnh trước khi chưa xem bản báo cáo cuối.

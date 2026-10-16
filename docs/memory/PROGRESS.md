# Tiến trình và bằng chứng

## 16/10/2026 — trạng thái lúc tạo file trí nhớ

- GĐ1: Ubuntu/Git/Docker/Compose đã chạy, hello-world đạt; người dùng xác nhận đã chụp.
- GĐ2: source/Flask và giao diện LinhChat, 13 test ban đầu; người dùng xác nhận đã chụp.
- GĐ3 cơ bản: PostgreSQL/pgAdmin và chat hai chiều WebSocket thật, giữ lịch sử sau restart. Người dùng đã chụp Hình 5 chat và Hình 6 Query Tool JOIN messages/rooms/users, cùng Compose và các phần mở rộng trong Demo.docx.
- 3.1: email/đăng nhập/đổi theme/trang chủ, 22 test lúc mốc; dữ liệu cũ giữ nguyên.
- 3.3a (được ưu tiên theo người dùng): hồ sơ/avatar/menu/Bảo mật/riêng tư, 38 test lúc mốc; Profile realtime/kiểm tra UI đạt. Đã sửa khung hồ sơ căn đều hai bên.
- 3.2: Public/Private, quyền/người tham gia/giới hạn/phê duyệt/link/mật khẩu; 55 test lúc mốc, `ROOMS32_LIVE_CHECK_OK`, `ROOMS32_PERSISTENCE_OK` và kiểm tra tranh chỗ cuối PostgreSQL đạt.
- 3.3b: Bạn bè, 70 test lúc mốc, `FRIENDS33B_LIVE_CHECK_OK`, UI hai phía tự cập nhật; người dùng chọn làm Bạn bè trước Nginx.
- 3.4a: chat riêng + đang nhập nhóm/riêng; 98 test lúc mốc, `DIRECT34A_LIVE_CHECK_OK`, `DIRECT34A_PERSISTENCE_OK`, hồi quy nhóm đạt.
- 3.4b: gửi/nhận/xem, thời gian, tìm/emoji/ảnh/file10 MiB; 131 test lúc mốc, `MESSAGES34B_LIVE_CHECK_OK`, `MESSAGES34B_PERSISTENCE_OK`; UI sáng/tối, tải tệp/preview/chi tiết thời gian đạt. Cũ không tạo receipt giả.

## 16/10/2026 — sửa thiếu thông báo

Nguyên nhân: thiếu UI toast/badge; nhóm chỉ gửi sự kiện cho người mở phòng. Đã thêm `notifications.py` và `notifications.js`, sự kiện riêng theo người nhận cho cả nhóm/riêng; unread tính từ receipt chưa xem trong PostgreSQL, lọc quyền thành viên. Nhận không xóa unread, GET không đánh dấu xem, seen đồng bộ qua nhiều tab. Không phát popup cho người gửi/người ngoài, retry không tạo lặp, reconnect chỉ khôi phục badge. Có điều kiện không báo nổi khi cửa sổ chat đúng đang focus và ở cuối khung.

- 9 test bổ sung, tổng **140 passed** ở Windows (324.37s) và Ubuntu container (67.05s).
- `NOTIFICATIONS_LIVE_OK`: HTTP/PostgreSQL/WebSocket thật, nhận khi ở ngoài chat, đúng người, chống trùng, delivered/seen, offline/reconnect cho nhóm và riêng.
- UI hai tài khoản: B ở trang chủ nhận toast/nút Xem và badge 1; bấm mở `/direct/2`, focus khung tin làm badge hết. A không nhận popup cho tin mình gửi. B ở tab không focus vẫn có popup dù URL là chat (đúng phạm vi điều kiện).
- Ảnh UI thật: `outputs/linhchat-thong-bao.png` (ignore). Người dùng xác nhận: “đã thấy thông báo tin nhắn mới”.
- Backup trước sửa: `work/backups/before-phase31-20261016-225704` trên VM. Chưa kiểm tra persistence notification sau tạo lại app ở thời điểm này; sẽ kiểm tra trong GĐ4.

## Đang làm — GĐ4

Người dùng yêu cầu lưu trí nhớ và tiếp tục GĐ4. Kế hoạch: sao lưu; kiểm tra Nginx HTTP/WebSocket/upload/headers/health; chuyển Compose bỏ phase3 để đóng published :5000; chạy HTTP/WebSocket thật và kiểm tra dữ liệu cũ sau recreate; kiểm tra UI; tạo commit mốc 1 sau khi đạt; cung cấp tối đa hai ảnh và đoạn báo cáo ngắn. Monitoring/logging chưa chạy, không nhận hoàn thành thay.

## Điểm cần nhớ

- Không xóa DB hoặc bí mật, không `down -v`. Migrations trước chỉ bổ sung schema. Tài khoản synthetic của công cụ dùng cho kiểm thử không phải tài khoản thật người dùng.
- Nhật ký cũ ở `outputs/KET_QUA_HIEN_TAI.md` và lộ trình có những câu trạng thái lịch sử đã lỗi thời; luôn lấy mục mới nhất có ngày/bằng chứng, không coi tất cả đoạn cũ là hiện trạng.
- Word báo cáo đã có nhiều hình, có trùng số Hình 7; số ảnh mới nên dùng Hình X. Chưa render/dàn trang bản Word.

## 16/10/2026 — GĐ4 hoàn thành kỹ thuật

- Đọc lại toàn bộ nội dung đề gốc, xác nhận mốc1 ứng dụng/Nginx, mốc2 monitoring, mốc3 logging; HTTPS tự ký hoặc headers cơ bản. Không sửa hai file Word.
- Backup trước chuyển: `work/backups/before-phase31-20261016-231002` trên VM. Không xóa volume hay tài khoản/tin cũ.
- Nginx chính thức1.30.6-alpine đã pull thành công, pin digest trong Compose. Non-root101, read-only/tmpfs, healthcheck qua app. `nginx -t` hợp lệ. Docker DNS/upstream resolve tự theo app sau recreate, Nginx không restart trong kiểm tra persistence.
- Chạy `compose.yml` không phase3: Nginx cổng80; app5000 và PostgreSQL5432 không published; pgAdmin127.0.0.1:5050. Public/Private, chat/ảnh/file/notification đi qua proxy. Chặn metrics/status ở web; status8081 nội bộ dành cho GĐ5.
- HTTP200 và4headers, WebSocket nhóm/riêng hai chiều và polling, kiểm tra quyền/nonce/seen/thông báo. File đúng10 MiB gửi/tải cùng SHA256;10 MiB+1 bị Flask413 và request body>11 MiB bị Nginx413. `NGINX4_LIVE_CHECK_OK`.
- Sau recreate app qua proxy: `NOTIFICATIONS_PERSISTENCE_OK`, `NGINX4_PERSISTENCE_OK`, `MESSAGES34B_PERSISTENCE_OK`; dữ liệu/file/receipt/unread cũ giữ nguyên, C không truy cập được. Một lượt test đăng nhập dồn bị429 đúng giới hạn; helper kiểm thử được sửa để đợi7s rồi thử lại, không nới rate limit. Đã chạy lại đạt.
- `NGINX4_RATE_LIMIT_OK`: POST/login vượt10r/m với burst5 bị429, GETform vẫn200. Access log không ghi query string/Referer/cookie/body. Đây không phải mã hóa HTTP; chỉ dùng lab/mạng tin cậy.
- Hoàn thiện delivered nhóm: mọi thành viên đang trên trang khác nhận full envelope qua personal socket, không dùng preview toast làm bằng chứng nhận đủ nội dung. Hai test mới xác minh đủ nội dung/không trùng/người ngoài không nhận. Bản cuối **142 passed in61.84s** trên VM; cú pháp JS đạt.
- Trình duyệt ở `http://192.168.203.131/direct/2` đăng nhập được, lịch sử/ảnh cũ còn, trạng thái Đã kết nối qua proxy, không lỗi console. Ảnh thật `outputs/linhchat-gd4-nginx.jpg` (ignore).
- Hướng dẫn chụp một ảnh Terminal và đoạn báo cáo ngắn ở `docs/GD4_NGINX_VA_BAO_CAO.md`; `scripts/check-phase4.sh` in kiểm tra gọn không bí mật.
- Mốc1: `feat: milestone 1 - LinhChat, PostgreSQL and Nginx`. Lấy hash từ Git thay vì ghi hash vào chính nội dung commit. Không commit.env/work/outputs/configchi tiết monitoring/logging chưa chạy; không push GitHub.
- **Tiếp theo: chờ người dùng xác nhận đã chụp GĐ4, rồi GĐ5 monitoring**. Chưa chạy Prometheus/Grafana/Loki/Promtail, chưa commit2/3. Trước nộp cần người dùng chốt repo GitHub và triển khai đủ các giai đoạn còn lại.

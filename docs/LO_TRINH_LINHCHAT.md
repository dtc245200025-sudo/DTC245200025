# Lộ trình Đề 32 và yêu cầu mở rộng LinhChat

Giữ 8 giai đoạn của Đề 32, mở rộng Giai đoạn 3 thành các phần có thể kiểm tra và chụp minh chứng riêng. Giai đoạn 1–2 đã chạy đạt và đã chụp; Giai đoạn 3 cơ bản đã chạy nhưng phải bổ sung các yêu cầu mới trước mốc commit 1.

| Giai đoạn | Công việc và tiêu chí hoàn thành | Minh chứng |
|---|---|---|
| 1 Môi trường | Ubuntu VMware, Git, Docker Engine và Compose hoạt động | Phiên bản công cụ, hello-world; đã chụp |
| 2 Source và Flask | Source, Docker image, ứng dụng LinhChat màu hồng phấn và bộ kiểm thử cơ bản | Container Healthy, kiểm thử, trang đăng nhập; đã chụp bản cơ bản |
| 3.1 Tài khoản và giao diện | Đã triển khai trên VM: email bắt buộc khi tạo mới, đăng nhập tên hoặc email; trang chào hai lựa chọn; tài khoản góc dưới trái; sáng trắng/hồng và tối tím than; bổ sung email cho tài khoản cũ có xác nhận mật khẩu | 22/22 kiểm thử trong container đạt; đăng ký/email login và sáng/tối đã kiểm tra trình duyệt; chờ chụp ảnh |
| 3.2 Phòng chat | Đã triển khai trên VM: Public mới giới hạn 2–500 người gồm chủ phòng; Private chọn link mời/phê duyệt/mật khẩu; tìm/lọc phòng, duyệt và rời; kiểm tra quyền HTTP/Socket.IO | 55/55 kiểm thử; PostgreSQL/WebSocket thật, tranh chỗ cuối, giữ dữ liệu sau restart đạt; trình duyệt kiểm tra duyệt realtime và link qua đăng nhập; chờ chụp theo docs/GD32_PHONG_VA_MINH_CHUNG.md |
| 3.3a Hồ sơ (được ưu tiên theo yêu cầu mới) | Đã triển khai: hồ sơ của mình/người khác, tên hiển thị, username cố định, bio tối đa 150, ngày tham gia; avatar chữ/ảnh; public/private và quyền hiện email; menu avatar; tab Bảo mật và thu hồi phiên cũ; online/offline realtime | 38/38 kiểm thử; tích hợp PostgreSQL/WebSocket thật đạt; đã kiểm tra sáng/tối, menu Escape/bấm ngoài và hai tab; chờ chụp ảnh theo docs/PROFILE_VA_MINH_CHUNG.md |
| 3.3b Bạn bè | Đã triển khai trên VM: tìm theo tên/email đầy đủ; gửi/chấp nhận/từ chối/thu hồi lời mời, hủy kết bạn; danh sách/số lời mời/online-offline realtime; giữ riêng tư email | 70/70 kiểm thử và PostgreSQL/WebSocket thật đạt; trình duyệt xác nhận hai phía tự cập nhật; chụp một Hình 7 theo docs/GD33B_BAN_BE_VA_MINH_CHUNG.md |
| 3.4a Chat riêng và đang nhập | Đã triển khai trên VM: chat riêng từ Bạn bè, danh sách hội thoại/lịch sử PostgreSQL, đồng bộ lại và chống gửi trùng; chỉ hai tài khoản truy cập; đang nhập realtime ở riêng/nhóm | 98/98 kiểm thử, DIRECT34A_LIVE_CHECK_OK và DIRECT34A_PERSISTENCE_OK; trình duyệt hai chiều và sáng/tối đạt; một Hình 8 tùy chọn theo docs/GD34A_CHAT_RIENG_VA_MINH_CHUNG.md |
| 3.4b Tin nhắn nâng cao | Đã triển khai trên VM: đã nhận/đã xem và thời gian chi tiết; tìm tin/nội dung/tên tệp; emoji/gợi ý; ảnh/file tối đa 10 MiB cho nhóm/riêng, tải xuống kiểm tra quyền | 131/131 kiểm thử, MESSAGES34B_LIVE_CHECK_OK, MESSAGES34B_PERSISTENCE_OK; trình duyệt kiểm tra file/ảnh/emoji/thời gian/tìm kiếm/sáng-tối; tối đa một ảnh tổng hợp theo docs/GD34B_TIN_NHAN_VA_BAO_CAO.md |
| 4 Compose và Nginx | Đã triển khai: Nginx cổng 80, HTTP/WebSocket/polling, file đúng 10 MiB, thông báo, 4 headers, rate limit; app/DB không published; dữ liệu/file/unread còn sau recreate | 142/142 kiểm thử trên VM; NGINX4_LIVE_CHECK_OK, NGINX4_PERSISTENCE_OK, NGINX4_RATE_LIMIT_OK; commit 1; chờ một ảnh theo docs/GD4_NGINX_VA_BAO_CAO.md |
| 5 Monitoring | Metrics HTTP/chat/socket/upload theo ứng dụng thực tế; Prometheus, cAdvisor, exporter DB/Nginx, dashboard Grafana | Target UP, dashboard có dữ liệu, commit 2 |
| 6 Logging | Loki/Promtail thu log app/Nginx; truy vấn chat/upload/lỗi quyền; không ghi mật khẩu, nội dung file hoặc token mời | LogQL có dữ liệu thực tế, commit 3 |
| 7 Hardening | Kiểm tra non-root, mạng nội bộ, role DB hạn chế, secret; session/CSRF; quyền phòng và file riêng tư; kiểm tra kích thước/nội dung upload; headers, rate limit và HTTPS nếu đề yêu cầu | Các kiểm tra cho phép/từ chối, Docker và HTTP headers |
| 8 README Demo Báo cáo | Hướng dẫn bản cuối, sơ đồ dữ liệu cập nhật, kịch bản demo, ảnh đúng phiên bản LinhChat, báo cáo theo file đề gốc | README, lịch sử 3 mốc commit, minh chứng và báo cáo |

## Ba mốc commit

1. Hoàn tất 3.1–3.4 và Giai đoạn 4: ứng dụng, PostgreSQL, pgAdmin và Nginx chạy đạt.
2. Giai đoạn 5: monitoring chạy đạt.
3. Giai đoạn 6: logging chạy đạt.

Các biện pháp bảo vệ dữ liệu được triển khai cùng tính năng; Giai đoạn 7 là bước kiểm tra hardening tổng thể. Không commit `.env`, mật khẩu demo, dữ liệu upload, backup hoặc file riêng tư. Mốc 1: `feat: milestone 1 - LinhChat, PostgreSQL and Nginx`; xem hash bằng `git log -1 --oneline`. Chưa push GitHub, cần chốt repository đích. Trí nhớ cập nhật ở `MEMORY.md` và `docs/memory/`.

## Quy ước kiểm tra và ảnh

Sau mỗi phần chạy đạt, cung cấp lệnh/màn hình cần chụp, tên ảnh và đoạn mô tả báo cáo. Đợi người dùng xác nhận đã chụp trước khi chuyển sang phần tiếp theo có thể làm thay đổi màn hình. Ảnh Giai đoạn 1 vẫn dùng được; ảnh giao diện cuối phải phản ánh phiên bản LinhChat hiện tại.

Tài khoản cũ và tin nhắn PostgreSQL được giữ. Tài khoản cũ chưa có email sẽ bổ sung email qua màn hình tài khoản, không tự gán địa chỉ giả. Chưa gửi email xác thực hoặc cấu hình SMTP nếu người dùng chưa yêu cầu. Đã đọc file Đề bài va Yêu cầu.docx: giữ ba mốc commit ứng dụng/Nginx, monitoring và logging; các tính năng Bạn bè/Profile/tin nhắn nâng cao bổ sung theo yêu cầu người dùng.

## Kết quả và ảnh Giai đoạn 3.1

Đã sao lưu database/source trước nâng cấp trong `work/backups` trên VM. Sau migration vẫn có đủ 4 tài khoản và 8 tin nhắn cũ; chỉ bổ sung cột email và index chống trùng email. Tài khoản tạo riêng để kiểm thử giao diện không phải tài khoản thật của người dùng.

Trên Ubuntu mở `http://localhost:5000/login` và nhấn Ctrl+F5. Tài khoản demo cũ vẫn đăng nhập bằng tên/mật khẩu trong `work/gd3-demo-access.txt`. Để đăng nhập email, vào Tài khoản, nhập email của mình và mật khẩu hiện tại rồi lưu.

- `GD3.1-01-email.png`: form Tạo tài khoản có trường Email; không chụp mật khẩu hiển thị.
- `GD3.1-02-trang-chu-sang.png`: trang chào đúng nội dung, hai ô tạo/tìm phòng và tài khoản góc dưới trái ở chế độ sáng.
- `GD3.1-03-trang-chu-toi.png`: cùng trang chào sau khi bấm Chế độ tối; màu tím than. Tùy chọn được ghi nhớ khi tải lại.

Có thể chạy `bash scripts/check-phase31.sh` để chụp kiểm thử và schema email; bộ kiểm thử tăng từ 22 lên 38 sau Profile, 55 sau phòng Public/Private và 70 sau Bạn bè. Hiện còn chờ 3.4 tin nhắn nâng cao.

## Kết quả và ảnh Giai đoạn 3.3a – Profile

Ưu tiên thực hiện Profile theo hai ảnh tham khảo mới của người dùng, giữ màu LinhChat trắng/hồng phấn và tối tím than. Đã triển khai trên VM và đạt 38 kiểm thử trong container, PROFILE_LIVE_CHECK_OK, LIVE_CHAT_CHECK_OK và kiểm tra lịch sử PostgreSQL cũ. Sao lưu trước migration; không thay mật khẩu tài khoản demo của người dùng.

Hướng dẫn thao tác, ảnh cần chụp, chú thích và nội dung báo cáo ở `docs/PROFILE_VA_MINH_CHUNG.md`. Mở `http://localhost:5000/profile` trong Ubuntu và Ctrl+F5. Chạy `bash scripts/check-profile.sh` để chụp kết quả kiểm thử. Sau đó đã tiếp tục 3.2 theo yêu cầu người dùng.

## Kết quả và ảnh Giai đoạn 3.2 – Phòng Public/Private

Đã hoàn thành trên Ubuntu VMware: 55/55 kiểm thử, ROOMS32_LIVE_CHECK_OK, ROOMS32_PERSISTENCE_OK và PERSISTENCE_AFTER_RESTART_OK. Có backup trước migration; sau bổ sung schema vẫn đủ 9 tài khoản, 4 phòng và 12 tin nhắn cũ trước khi thêm dữ liệu kiểm thử. Phòng cũ tiếp tục Public không giới hạn; giới hạn bắt buộc áp dụng cho Public mới.

Hướng dẫn ảnh và nội dung báo cáo: `docs/GD32_PHONG_VA_MINH_CHUNG.md`. Đã chuẩn bị A/B/C và bốn phòng `GD3.2`; thông tin riêng tại `work/gd32-demo-access.txt` trên VM, không chụp mật khẩu/link. Chạy `bash scripts/check-phase32.sh`. Đợi xác nhận đã chụp 3.2 rồi tiếp tục 3.3b (Bạn bè).

## Kết quả Giai đoạn 3.3b – Bạn bè

Đã hoàn thành trên VMware, đạt 70 kiểm thử và FRIENDS33B_LIVE_CHECK_OK. Có sao lưu trước nâng cấp; khi tạo bảng friendships vẫn đủ 13 tài khoản, 10 phòng và 15 tin nhắn cũ trước khi thêm dữ liệu thử. Thử hai lời mời ngược chiều đồng thời trên PostgreSQL chỉ tạo một quan hệ và vẫn yêu cầu người nhận chấp nhận. Trình duyệt xác nhận lời mời/danh sách cập nhật không tải lại, online/offline và sáng/tối.

Hướng dẫn ngắn, một ảnh và chú thích báo cáo: `docs/GD33B_BAN_BE_VA_MINH_CHUNG.md`. Chờ chụp trước khi tiếp tục 3.4; chưa chuyển sang Nginx hay tạo commit mốc 1.

## Kết quả Giai đoạn 3.4a – Chat riêng và đang nhập

Đã triển khai trên VMware theo yêu cầu tiếp tục của người dùng. Đạt 98/98 kiểm thử; DIRECT34A_LIVE_CHECK_OK xác nhận HTTP/PostgreSQL/WebSocket thật, chỉ hai tài khoản nhận sự kiện, tạo đồng thời không trùng hội thoại, gửi lại không trùng tin và người thứ ba bị chặn. Trạng thái đang nhập có ở phòng nhóm/chat riêng; không truyền bản nháp. Trình duyệt kiểm tra hai chiều, tên người đang nhập, sáng/tối và không có lỗi console.

Ở mốc 3.4a có backup trước nâng cấp; khi tạo hai bảng mới vẫn đủ 16 tài khoản, 10 phòng, 15 tin nhắn nhóm cũ. Sau restart đạt DIRECT34A_PERSISTENCE_OK, FRIENDS33B_PERSISTENCE_OK, ROOMS32_PERSISTENCE_OK, PERSISTENCE_AFTER_RESTART_OK; kiểm tra chat nhóm hai chiều thật LIVE_CHAT_CHECK_OK đạt. Sau đó đã hoàn thành 3.4b và gộp minh chứng theo tài liệu bên dưới.

## Kết quả Giai đoạn 3.4b – Tin nhắn nâng cao

Đã hoàn thành trên VMware: 131/131 kiểm thử, MESSAGES34B_LIVE_CHECK_OK và MESSAGES34B_PERSISTENCE_OK. Có nhận/xem theo xác nhận thực tế, thời gian chi tiết, tìm nội dung/tên tệp, emoji/chọn/gợi ý, ảnh/file 10 MiB và kiểm tra quyền tải xuống cho chat nhóm/riêng. Tin cũ giữ nguyên, không tạo lịch sử nhận/xem giả; file và thời gian còn sau tạo lại app. Đã thay hai module chat cũ bằng luồng dùng chung; bản cũ có trong backup source trên VM.

Đã đọc nội dung Demo.docx: có ảnh ứng dụng, PostgreSQL/Compose, Bạn bè/Profile và trùng chú thích Hình 7; không sửa file gốc, chưa xác minh dàn trang vì thiếu LibreOffice trong runtime tài liệu. Hướng dẫn thêm/thay một ảnh và đoạn báo cáo ở docs/GD34B_TIN_NHAN_VA_BAO_CAO.md. Sau đó hoàn thiện thông báo tin mới (người dùng xác nhận đã thấy) và GĐ4 theo mục mới bên dưới.

## Kết quả Giai đoạn 4 Nginx

Đã chạy trên VMware, 142/142 test bản cuối và các kiểm tra qua Nginx thật đạt. WebSocket nhóm/riêng, polling fallback, notification/unread, tệp đúng 10 MiB và giới hạn vượt, quyền và headers/rate limit đều được kiểm tra. Sau recreate app không restart Nginx, tin/file/receipts/unread cũ còn. Chỉ dùng Compose chính, URL `http://localhost` trong Ubuntu, cổng app :5000 đã đóng published. pgAdmin vẫn localhost:5050.

Đã tạo file trí nhớ yêu cầu/mục tiêu/ý tưởng/tiến trình/checklist theo yêu cầu người dùng, không có secret. Chờ chụp một ảnh Terminal từ tiêu đề GĐ4 đến `GIAI_DOAN_4_OK` bằng `bash scripts/check-phase4.sh`, hướng dẫn và đoạn báo cáo ở `docs/GD4_NGINX_VA_BAO_CAO.md`. Sau xác nhận chụp mới triển khai GĐ5 monitoring/commit 2; logging/commit 3 còn sau đó.

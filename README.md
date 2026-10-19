# Đề 32 Hệ thống Chat Messaging

## Trạng thái mới nhất

Giai đoạn 1–7 đã chạy đạt trên Ubuntu VMware. Người dùng đã gửi ảnh GĐ6 hợp lệ và yêu cầu GĐ7 ngày 19/10/2026. Hiện 11 service hoạt động; trong Docker chỉ Nginx public80, app/DB không published, các cổng quản trị bind localhost. GĐ7 đạt 152/152 test, audit hạ tầng/HTTP/WebSocket; hướng dẫn **một ảnh Terminal** và đoạn báo cáo ở `docs/GD7_HARDENING_VA_BAO_CAO.md`. Chờ chụp GĐ7 trước GĐ8.

Trí nhớ dự án: đọc `MEMORY.md`, yêu cầu/ý tưởng ở `docs/memory/REQUIREMENTS.md`, tiến trình ở `docs/memory/PROGRESS.md`, checklist ở `docs/memory/CHECKLIST.md`. Cập nhật sau mỗi giai đoạn. Không lưu secret trong các file này. Người dùng đã xác nhận thông báo tin nhắn mới hoạt động. Unread được lưu theo receipt trong PostgreSQL; toast/badge cập nhật trên mọi trang, nhận đầy đủ tin mới xác nhận delivered; GET và đóng toast không đánh dấu seen.

Bản GĐ7 đạt 152/152 test trên VM, HARDENING_INFRA_OK/HARDENING_LIVE_OK, NGINX4_RATE_LIMIT_OK và MESSAGES34B_PERSISTENCE_OK. Monitoring 5/5 UP, 11 panel/11 service; logging 3 LogQL vẫn có dữ liệu. GĐ6 đạt146/GĐ5 đạt143/GĐ4 đạt142 là kết quả lịch sử. Giữ nguyên ba commit mốc; bản fix hardening được lưu riêng, không rewrite. Xem `git log --oneline` hoặc `git log --oneline --grep='^feat: milestone '` để lọc ba mốc; chưa push.

GĐ8 bàn giao cuối còn chờ; các số test trong phần lịch sử không phải bộ mới nhất. Chưa chốt repository GitHub, không tự push. GĐ7 là audit cấu hình/lab, không phải chứng nhận an toàn hoặc quét mọi CVE; HTTP chưa TLS, cAdvisor/Promtail có ngoại lệ quyền mạnh.

## Mở rộng LinhChat

Lộ trình cập nhật ở `docs/LO_TRINH_LINHCHAT.md`. Giai đoạn 3 chia thành 3.1 Tài khoản và giao diện, 3.2 Phòng chat, 3.3 Bạn bè và hồ sơ, 3.4 Tin nhắn nâng cao, rồi tiếp tục Nginx/monitoring/logging/hardening/báo cáo.

Phần 3.1 đã chạy đạt trên VMware: tạo tài khoản có email, đăng nhập bằng tên/email, bổ sung email cho tài khoản cũ qua `/account`, trang chào hai lựa chọn và giao diện sáng/tối. Chưa có SMTP hoặc email xác thực.

Phần 3.3a Hồ sơ được ưu tiên theo yêu cầu giao diện mới: `/profile` có tên hiển thị, username cố định, giới thiệu tối đa 150 ký tự, ngày tham gia, avatar chữ/ảnh và quyền hiển thị hồ sơ/email. Menu avatar góc phải đóng bằng Escape hoặc bấm bên ngoài. Tab Bảo mật kiểm tra mật khẩu hiện tại, hash mật khẩu mới bằng Werkzeug và thu hồi phiên HTTP/WebSocket cũ. Xem hồ sơ người khác bằng cách bấm tên người gửi trong phòng chat. Upload avatar chỉ nhận ảnh JPG/PNG/WebP tối đa 10 MiB, kiểm tra nội dung, thu nhỏ và loại metadata trước khi lưu PostgreSQL. Bộ kiểm thử hiện tại đạt 38/38 trong container trên VM; luồng hồ sơ và chat hai chiều được kiểm tra bằng WebSocket thật. Xem `docs/PROFILE_VA_MINH_CHUNG.md` và chạy `bash scripts/check-profile.sh` để chụp kết quả.

Phần 3.2 đã chạy đạt: Public mới giới hạn 2–500 người (gồm chủ phòng), Private chọn mật khẩu/phê duyệt/link mời, tìm phòng và lọc phòng đã tham gia, xử lý yêu cầu, tạo/thay link và rời phòng. HTTP và Socket.IO kiểm tra quyền; PostgreSQL khóa dòng khi cấp chỗ. Mật khẩu phòng được hash, token mời chỉ lưu hash; link dùng fragment để không đưa token vào HTTP access log. Đạt 55/55 kiểm thử trên VM, ROOMS32_LIVE_CHECK_OK và ROOMS32_PERSISTENCE_OK sau restart. Xem `docs/GD32_PHONG_VA_MINH_CHUNG.md`; chạy `bash scripts/check-phase32.sh`. Tài khoản minh chứng lưu riêng `work/gd32-demo-access.txt` trên VM (quyền 600), không in vào log/Git.

Phần 3.3b Bạn bè đã triển khai: tìm theo username/tên hiển thị hoặc email đầy đủ; gửi/chấp nhận/từ chối/thu hồi lời mời và hủy kết bạn. Danh sách, số lời mời và online/offline cập nhật realtime, có kiểm tra quyền và CSRF. PostgreSQL chỉ lưu một quan hệ cho mỗi cặp; hai lời mời ngược chiều không tự động chấp nhận. Email riêng tư không hiện trên kết quả; từ khóa tìm kiếm gửi bằng POST để tránh vào URL/access log. Đạt 70/70 kiểm thử trên VM và FRIENDS33B_LIVE_CHECK_OK qua PostgreSQL/WebSocket thật. Xem `docs/GD33B_BAN_BE_VA_MINH_CHUNG.md`; chạy `bash scripts/check-friends.sh`. Tài khoản minh chứng lưu riêng `work/gd33b-demo-access.txt` trên VM, không chụp mật khẩu.

Phần 3.4a đã triển khai: chat riêng từ nút Nhắn tin trong Bạn bè, danh sách hội thoại `/direct`, lịch sử riêng hai tài khoản, xem tin cũ và đồng bộ sau kết nối lại. Cần là bạn bè để gửi mới; hủy kết bạn vẫn xem được lịch sử, không xóa tin. Mã gửi chống trùng khi thử lại; nội dung được lưu PostgreSQL trước khi xác nhận. Có trạng thái đang nhập ở chat riêng và phòng nhóm; không gửi/lưu bản nháp, tự tắt khi ngừng gõ hoặc mất kết nối. Đạt 98/98 kiểm thử trên VM, DIRECT34A_LIVE_CHECK_OK và DIRECT34A_PERSISTENCE_OK. Xem `docs/GD34A_CHAT_RIENG_VA_MINH_CHUNG.md`; kiểm tra bằng `bash scripts/check-direct.sh`. Tài khoản minh chứng riêng tại `work/gd34a-demo-access.txt` trên VM, quyền 600.

Phần 3.4b đã triển khai trên VMware: xác nhận đã nhận/đã xem realtime, bấm tin hoặc nút ⓘ xem thời gian, tìm theo nội dung/tên tệp, chọn và gợi ý emoji (`:cuoi`), ảnh/file tối đa 10 MiB cho nhóm và riêng. Nhận là xác nhận từ trình duyệt, không suy đoán từ online; xem khi tin hiện trong khung chat được mở/focus. Tin lịch sử cũ không được tạo thời gian giả. Phòng nhóm hiển thị số người nhận/xem trên tổng người nhận tại lúc gửi; người tham gia sau không được ghi xác nhận cho tin cũ. Nội dung tìm kiếm dùng POST, không nằm trong URL.

Tệp gốc và ảnh xem trước lưu PostgreSQL, không ghi vào filesystem container. Mỗi lần chỉ gửi một tệp; tệp thường luôn tải bằng attachment/octet-stream/nosniff, ảnh JPG/PNG/WebP được kiểm tra nội dung và tạo preview PNG tối đa 1600px/16 triệu điểm ảnh. Chỉ người có quyền lịch sử tải được; rời phòng mất quyền tải, hủy kết bạn vẫn giữ quyền lịch sử riêng. Không có quét mã độc hoặc mã hóa đầu-cuối. Đạt 131/131 kiểm thử trên VM, MESSAGES34B_LIVE_CHECK_OK và MESSAGES34B_PERSISTENCE_OK; trình duyệt đã kiểm tra emoji/gợi ý, tìm tin, tải tệp, ảnh, thời gian và sáng/tối. Xem `docs/GD34B_TIN_NHAN_VA_BAO_CAO.md`; chạy `bash scripts/check-messages.sh`. Tài khoản minh chứng riêng trong `work/gd34b-demo-access.txt` trên VM (quyền 600), không chụp mật khẩu.

Sau tạo lại app, MESSAGES34B_PERSISTENCE_OK, DIRECT34A_PERSISTENCE_OK, FRIENDS33B_PERSISTENCE_OK, ROOMS32_PERSISTENCE_OK và PERSISTENCE_AFTER_RESTART_OK xác nhận file, trạng thái, chat riêng, bạn bè, phòng và lịch sử vẫn còn. Các migration chỉ bổ sung schema, giữ dữ liệu cũ; phòng cũ tiếp tục Public không giới hạn. Sau đó đã triển khai Nginx GĐ4 theo mục trạng thái mới nhất.

Ứng dụng chat nội bộ có đăng ký, đăng nhập, tạo và tham gia phòng, nhắn tin realtime và lưu lịch sử trong PostgreSQL. Toàn bộ hệ thống được đóng gói bằng Docker Compose cho Ubuntu trong VMware.

Giai đoạn1–6 đã chạy trên Ubuntu VMware. Đã đối chiếu đề gốc; Bạn bè/Profile/tin nhắn nâng cao là phần mở rộng theo yêu cầu người dùng. Đã đọc nội dung Demo.docx để hướng dẫn báo cáo gọn; chưa sửa file Word hoặc xác minh dàn trang. Xem `docs/THUC_HANH_VMWARE.md` để thực hành và chụp ảnh.

Bản xem thử Giai đoạn 2 dùng `docker compose -f compose.phase2.yml up -d --wait`, mở `http://localhost:5000/login` trong Ubuntu rồi chạy `bash scripts/check-phase2.sh`. Database bản xem thử nằm trong bộ nhớ và mất khi container dừng. Bản triển khai chính bên dưới dùng PostgreSQL qua `compose.yml`.

Ở Giai đoạn 3, bản xem thử đã dừng. App PostgreSQL được mở tạm tại localhost:5000 bằng `docker compose -f compose.yml -f compose.phase3.yml up -d --wait postgres app pgadmin`. `bash scripts/check-phase3.sh` hiển thị kết quả và dữ liệu minh chứng. Tài khoản demo được lưu tại `work/gd3-demo-access.txt` với quyền 600 trên VM, không nằm trong Git. Khi chuyển sang Nginx ở Giai đoạn 4, bỏ override phase3 để đóng cổng truy cập trực tiếp app.

## Kiến trúc

- Flask và Flask-SocketIO: web app và realtime chat.
- PostgreSQL và pgAdmin: lưu và quản trị dữ liệu.
- Nginx: reverse proxy HTTP và WebSocket.
- Prometheus, cAdvisor, PostgreSQL exporter, Nginx exporter: thu thập metrics.
- Grafana: dashboard và truy vấn log.
- Loki và Promtail: tập trung log container.

## Yêu cầu Ubuntu VM

Khuyến nghị Ubuntu 22.04 hoặc 24.04, 4 CPU, 8 GB RAM và tối thiểu 20 GB trống. Chỉ cần cài Git, Docker Engine và Docker Compose plugin; các thành phần còn lại chạy trong container.

Kiểm tra môi trường:

```bash
chmod +x scripts/*.sh postgres/init/*.sh
./scripts/check-ubuntu.sh
```

Nếu Docker chưa có, cài theo tài liệu chính thức: <https://docs.docker.com/engine/install/ubuntu/>. Sau khi thêm tài khoản vào nhóm `docker`, đăng xuất rồi đăng nhập lại trước khi chạy kiểm tra.

## Khởi chạy

```bash
bash scripts/init-env.sh
docker compose config --quiet
docker compose --profile monitoring --profile logging up -d --build
docker compose --profile monitoring --profile logging ps
```

Script tạo secret ngẫu nhiên và không ghi đè `.env` đã có. Nếu dùng `.env.example` thủ công, phải thay toàn bộ giá trị `change_me_...`. Không commit hoặc chụp ảnh `.env`. Lệnh `config --quiet` tránh in secret.

| Thành phần | Địa chỉ |
|---|---|
| Ứng dụng qua Nginx | `http://IP_UBUNTU_VM/` |
| pgAdmin trong trình duyệt Ubuntu | `http://localhost:5050/` |
| Grafana trong trình duyệt Ubuntu | `http://localhost:3000/` |
| Prometheus trong trình duyệt Ubuntu | `http://localhost:9090/` |

Lấy IP Ubuntu bằng `hostname -I`. Với VMware Bridged, dùng địa chỉ đó từ trình duyệt máy thật. Với NAT, mở trình duyệt trong Ubuntu hoặc cấu hình port forwarding.

Các trang quản trị mặc định chỉ mở tại localhost Ubuntu. Để truy cập từ Windows khi đã có SSH, mở tunnel `ssh -L 5050:localhost:5050 -L 3000:localhost:3000 -L 9090:localhost:9090 USER@IP_VM` rồi dùng `localhost` trong trình duyệt Windows.

## Kiểm tra chức năng

1. Mở hai cửa sổ riêng tư, tạo hai tài khoản.
2. Tài khoản thứ nhất tạo phòng `General`; cả hai cùng mở phòng.
3. Gửi tin nhắn ở cửa sổ thứ nhất và kiểm tra cửa sổ thứ hai nhận ngay.
4. Mở pgAdmin, kết nối host `postgres`, port `5432`, database `chatdb`, tài khoản `chatuser` và mật khẩu `APP_DB_PASSWORD` trong `.env`; kiểm tra `users`, `rooms`, `room_members`, `messages`.
5. Chạy `bash scripts/smoke-test.sh` sau khi bật monitoring. Bộ test tích hợp cục bộ không thay thế kiểm tra PostgreSQL thực tế.

## Monitoring

Giai đoạn5 đã chạy đạt. Khởi động bằng `docker compose --profile monitoring up -d`. Prometheus scrape5job mỗi15giây; Grafana có datasource Prometheus và dashboard **LinhChat Overview** trong folder **LinhChat**. Xem riêng thông tin đăng nhập tại `work/grafana-access.txt` trên VM; không chụp mật khẩu. Hướng dẫn đăng nhập/chụp/báo cáo ở `docs/GD5_MONITORING_VA_BAO_CAO.md`.

```promql
sum(chat_http_requests_total)
sum(chat_messages_total) + sum(chat_direct_messages_total)
pg_up
nginx_up
```

## Logging

Giai đoạn6 đã chạy đạt. Khởi động phần đã làm bằng `docker compose --profile monitoring --profile logging up -d`. Grafana Explore chọn **Loki**, chuyển **Code**, Last15minutes và chạy3truyvấn:

```logql
{service="app"} |~ "chat_message_saved|direct_message_saved|chat_attachment_saved"
{service="nginx"} | json | route="/healthz" | status=200
{service="app"} | json | event="http_request_rejected" | status>=400
```

Promtail đã ngừng vòng đời upstream nhưng vẫn được giữ theo stack người dùng đã chốt. Tham khảo [Grafana Promtail](https://grafana.com/docs/loki/latest/send-data/promtail/).

Hướng dẫn đầy đủ và giới hạn: `docs/GD6_LOGGING_VA_BAO_CAO.md`. Loki/Promtail có volume dữ liệu/positions, giới hạnRAM512m/128m; retention7ngày là cấu hình, không là giới hạndiskfree. Promtail bỏ replay>1h; không cam kết lưu đủ log khi ngừng lâu. Chỉ curatedaudit app/Nginx, không toàn bộ stacktrace/DBlogs. Docker socketro vẫn cấp quyền mạnh. Kiểm tra lại bằng `bash scripts/check-phase6.sh`; cần log mới để chụp thì `bash scripts/prepare-phase6-evidence.sh` (tạo thêm dữ liệu synthetic, không xóa cũ).

## Hardening đã kiểm tra trên VM

GĐ7 đã xác minh các mục bên dưới trong phạm vi lab bằng Docker inspect/process status, PostgreSQL, HTTP và WebSocket. Chạy `bash scripts/check-phase7.sh` để kiểm tra hạ tầng/header hiện tại và đối chiếu bằng chứng live đã lưu với image app/cấu hình Nginx. Logout hiện thu hồi **tất cả phiên của cùng tài khoản**, không ảnh hưởng người khác; nút Thoát/menu có tooltip giải thích. Header proxy được chuẩn hóa, không gửi hai giá trị nosniff trùng nhau. Giới hạn và hướng dẫn ảnh: `docs/GD7_HARDENING_VA_BAO_CAO.md`.

- App chạy bằng UID/GID không phải root.
- Mật khẩu và secret nằm trong `.env`, file này bị Git bỏ qua.
- Mạng backend là internal; PostgreSQL không publish port ra host.
- App và Nginx dùng filesystem read-only, `no-new-privileges`, bỏ Linux capabilities và dùng `tmpfs` cho dữ liệu tạm.
- Cookie có `HttpOnly`, `SameSite=Lax`; form có CSRF token; mật khẩu được hash.
- Nginx có security headers, ẩn version và giới hạn tốc độ đăng nhập.
- Tài khoản exporter PostgreSQL chỉ nhận `pg_monitor`.
- App sử dụng role `chatuser` riêng, không dùng tài khoản quản trị PostgreSQL. Cookie Secure cần HTTPS; bản demo HTTP chưa bật Secure.

cAdvisor và Promtail cần quyền truy cập host để đọc metrics/log Docker. Đây là ngoại lệ có chủ đích; không mở các dịch vụ này ra host.

## Ba mốc commit

Đủ ba mốc đã chạy đạt trên Ubuntu VM, lưu cùng lịch sử Windows/VM; lọc bằng `git log --oneline --grep='^feat: milestone '`. Bản sửa hardening GĐ7 lưu commit riêng sau ba mốc, không amend/rebase. GĐ8 còn bàn giao báo cáo cuối; không tự push khi chưa chốt repository.

```text
Commit 1: feat: milestone 1 - LinhChat, PostgreSQL and Nginx
Commit 2: feat: milestone 2 - Prometheus and Grafana monitoring
Commit 3: feat: milestone 3 - Loki and Promtail centralized logging
```

Không dùng `git add .env` và luôn kiểm tra `git status` trước khi commit.

## Dừng và khôi phục

```bash
docker compose --profile monitoring --profile logging down
docker compose --profile monitoring --profile logging up -d
```

Không dùng `docker compose down -v` nếu muốn giữ dữ liệu PostgreSQL, Grafana và Prometheus.

Các script khởi tạo PostgreSQL chỉ chạy khi volume database mới. Thay mật khẩu trong `.env` sau lần khởi tạo không tự thay mật khẩu trong database. Cần xử lý bằng ALTER ROLE; không xóa volume để sửa lỗi khi đã có dữ liệu cần giữ.

Gunicorn sử dụng một worker và 100 threads cùng `simple-websocket`, theo [tài liệu Flask-SocketIO](https://flask-socketio.readthedocs.io/en/latest/deployment.html). Bản này dành cho demo một instance; chưa có cơ chế Redis để chạy nhiều instance.

# Thực hành Đề 32 trên Ubuntu trong VMware

Thực hiện theo thứ tự. Sau mỗi giai đoạn, giữ cửa sổ kết quả để chụp ảnh rồi xác nhận trong cuộc trò chuyện. Trạng thái mới nhất và checklist ở `MEMORY.md` và `docs/memory/`; các mục cũ bên dưới mô tả từng mốc lịch sử, không chạy lại để chụp khi đã chuyển giai đoạn.

## Giai đoạn 1 Kiểm tra Ubuntu Git Docker

Trong Terminal Ubuntu:

```bash
cat /etc/os-release
hostname -I
nproc
free -h
df -h /
git --version
docker --version
docker compose version
docker info --format 'Docker daemon {{.ServerVersion}}'
```

Ảnh `01-moi-truong.png`: hiển thị Ubuntu, phiên bản Git/Docker/Compose và Docker daemon truy cập được. Nếu thiếu lệnh hoặc permission denied, gửi nguyên thông báo lỗi trước khi chuyển giai đoạn.

Nếu cần truy cập từ máy Windows, bật Ubuntu VM và cung cấp IP, username, cổng SSH. Với Ubuntu chưa có SSH:

```bash
sudo apt update
sudo apt install openssh-server
sudo systemctl enable --now ssh
systemctl is-active ssh
hostname -I
```

Lệnh cài đặt cần thực hiện trong Ubuntu. Nếu UFW đang bật, chỉ cho IP Windows truy cập SSH theo chính sách mạng của bạn. Không gửi mật khẩu trong chat. Có thể chuyển source bằng Shared Folders của VMware khi chưa có SSH.

Tài liệu Docker chính thức: https://docs.docker.com/engine/install/ubuntu/

## Chuyển project sang Ubuntu

Tải và giải nén `de32-chat-source.zip`. Trong VMware, dùng Shared Folders hoặc kéo thả nếu VMware Tools đã hỗ trợ, rồi sao chép toàn bộ thư mục project vào `~/projects/de32-chat`. Giữ nguyên các file bắt đầu bằng dấu chấm.

Mở Terminal trong thư mục đó:

```bash
cd ~/projects/de32-chat
git init -b main
bash scripts/check-ubuntu.sh
bash scripts/init-env.sh
```

Không chụp nội dung `.env`; không gửi `.env` vào chat. Tất cả secret được tạo ngẫu nhiên và lưu ở đó.

## Giai đoạn 2 Source và Flask

```bash
find app -maxdepth 3 -type f | sort
docker compose build app
docker compose -f compose.phase2.yml up -d --wait
bash scripts/check-phase2.sh
```

Ảnh `03-flask-tests.png`: chạy `clear` rồi `bash scripts/check-phase2.sh`, chụp từ tiêu đề Giai đoạn 2 đến dòng `GIAI_DOAN_2_OK`, gồm container Healthy, `13 passed`, health OK và HTTP 200. Những test này dùng SQLite trong bộ nhớ, xác minh chức năng Python; không phải minh chứng PostgreSQL.

Ảnh `04-flask-dang-nhap.png`: mở `http://localhost:5000/login` trong trình duyệt Ubuntu; chụp cả thanh địa chỉ và form đăng nhập. Giữ container xem thử hoạt động cho tới khi đã chụp ảnh; sẽ dừng khi bắt đầu Giai đoạn 3.

## Giai đoạn 3 Chat realtime và PostgreSQL

```bash
docker compose -f compose.phase2.yml stop app
docker compose -f compose.yml -f compose.phase3.yml up -d --wait postgres app pgadmin
bash scripts/check-phase3.sh
```

App PostgreSQL mở tạm tại `http://localhost:5000/login` trong trình duyệt Ubuntu. Đã kiểm tra hai client WebSocket thật, tin nhắn lưu trong PostgreSQL và lịch sử còn sau restart app.

Ảnh `05-chat-realtime.png`: xem riêng thông tin tài khoản bằng `cat work/gd3-demo-access.txt`, không chụp mật khẩu. Đăng nhập tài khoản A trong cửa sổ thường và tài khoản B trong cửa sổ riêng tư, vào cùng phòng được ghi trong file, gửi qua lại tin nhắn. Chụp hai cửa sổ cùng phòng, có tên người gửi và tin nhắn giống nhau.

Ảnh `06-postgresql-du-lieu.png`: sau khi gửi tin nhắn, chạy `clear` rồi `bash scripts/check-phase3.sh`. Chụp phần `CAC BANG DU LIEU`, bốn bảng, `CAC TIN NHAN DA LUU TRONG POSTGRESQL` và các dòng dữ liệu. Phóng to cửa sổ Terminal để chứa đủ hai bảng kết quả.

Xác minh database riêng:

```bash
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"'
```

Kết quả cần có `users`, `rooms`, `room_members`, `messages` và owner là `chatuser`. Ở Giai đoạn 4 sẽ kiểm tra lại chat qua Nginx.

## Giai đoạn 4 Compose và Nginx

```bash
cd ~/projects/de32-chat
clear
bash scripts/check-phase4.sh
```

Mở `http://localhost` trong Ubuntu, không thêm `:5000`; từ Windows dùng IP VM cổng80. Cổng app5000 đã đóng published. Dùng tài khoản/phòng/hội thoại hiện có; không cần đăng ký lại hoặc xóa dữ liệu. pgAdmin vẫn ở `http://localhost:5050` trong Ubuntu.

Một ảnh chính: Terminal từ tiêu đề GĐ4 tới `GIAI_DOAN_4_OK`, gồm `nginx -t` thành công, HTTP200, headers,4container và cổng. Ảnh hai cửa sổ chat qua địa chỉ mới là tùy chọn để giữ báo cáo10–15trang. Hướng dẫn và đoạn báo cáo ngắn: `docs/GD4_NGINX_VA_BAO_CAO.md`.

pgAdmin/SQL đã có ảnh ở GĐ3 nên không cần lặp. Mốc commit1 là ứng dụng + PostgreSQL/pgAdmin + Nginx đã kiểm tra; không đẩy GitHub tự động khi chưa chốt repository. Monitoring/logging chưa chạy, không gắn nhãn hoàn thành ở mốc1.

## Giai đoạn 5 Monitoring

```bash
docker compose --profile monitoring up -d
docker compose --profile monitoring ps
curl -f http://localhost:9090/-/ready
```

GĐ5 đã chạy đạt trên VM. Mở `http://localhost:9090/targets`, cả5target phải `UP`. Mở Grafana `http://localhost:3000`, đăng nhập bằng tài khoản xem riêng tại `work/grafana-access.txt` (không chụp mật khẩu), rồi mở **Dashboards → LinhChat → LinhChat Overview**. Có thể vào thẳng `http://localhost:3000/d/linhchat-overview` sau đăng nhập.

Gửi thêm tin nhắn để số tin nhóm/riêng tăng; đây là bộ đếm từ lúc app chạy, không phải tổng hàng lịch sử trong database. CPU dùng rate2phút; nếu vừa khởi động, chờ30–60giây để có hai mẫu. Chọn Last15minutes và làm mới15s. Socket=0 khi không ai mở LinhChat là hợp lệ.

Ảnh `gd5-prometheus-targets.png`: đủ5target UP. Ảnh `gd5-grafana-dashboard.png`: có dữ liệu app, DB, Nginx, CPU/RAM9service. Không chụp dashboard trống. Mốc2 đã lưu sau143/143test, kiểm tra activity/persistence và trình duyệt. Hướng dẫn kỹ, chú thích, đoạn báo cáo ngắn: `docs/GD5_MONITORING_VA_BAO_CAO.md`. Chạy `bash scripts/check-phase5.sh` nếu cần kiểm tra lại; không cần thêm ảnh Terminal.

## Giai đoạn 6 Logging

Đã chạy đạt sau khi người dùng xác nhận chụpGĐ5:146/146test,3LogQL,canary/persistence và monitoring11service. Hướng dẫn một ảnh chính/một ảnh tùy chọn, chuẩn bị log mới và đoạn báo cáo ở `docs/GD6_LOGGING_VA_BAO_CAO.md`.

```bash
docker compose --profile monitoring --profile logging up -d
docker compose --profile monitoring --profile logging ps
```

Trong Grafana Explore chọn Loki, khoảng thời gian 15 phút gần nhất. Gửi thêm một tin nhắn rồi chạy lần lượt:

```logql
{service="app"} |~ "chat_message_saved|direct_message_saved|chat_attachment_saved"
{service="nginx"} | json | route="/healthz" | status=200
{service="app"} | json | event="http_request_rejected" | status>=400
```

Không cần3ảnh. Chụp ảnh log gửi tin/upload và tùy chọn ảnh yêu cầu bị từ chối; cả3truyvấn đã kiểm tra có dữ liệu. Log gửi tin chứa ID, không chứa nội dung/mật khẩu. Mốc commit3 đã lưu; chờ chụpGĐ6 trước auditGĐ7. `bash scripts/check-phase6.sh` kiểm tra lại; `bash scripts/prepare-phase6-evidence.sh` tạo dữ liệu synthetic mới nếu log thử đã quá15phút.

## Giai đoạn 7 Hardening

```bash
docker compose exec app id
docker compose exec nginx id
docker compose port postgres 5432
curl -I http://localhost/login
git check-ignore .env
docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < scripts/verify-db-roles.sql
```

Cũng có thể dùng pgAdmin Query Tool:

```sql
SELECT rolname, rolsuper, rolcreatedb, rolcreaterole
FROM pg_roles
WHERE rolname IN ('chatuser', 'postgres_exporter');
```

Kết quả mong muốn: app/Nginx UID khác 0; PostgreSQL không có published port; security headers có mặt; `.env` bị bỏ qua; `chatuser` và exporter không có quyền superuser/create role/create DB.

Ảnh `07a-non-root-network.png` và `07b-database-roles.png`. cAdvisor dùng privileged và Promtail đọc Docker socket là ngoại lệ phải mô tả trong báo cáo. Socket mount read-only vẫn cấp quyền mạnh tới Docker API; không được coi đó là ranh giới bảo mật hoàn chỉnh. Bản demo dùng HTTP nên chưa có cookie Secure/TLS; đề cho phép HTTPS tự ký hoặc security headers cơ bản, mốc này chọn headers, không coi tương đương mã hóa HTTPS.

## Giai đoạn 8 README Demo Báo cáo

Báo cáo chỉ ghi kết quả đã có minh chứng. Chọn ảnh Giai đoạn1–7, sơ đồ kiến trúc, mô hình dữ liệu cập nhật theo `models.py`, cách triển khai, ba mốc commit, truy vấn metrics/log và giới hạn hardening. Tổng10–15trang; monitoring/logging đã chạy đạt, auditGĐ7 và bàn giaoGĐ8 chưa xong.

Kịch bản demo: khởi động Compose, đăng nhập hai user, tạo phòng/gửi tin, xem dữ liệu pgAdmin, Prometheus targets, Grafana dashboard, ba truy vấn LogQL và kiểm tra non-root.

Không chạy `docker compose down -v` trong quá trình thực hành khi cần giữ dữ liệu. Để tạo minh chứng khả năng lưu trữ, restart `app` rồi tải lại phòng chat và kiểm tra các tin nhắn vẫn còn.

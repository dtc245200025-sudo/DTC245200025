# Giai đoạn 4 Nginx và minh chứng báo cáo

## Địa chỉ sử dụng từ giai đoạn này

Trong Ubuntu VMware mở `http://localhost` (không thêm `:5000`). Từ máy Windows mở `http://192.168.203.131` khi VM còn IP này. Cổng80 đi qua Nginx; cổng app5000 đã bỏ published, PostgreSQL5432 vẫn nội bộ Docker. pgAdmin vẫn ở `http://localhost:5050` trong Ubuntu, không chuyển thành đường dẫn của LinhChat.

Tài khoản, phòng, bạn bè, tin nhắn và tệp cũ giữ nguyên. Cookie localhost có thể dùng tiếp; nếu cần đăng nhập lại, dùng tài khoản hiện có. Không tạo lại tài khoản chỉ để chuyển cổng.

## Chỉ cần một ảnh chính

Trong Terminal Ubuntu, phóng to cửa sổ rồi chạy:

```bash
cd ~/projects/de32-chat
clear
bash scripts/check-phase4.sh
```

Chụp từ tiêu đề `GIAI DOAN 4 - NGINX REVERSE PROXY` tới `GIAI_DOAN_4_OK`, gồm `nginx -t` thành công, `HTTP/1.1 200 OK`, security headers và trạng thái container/cổng. Nếu bị cuộn, giảm cỡ chữ Terminal một nấc. Không cần mở hoặc chụp `.env`. Tên ảnh `nginx-kiem-tra-gd4.png`, dùng số Hình tiếp theo sau khi đánh lại các số Hình 7 bị trùng.

Ảnh chat bổ sung là tùy chọn, không cần nếu báo cáo chật: hai phiên trình duyệt cùng dùng `http://localhost`, A/B vào cùng phòng/hội thoại có sẵn, gửi tin `Kiểm thử chat qua Nginx`. Chụp thanh địa chỉ không có `:5000`, tin hai chiều và dòng `Đã kết nối`. Không trộn URL :5000 cũ; không dùng hai tab thường cùng trình duyệt cho hai tài khoản vì cookie chung. Dùng cửa sổ thường + riêng tư hoặc hai trình duyệt độc lập.

## Chú thích và đoạn ngắn để viết báo cáo

**Hình X. Kiểm tra Nginx reverse proxy và các container LinhChat.**

Hệ thống được triển khai bằng Docker Compose trên Ubuntu VMware. Nginx làm reverse proxy tại cổng80, chuyển tiếp HTTP và WebSocket tới Flask-SocketIO; ứng dụng và PostgreSQL không mở cổng trực tiếp ra máy chủ. Nginx bổ sung security headers và giới hạn kích thước yêu cầu. Kiểm thử xác nhận chat realtime, thông báo và gửi tệp hoạt động qua proxy; dữ liệu vẫn được giữ sau khi tạo lại container ứng dụng.

## Cấu hình và nguồn tham khảo

`nginx/nginx.conf` dùng HTTP/1.1 và header Upgrade/Connection cho WebSocket, timeout3600s, Docker DNS động cho upstream khi app đổi IP, body11 MiB cho tệp10 MiB kèm multipart. Flask vẫn là nơi kiểm tra chính xác giới hạn từng file. Chặn `/metrics` và `/nginx_status` ở cổng web; status8081 chỉ trong mạng Docker cho exporter GĐ5. POST/login giới hạn10 lần/phút mỗi IP với burst5; GET form không bị tính là lần thử đăng nhập.

Nginx chạy UID/GID101, read-only với thư mục tạm tmpfs; healthcheck đi qua proxy tới `/healthz`. Image chính thức1.30.6-alpine được ghim digest đã tải thành công trên VM. Không có TLS ở mốc này; security headers không mã hóa HTTP, chỉ dùng cho lab/mạng tin cậy. Cấu hình sản xuất cần HTTPS/cookie Secure và đánh giá riêng.

Nguồn cấu hình: [Nginx WebSocket proxying](https://nginx.org/en/docs/http/websocket.html), [client_max_body_size](https://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size), [upstream resolve](https://nginx.org/en/docs/http/ngx_http_upstream_module.html#server), [Docker Official Nginx image](https://hub.docker.com/_/nginx).

## Nhật ký kiểm tra

- `GIAI_DOAN_4_OK`: syntax, headers,4container, đóng published5000/5432, chặn metrics/status, pgAdmin200.
- `NGINX4_LIVE_CHECK_OK`: PostgreSQL/HTTP/WebSocket thật qua proxy, nhóm/riêng hai chiều, quyền truy cập/thông báo/seen/nonce, HTTP polling fallback. File đúng10 MiB tải lại đúng SHA256,10 MiB+1 bị413; body trên11 MiB bị Nginx chặn413.
- `NGINX4_PERSISTENCE_OK`: sau force-recreate app, hai tệp10 MiB còn nguyên và người ngoài vẫn bị chặn; không restart Nginx.
- `NOTIFICATIONS_PERSISTENCE_OK`: unread còn qua recreate; `MESSAGES34B_PERSISTENCE_OK`: tin/emoji/receipt/file cũ còn và quyền giữ nguyên.
- Chưa triển khai monitoring/logging ở GĐ4. Chỉ chuyển GĐ5 sau khi người dùng xác nhận đã chụp.
- Bản cuối142/142test trên Ubuntu (61.84s), `NGINX4_RATE_LIMIT_OK`; trình duyệt qua IP VM cổng80 kết nối được và không lỗi console. Mốc1: `feat: milestone 1 - LinhChat, PostgreSQL and Nginx`, xem hash bằng `git log -1 --oneline`; chưa push GitHub.

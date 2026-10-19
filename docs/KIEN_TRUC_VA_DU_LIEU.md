# Kiến trúc và dữ liệu LinhChat

## Triển khai thực tế trong Ubuntu VMware

```text
Trình duyệt A/B -- HTTP + Socket.IO --> Nginx :80 --> Flask/Gunicorn :5000
                                                     |
                                              PostgreSQL :5432
                                                     ^
                                              pgAdmin localhost:5050

app / nginx-exporter / postgres-exporter / cAdvisor / Prometheus
                             | scrape 15s
                         Prometheus ----> Grafana localhost:3000

Log JSON app/Nginx --> Docker API --> Promtail --> Loki --> Grafana Explore
```

Đây là sơ đồ luồng, không phải tất cả kết nối đều được phép trên cùng mạng. `frontend`: app/Nginx; `backend` internal: app/PostgreSQL/pgAdmin/postgres-exporter; `management`: pgAdmin; `observability`: app/Nginx và các dịch vụ giám sát/logging. Nginx/Grafana không vào mạng database. Chỉ Nginx public80; pgAdmin5050, Grafana3000, Prometheus9090 chỉ bind localhost. Các exporter, cAdvisor, Loki và Promtail không publish port.

Một worker Gunicorn/100 threads và Flask-SocketIO/simple-websocket; presence/typing giữ trong bộ nhớ, chưa hỗ trợ nhiều instance. PostgreSQL lưu dữ liệu ứng dụng, avatar và tệp; volumes riêng cho PostgreSQL, pgAdmin, Prometheus, Grafana, Loki và positions Promtail.

## Mười bảng khớp models.py

| Bảng | Vai trò và quan hệ chính |
|---|---|
| `users` | Username/email, hash mật khẩu, auth_version, hồ sơ và avatar |
| `rooms` | Phòng Public/Private; created_by → users; hash mật khẩu/token mời, sức chứa |
| `room_members` | Quan hệ users ↔ rooms; duy nhất (room_id, user_id) |
| `room_join_requests` | Yêu cầu tham gia, user_id → users, room_id → rooms |
| `messages` | Tin nhóm; room_id → rooms, user_id → users; nonce chống gửi trùng |
| `friendships` | Cặp user_low_id/user_high_id → users, requester_id và trạng thái quan hệ |
| `direct_conversations` | Hội thoại riêng duy nhất cho mỗi cặp users |
| `direct_messages` | Tin riêng; conversation_id → direct_conversations, user_id → users |
| `message_receipts` | Người nhận → users; đúng một trong room_message_id/direct_message_id; delivered_at, seen_at |
| `chat_attachments` | Đúng một tin nhóm/riêng; filename, byte_size, SHA256, bytes gốc/preview |

Mỗi tin tối đa một tệp, giới hạn 10 MiB; receipt riêng mỗi người nhận. Không gán thời gian nhận/xem giả cho tin cũ. Migrations bổ sung schema, không thay thế database bằng dữ liệu mẫu. Ràng buộc, tên cột chi tiết lấy từ `app/chatapp/models.py`; sơ đồ này không chứa dữ liệu cá nhân.

## Luồng gửi tin và quan sát

1. HTTP xác thực bằng cookie ký, form POST kiểm tra CSRF. Socket.IO kiểm tra phiên và Origin.
2. Backend xác minh thành viên phòng/hai bên hội thoại, lưu tin/receipt vào PostgreSQL trước xác nhận gửi.
3. Sự kiện realtime đến đúng người; trình duyệt xác nhận nhận/xem theo điều kiện UI. Badge chưa đọc tính từ receipt; đóng popup không coi là đã xem.
4. Counter/gauge có nhãn giới hạn được scrape; log audit chỉ chứa các trường cho phép, không nội dung tin/secret. Grafana hiển thị metrics và truy vấn Loki.

## Giới hạn

HTTP chưa mã hóa/TLS, chưa Secure cookie. cAdvisor privileged, Promtail root/Docker socket và nhóm Docker là quyền mạnh; read-only socket mount không là ranh giới API an toàn. Promtail EOL, chỉ giữ theo stack bài lab. Role app sở hữu schema để migration; chưa E2EE, quét virus tệp, SMTP/2FA, HA, pentest hoặc kiểm thử restore/clean-install trên VM thứ hai.

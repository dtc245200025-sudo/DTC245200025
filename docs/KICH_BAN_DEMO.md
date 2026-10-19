# Kịch bản demo LinhChat (khoảng 5–7 phút)

## Chuẩn bị riêng trước khi trình bày

- Trong Ubuntu mở Terminal tại `~/projects/de32-chat`. Dùng deployment hiện có, không chạy lại bản phase2/phase3. Nếu máy mới bật: `docker compose --profile monitoring --profile logging up -d --wait`, đợi `bash scripts/check-phase8.sh` đạt.
- Mở Firefox thường cho A và cửa sổ riêng tư hoặc trình duyệt khác cho B. Hai cửa sổ riêng tư cùng Firefox có thể dùng chung phiên; không dùng chúng để giả định hai tài khoản độc lập.
- Website `http://localhost`; pgAdmin `http://localhost:5050`; Grafana `http://localhost:3000`; Prometheus `http://localhost:9090`. Trong Windows, website dùng IP VM, quản trị dùng SSH tunnel như README, không mở public các cổng quản trị.
- Dùng hai tài khoản demo đã có hoặc tự đăng ký tài khoản thử. Đăng nhập riêng trước khi quay/chụp. Thông tin demo/Grafana nằm trong `work/` trên VM, không đưa vào báo cáo. Không đăng xuất khi đang cần nhiều phiên của cùng tài khoản.
- Giữ sẵn một ảnh nhỏ và một tệp thử <10 MiB. Không dùng dữ liệu/mật khẩu quan trọng vì lab đang HTTP.

## Trình tự trình bày

| Thời gian | Thao tác | Kết quả cần thấy |
|---|---|---|
| 0:00–0:45 | Terminal `bash scripts/check-phase8.sh`, giới thiệu kiến trúc | Stack chạy, metrics/log, schema và 3 mốc Git; phần GitHub còn chờ nếu chưa push |
| 0:45–2:00 | A tạo Public giới hạn người; B tìm/tham gia; gửi hai chiều | Nhận realtime, đang nhập, bấm tin xem các mốc thời gian; tải lại vẫn có lịch sử |
| 2:00–3:00 | A/B đã là bạn bè: mở Nhắn tin, gửi emoji/ảnh/tệp; B về Trang chủ khi A gửi tiếp | Chat riêng, preview/tải tệp; toast/badge ở B, bấm Xem mở đúng hội thoại |
| 3:00–3:45 | Mở phòng Private có sẵn bằng tài khoản không có quyền | Bị yêu cầu đúng phương thức truy cập; không công khai link/token/mật khẩu khi trình bày |
| 3:45–4:30 | pgAdmin Query Tool chạy SELECT JOIN trong hướng dẫn GĐ3 | Tin vừa gửi gắn đúng phòng/người gửi; không SELECT toàn bảng users/hash/password |
| 4:30–5:30 | Prometheus Targets; Grafana LinhChat Overview | 5/5 target UP, 11 panel; số liệu HTTP/chat tăng sau thao tác |
| 5:30–6:30 | Grafana Explore → Loki → Code, Last 15 minutes | Log mới bằng query bên dưới, không hiện nội dung tin/secret |
| 6:30–7:00 | Tổng kết hardening và giới hạn | Non-root/ro/quyền/mạng/header; nêu chưa TLS, ngoại lệ cAdvisor/Promtail |

```logql
{service="app"} |~ "chat_message_saved|direct_message_saved|chat_attachment_saved"
```

Hai query khác và cách chọn Code có ở `docs/GD6_LOGGING_VA_BAO_CAO.md`. Nếu log cũ quá 15 phút, gửi tin mới trong demo hoặc tăng khoảng thời gian; không nói dữ liệu lịch sử là hoạt động vừa diễn ra.

## Khi gặp lỗi

- Web không mở: kiểm tra VM bật, IP bằng `hostname -I`, `docker compose --profile monitoring --profile logging ps`; trong Ubuntu dùng localhost:80, không :5000.
- Đăng nhập gặp429: đợi ít nhất7giây trước lần thử tiếp, tránh gửi dồn; không tắt rate limit.
- Chỉ có một tài khoản ở hai cửa sổ: dùng Firefox thường + riêng tư, hoặc hai trình duyệt khác nhau.
- Grafana không có dữ liệu: kiểm tra time range/datasource và chạy script bàn giao; không tạo ảnh hoặc số liệu giả.
- Không dùng `down -v`/xóa volume để sửa lỗi. Muốn backup: `bash scripts/backup-before-upgrade.sh`; file dump trong work/backups là dữ liệu riêng, giữ ngoài Git. Script backup hiện lưu DB và source ứng dụng, không sao lưu toàn bộ TSDB/Loki/Grafana; chưa kiểm thử khôi phục trên VM khác.

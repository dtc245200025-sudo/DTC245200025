# Giai đoạn6 — Logging Loki/Promtail

## Kết quả đã kiểm tra trên Ubuntu VMware

- Loki3.6.18 và Promtail3.6.7 được ghim digest; tổng11service chạy. Loki/Promtail không publish cổng host, Grafana vẫn localhost3000. Promtail chỉ đọc log app/Nginx thuộc projectde32-chat, bỏ one-off; không thu log DB/pgAdmin hoặc project khác.
- App log JSON theo allowlist: tin nhóm, tin riêng, upload và yêu cầu HTTP bị từ chối. Không ghi nội dung tin, tên file, email, mật khẩu, token hoặc exception tùy ý. Nginx chỉ ghi họ route cố định, status/bytes/duration; bỏ IP, UA, query và body. Gunicorn access cũng không chứaURL/query. Log Docker app/Nginx xoay10MB×3file mỗi container.
- 146/146test đạt trên VM; gửi tin nhóm/riêng, upload và receipt bằng WebSocket/HTTP thật; kiểm tra3query qua Loki/Grafana có dữ liệu. Canary đặt trong nội dung/tên file/path/query/UA và các secret.env không xuất hiện trong log được kiểm tra. Đây là kiểm tra phạm vi mẫu, không chứng minh chống mọi kiểu lộ dữ liệu.
- LOGGING_PERSISTENCE_OK: mẫu audit cũ còn và kết quả truy vấn không lặp sau recreate riêng Loki/Promtail. Positions nằm trong volume riêng. MESSAGES34B_PERSISTENCE_OK: lịch sử/tệp/receipt cũ và quyền vẫn đúng. Monitoring5/5target UP, dashboard11panel, CPU/RAM hiện đủ11service.
- Mốc3: `feat: milestone 3 - Loki and Promtail centralized logging`. Xem `git log -3 --oneline`; chưa push GitHub. GĐ7audit và GĐ8báo cáo cuối chưa hoàn thành.

## Chuẩn bị log mới trước khi chụp

Nếu log thử đã quá15phút, trong Terminal Ubuntu chạy:

```bash
cd ~/projects/de32-chat
bash scripts/prepare-phase6-evidence.sh
```

Script dùng tài khoản synthetic A/B/C đã có, gửi tin/tệp mẫu và thử quyền; không in tài khoản/mật khẩu. Có thêm dữ liệu thử, không xóa dữ liệu cũ. Khi kết thúc thấy GIAI_DOAN_6_OK mới quay lại trình duyệt. Không cần chụp Terminal này.

## Chụp tối đa hai ảnh

1. Trong Firefox Ubuntu mở `http://localhost:3000/explore`. Nếu cần đăng nhập, xem riêng `less work/grafana-access.txt`, nhấnq để đóng; không chụp mật khẩu. Dùng tài khoản Grafana cũ, không phải tài khoản LinhChat/Ubuntu.
2. Ở ô datasource trên cùng bên trái, đổi Prometheus thành **Loki**. Bấm **Code**, chọn **Last15minutes** (hoặc Last1hour nếu đang xem log cũ).
3. Bấm vào ô code, Ctrl+A rồi dán truy vấn; sau khi hiện đúng nội dung mới bấm **Run query** hoặc Shift+Enter. Nếu lần đầu chưa chạy, bấm Run query sau khi editor đã nhận đủ nội dung.

### Ảnh chính — sự kiện tin nhắn và upload

```logql
{service="app"} |~ "chat_message_saved|direct_message_saved|chat_attachment_saved" | json | line_format "{{.event}} message_id={{.message_id}} scope={{.scope}}"
```

Bấm tiêu đề **Logs volume** để thu gọn biểu đồ nếu che dòng log; thu **Outline** và sidebar nếu cần. Chụp có thanh địa chỉ, datasourceLoki, code truy vấn và các dòng chat_message_saved/direct_message_saved/chat_attachment_saved cùng timestamp. line_format chỉ làm gọn cách hiển thị, không tạo log giả.

**Hình X. Grafana Explore truy vấn log tin nhóm, tin riêng và upload từ Loki.**

### Truy vấn web — cần chạy, không bắt buộc thêm ảnh

```logql
{service="nginx"} | json | route="/healthz" | status=200
```

Kết quả phải có log http_access, route/healthz và status200. Giữ truy vấn này trong phần mô tả/demo để đủ3LogQL; tránh thêm ảnh lặp cho báo cáo10–15trang.

### Ảnh thứ hai — yêu cầu bị từ chối (tùy chọn nếu báo cáo chật)

```logql
{service="app"} | json | event="http_request_rejected" | status>=400 | line_format "{{.event}} endpoint={{.endpoint}} status={{.status}}"
```

Thay nội dung ô code bằng Ctrl+A; Run query. Chụp có truy vấn và các dòng cảnh báo404 từ kiểm tra quyền/lịch sử hoặc URL không tồn tại. Đây là yêu cầu bị từ chối có chủ đích để kiểm thử, **không phải ứng dụng bị crash**.

**Hình X+1. Truy vấn log cảnh báo các yêu cầu HTTP bị từ chối.**

Nếu cần kiểm tra lại mọi thành phần: `bash scripts/check-phase6.sh`. Giữ dịch vụ chạy, xác nhận đã chụp GĐ6 trước khi chuyển GĐ7.

## Đoạn ngắn cho báo cáo

Hệ thống sử dụng Promtail thu thập log JSON từ Flask và Nginx, gắn nhãn dịch vụ rồi chuyển tới Loki. Datasource Loki được cấu hình tự động trong Grafana; các truy vấn LogQL lọc sự kiện gửi tin/upload, truy cập web và yêu cầu bị từ chối. Log và vị trí đọc được lưu bằng volume Docker, đã kiểm tra còn sau khi tạo lại dịch vụ; nội dung tin nhắn và thông tin đăng nhập được loại khỏi log.

## Giới hạn cần ghi đúng

- Promtail đãEOL02/03/2026; giữ cho bài lab theo stack đã chốt. Với hệ thống thực tế nên chuyển GrafanaAlloy. [Nguồn Grafana](https://grafana.com/docs/loki/latest/send-data/promtail/).
- Loki single-instance/filesystem, không HA. Retention7ngày bằng Compactor là cấu hình, chưa chờ7ngày để thử xóa tự động; không tự giới hạn tổng dung lượng theo diskfree. WAL/volume lưu dữ liệu. Promtail128m/Loki512m là giới hạn RAM.
- Drop log cũ hơn1h khi Promtail replay để tránh cold-backfill/out-of-order của lab; không phải giải pháp lưu trữ đủ lịch sử hoặc chống mất log khi agent ngừng lâu. Chỉ lưu curatedaudit app/Nginx, không toàn bộ stacktrace/DB/systemlog. Kết quả không lặp khi query snapshot không tương đương cam kết exactly-once mọi tình huống.
- Promtail chạyroot để đọc Docker socket; mountro vẫn có quyềnDockerAPI mạnh, không phải ranh giới bảo mật hoàn chỉnh. Không sửa daemon hay mở socket quaTCP. Loki auth_enabledfalse chỉ trong mạng Compose; không publish3100/9080.
- Loki có thể tự thêm metadata service_name/detected_level; nhãn chính service/event/level, không dùng username/email/messageID làm streamlabel. IDs phòng/tin chỉ ở nội dung audit.

Nguồn: [Loki retention](https://grafana.com/docs/loki/latest/operations/storage/retention/), [LogQL](https://grafana.com/docs/loki/latest/query/log_queries/), [Loki3.6.18](https://github.com/grafana/loki/releases/tag/v3.6.18).

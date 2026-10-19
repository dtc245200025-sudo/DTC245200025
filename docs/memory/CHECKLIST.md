# Checklist dự án LinhChat

`[x]` đã thực hiện và có bằng chứng, `[ ]` chưa hoàn thành/đang làm. Không dùng trạng thái này thay kiểm tra runtime sau mỗi thay đổi.

## Quản lý và yêu cầu

- [x] Chốt stack và mục tiêu Ubuntu VMware.
- [x] Ghép yêu cầu giao diện/chức năng vào lộ trình gốc.
- [x] Tạo trí nhớ yêu cầu/mục tiêu/tiến trình/checklist và quy ước AGENTS.md.
- [x] Giữ `.env`, SSH, backup, tài khoản minh chứng ngoài Git.
- [x] Cập nhật trí nhớ GĐ4; tiếp tục cập nhật sau từng phần tiếp theo.

## GĐ1–3

- [x] Môi trường/Git/Docker/Compose, người dùng đã chụp GĐ1.
- [x] Flask/source/LinhChat hồng phấn, người dùng đã chụp GĐ2.
- [x] PostgreSQL/pgAdmin/chat nhóm realtime và lịch sử còn sau restart.
- [x] Email bắt buộc, login username/email, bổ sung email tài khoản cũ.
- [x] Trang chủ hai lựa chọn, account dock, theme sáng/tối.
- [x] Profile của mình/người khác, avatar, bio150, username cố định, public/private.
- [x] Menu avatar đóng ngoài/Escape, tab Bảo mật, password hash/thu hồi phiên.
- [x] Public có sức chứa, Private link/phê duyệt/mật khẩu; quyền HTTP/Socket/file.
- [x] Bạn bè/tìm tên/email/lời mời/hủy/online-offline.
- [x] Chat riêng/tải lịch sử/reconnect/nonce chống gửi trùng.
- [x] Đang nhập nhóm/riêng, không truyền nội dung bản nháp.
- [x] Receipt gửi/nhận/xem + thời gian, không bịa lịch sử cũ.
- [x] Tìm tin/tệp, emoji/gợi ý, ảnh/file10 MiB, quyền tải xuống.
- [x] Thông báo nổi và badge chưa đọc nhóm/riêng, người dùng xác nhận hoạt động.
- [x] 140/140 test trên VM, notifications live với PostgreSQL/WebSocket thật.

## GĐ4 — đã chạy đạt và người dùng đã chụp

- [x] Sao lưu trước chuyển proxy.
- [x] Nginx config hợp lệ, non-root/read-only/healthcheck.
- [x] Proxy HTTP/Socket.IO WebSocket và polling hoạt động.
- [x] Upload10 MiB qua proxy được, vượt giới hạn bị chặn.
- [x] Chuyển URL sang cổng80, app5000 và DB5432 không published.
- [x] Đường metrics/status không mở ra cổng web; pgAdmin vẫn localhost5050.
- [x] Chat nhóm/riêng/thông báo/ảnh/file và UI qua Nginx đạt.
- [x] Tin/file/receipts/unread cũ còn sau recreate app.
- [x] 142/142 kiểm thử hồi quy trên VM; Nginx rate limit/runtime đạt.
- [x] Hướng dẫn một ảnh chính, một ảnh tùy chọn và đoạn báo cáo ngắn.
- [x] Commit mốc1 với nội dung đã chạy đạt, không bí mật.
- [x] Người dùng xác nhận đã chụp GĐ4 ngày18/10/2026.

## GĐ5 — đã chạy đạt và người dùng đã chụp

- [x] Sao lưu trước triển khai, ghim phiên bản/digest image chính thức; không thay DB/app nền.
- [x] Prometheus5/5target UP, PostgreSQL/Nginx exporter hoạt động; role exporter pg_monitor không superuser.
- [x] cAdvisor thu CPU/RAM9service; lọc one-off và instance cũ sau recreate, không nhãn người dùng.
- [x] Grafana provisioning datasource/dashboard LinhChat Overview,11/11panel có dữ liệu; refresh15s được xác minh UI.
- [x] Hai client WebSocket gửi6tin gồm2tệp, số liệu HTTP/chat/upload/socket tăng thực tế.
- [x] 143/143 kiểm thử trên VM; kiểm tra persistence metrics/dashboard và dữ liệu app cũ đạt.
- [x] Giới hạn RAM/TSDB, healthcheck; cổng quản trị localhost, exporter không published.
- [x] Kiểm tra trình duyệt thật, hướng dẫn tối đa2ảnh và đoạn báo cáo ngắn.
- [x] Commit mốc2 với thành phần đã chạy đạt, không secret; chưa push.
- [x] Người dùng xác nhận đã chụp GĐ5 ngày19/10/2026; cho phép tiếp tục GĐ6.

## GĐ6 — đã chạy đạt và người dùng đã chụp

- [x] Backup trước triển khai; image Loki/Promtail chính thức ghimdigest, không thay DB.
- [x] AppJSON allowlist; Nginxroutecốđịnh, GunicornkhôngURL/query; xoaylogDocker10MB×3.
- [x] Promtail chỉ project/app/nginx, bỏone-off/non-audit; Loki+positionsvolume.
- [x] Log thật từ chat nhóm/riêng/upload/HTTP,3LogQL qua Loki và GrafanaAPI có dữ liệu.
- [x] Canary nội dung/tên file/query/path/UA và secret.env không xuất hiện trong mẫu log.
- [x] 146/146test; dữ liệu/tệp/receipt/quyền cũ còn sau cập nhậtapp.
- [x] Recreate Loki/Promtail: log snapshot còn, không lặp kết quả; positions còn.
- [x] Monitoring5/5UP,11panel,CPU/RAM11service sau thêmlogging.
- [x] Xác minh giao diện Explore và hướng dẫn một ảnh chính/một ảnh tùy chọn.
- [x] Commit mốc3 có thành phần chạy đạt, không secret; chưa push.
- [x] Người dùng gửi ảnhGĐ6 hợp lệ và yêu cầu tiếp tụcGĐ7 ngày19/10/2026.

## GĐ7 — đã chạy đạt, chờ người dùng chụp

- [x] App/Nginx non-root/rootfsro/capdropALL/NoNewPrivs/seccomp; sourcehashkhớpcontainer.
- [x] Cổngadminlocalhost, app/DB/collector khôngpublish; backendinternal, proxy/Grafana khôngvàomạngDB.
- [x] RoleDBhạnchế, exporterpg_monitor/khôngghi messages; kiểmtrahash khôngin dữliệu.
- [x] .env600/work700,secretkhôngmặcđịnh/trùng; quétGit vàlịchsửkhôngsecret/privatepath.
- [x] CSRF/cookietamper/Origin/quyềnHTTP-file vàheaderđạt; ratelimit429/GET200.
- [x] Backupvàsửalogoutthu hồimọiphiêncùngtài khoản; userkhác khôngbịảnhhưởng.
- [x] Chuẩnhóasecurityheaderproxykhôngtrùng; Nginxnhậnđúngmountsource.
- [x] 152/152unit; HARDENING_LIVE_OK/INFRA_OK vàpersistence/monitoring/loggingđạt.
- [x] MộtảnhTerminal, đoạn báo cáo ngắn vàgiớihạnHTTP/DockerAPI đượcghi rõ.
- [x] Giữ3commitmốcbanđầu, commitsửaGĐ7riêng; khôngpush.
- [ ] Người dùng xác nhận đã chụpGĐ7; chờ trướcGĐ8.

## GĐ8

- [ ] GĐ8 README/source/demo cuối, mô hình dữ liệu cập nhật, lịch sử3commit và báo cáo10–15trang.
- [ ] Đánh lại số hình trùng khi người dùng hoàn thiện báo cáo; chưa tự sửa Demo.docx.
- [ ] Chốt repository GitHub theo mã sinh viên và push03mốc trước nộp; hiện chưa có remote, không tự tạo/push.

## Không tự mở rộng

- [ ] Chưa triển khai SMTP/2FA/PWA/push OS/âm thanh, Bận/Vắng mặt, nhiều instance. Các mục này không chặn hoàn thành phạm vi đã chốt.

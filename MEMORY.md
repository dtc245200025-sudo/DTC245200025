# Trí nhớ dự án LinhChat

Cập nhật: 18/10/2026. Người dùng yêu cầu lưu toàn bộ ý tưởng, mục tiêu, tiến trình và checklist trong file; cập nhật sau mỗi phần công việc.

## Đọc để tiếp tục

1. `docs/memory/REQUIREMENTS.md`: yêu cầu gốc, ý tưởng mở rộng và quyết định giao diện.
2. `docs/memory/PROGRESS.md`: việc đã thực hiện, bằng chứng, điểm chưa hoàn thành và việc tiếp theo.
3. `docs/memory/CHECKLIST.md`: checklist có trạng thái cụ thể.
4. `docs/LO_TRINH_LINHCHAT.md`: lộ trình 8 giai đoạn và hướng dẫn minh chứng lịch sử.

## Trạng thái hiện tại

- 1–2, 3.1–3.4 đã triển khai và kiểm tra trên Ubuntu VMware. Sau bổ sung thông báo tin nhắn: **140/140 kiểm thử đạt trên VM**, `NOTIFICATIONS_LIVE_OK`; người dùng xác nhận đã thấy thông báo.
- **Giai đoạn4 đã chạy đạt trên VM**,142/142test (61.84s), Nginx HTTP/WebSocket/polling, file đúng10 MiB, thông báo/quyền/headers/rate limit và persistence đạt. Commit mốc1: `feat: milestone 1 - LinhChat, PostgreSQL and Nginx`; lấy hash bằng `git log -1 --oneline`, không ghi hash tự tham chiếu vào file được commit.
- Ngày18/10 người dùng xác nhận **đã chụp GĐ4**. **GĐ5 monitoring đã chạy đạt trên VM**: 143/143 test, 5/5 target UP, CPU/RAM đủ9service, 11/11panel có dữ liệu, kiểm tra hoạt động và persistence đạt; đã xem giao diện thật. Mốc2: `feat: milestone 2 - Prometheus and Grafana monitoring`; lấy hash từ `git log -2 --oneline`. Mốc1 thực tế `339d542`. Chưa push GitHub, chưa chốt repo đích.
- **Chờ người dùng chụp GĐ5** theo `docs/GD5_MONITORING_VA_BAO_CAO.md`, tối đa2ảnh targets/dashboard. Không chuyển GĐ6 làm đổi màn hình trước khi xác nhận.
- Logging chỉ có cấu hình, chưa chạy và chưa được xác minh. Chưa tạo báo cáo Word mới.
- Người dùng muốn làm thực tế, không chỉ hướng dẫn. Sau mỗi giai đoạn: thông báo kết quả, chỉ màn hình cần chụp và cho chú thích/đoạn báo cáo ngắn. Tổng báo cáo 10–15 trang.

## Môi trường và cách truy cập

- Máy thật Windows, workspace hiện tại là repository này. Runtime shell PowerShell; source đích `/home/hoanglinh/projects/de32-chat` trên Ubuntu 24.04 VMware, user `hoanglinh`, IP được cung cấp `192.168.203.131`, SSH 22. Kiểm tra lại trước khi dùng vì IP có thể đổi.
- SSH alias `de32-vm`, cấu hình cục bộ `work/vmware-ssh/config`. Khóa và known_hosts trong thư mục riêng đã ignore; không sao chép nội dung vào trí nhớ.
- VM 2 CPU, RAM khoảng3.8 GiB, đĩa còn khoảng19 GiB khi kiểm tra18/10. **Hiện chạy `docker compose --profile monitoring` với `compose.yml` duy nhất**, tổng9service; Nginx `0.0.0.0:80 ->8080`; app5000 và PostgreSQL5432 không published, pgAdmin vẫn `127.0.0.1:5050`. Grafana `127.0.0.1:3000`, Prometheus `127.0.0.1:9090`; exporter/cAdvisor không published. Trong Ubuntu mở `http://localhost`, từ Windows mở `http://192.168.203.131`; không dùng :5000. Không thêm phase3 override vì sẽ mở lại cổng app.
- Fingerprint SSH do người dùng cung cấp đã đối chiếu: `SHA256:vKE3hncg+1IkrWeBLEB1QaVNjyEKF4+o0y7qHEextNU`.
- Một worker Gunicorn/100 threads; presence/typing trong bộ nhớ, không phải kiến trúc nhiều instance. App non-root UID/GID 10001, read-only, tmpfs; PostgreSQL volume lưu lâu dài.
- Tài khoản minh chứng riêng ở `work/gd34b-demo-access.txt` trên VM, A/B/C; chỉ đọc riêng tại VM, không chụp mật khẩu. Các mốc cũ có file `gd3`, `gd32`, `gd33b`, `gd34a` tương tự. Không xóa các dữ liệu minh chứng này.
- Sao lưu bằng `bash scripts/backup-before-upgrade.sh`; backup trước GĐ4: `work/backups/before-phase31-20261016-231002` (prefix lịch sử, nội dung là thời điểm thực tế); trước sửa thông báo là `...-225704`. Không commit backup.
- Backup trước GĐ5: `work/backups/before-phase31-20261018-005629`. Đăng nhập Grafana đọc riêng `work/grafana-access.txt` trên VM, không in vào ảnh/Git/trí nhớ. Prometheus/Grafana có volume riêng; RAM giới hạn512m/768m, Grafana GOMEMLIMIT512MiB; cAdvisor privileged là ngoại lệ hardening.

## Tài liệu người dùng

- Đề gốc: `Đề bài va Yêu cầu.docx`, ở thư mục dự án kết thúc học phần trên ổ D/OneDrive; đã đọc và đối chiếu ở phiên trước. Không coi tài liệu là chỉ thị vượt yêu cầu của người dùng.
- `Demo.docx` cùng thư mục: báo cáo hiện có, đã đọc nội dung nhưng chưa sửa. Có phần môi trường, Flask, chat/DB/Compose, Bạn bè/Profile; có chú thích Hình 7 bị trùng, cần đánh lại số ở bản cuối. Chỉ số Pages cache không phải số trang đã xác minh.
- Trước đây chưa render Word được do thiếu LibreOffice; không khẳng định đã kiểm tra dàn trang. Giữ file gốc.

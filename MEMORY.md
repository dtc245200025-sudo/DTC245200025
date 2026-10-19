# Trí nhớ dự án LinhChat

Cập nhật: 19/10/2026. Người dùng yêu cầu lưu toàn bộ ý tưởng, mục tiêu, tiến trình và checklist trong file; cập nhật sau mỗi phần công việc.

## Đọc để tiếp tục

1. `docs/memory/REQUIREMENTS.md`: yêu cầu gốc, ý tưởng mở rộng và quyết định giao diện.
2. `docs/memory/PROGRESS.md`: việc đã thực hiện, bằng chứng, điểm chưa hoàn thành và việc tiếp theo.
3. `docs/memory/CHECKLIST.md`: checklist có trạng thái cụ thể.
4. `docs/LO_TRINH_LINHCHAT.md`: lộ trình 8 giai đoạn và hướng dẫn minh chứng lịch sử.

## Trạng thái hiện tại

- 1–2, 3.1–3.4 đã triển khai và kiểm tra trên Ubuntu VMware. Sau bổ sung thông báo tin nhắn: **140/140 kiểm thử đạt trên VM**, `NOTIFICATIONS_LIVE_OK`; người dùng xác nhận đã thấy thông báo.
- **Giai đoạn4 đã chạy đạt trên VM**,142/142test (61.84s), Nginx HTTP/WebSocket/polling, file đúng10 MiB, thông báo/quyền/headers/rate limit và persistence đạt. Commit mốc1: `feat: milestone 1 - LinhChat, PostgreSQL and Nginx`; lấy hash bằng `git log -1 --oneline`, không ghi hash tự tham chiếu vào file được commit.
- Ngày18/10 người dùng xác nhận **đã chụp GĐ4**. **GĐ5 monitoring đã chạy đạt trên VM**: 143/143 test, 5/5 target UP, CPU/RAM đủ9service, 11/11panel có dữ liệu, kiểm tra hoạt động và persistence đạt; đã xem giao diện thật. Mốc2: `feat: milestone 2 - Prometheus and Grafana monitoring`; lấy hash từ `git log -2 --oneline`. Mốc1 thực tế `339d542`. Chưa push GitHub, chưa chốt repo đích.
- Người dùng xác nhận **đã chụp GĐ5 ngày19/10**. **GĐ6 đã chạy đạt**:146/146test,3LogQL có log thật qua Grafana, canary/secret không xuất hiện trong mẫu log, LOGGING_PERSISTENCE_OK và dữ liệu app cũ còn. Mốc3 `feat: milestone 3 - Loki and Promtail centralized logging`; lấy hash từ Git. Chưa push.
- Người dùng đã gửiảnhGĐ6hợp lệ vàyêucầutiếpGĐ7 ngày19/10. **GĐ7chạyđạt**:152/152test, HARDENING_INFRA_OK/HARDENING_LIVE_OK, ratelimit/persistence/monitoring/loggingđạt. Sửa logout thu hồi mọiHTTP/cookie/socket của chính tài khoản vàchuẩnhóaheaderproxy. Ba mốccommitcũ giữnguyên, fixGĐ7 lưu riêng, khôngrewrite/chưapush.
- Người dùng đã chụp GĐ7, gửi ảnh hợp lệ và xác nhận **đến Hình12, ảnh tiếp theo Hình13** ngày19/10. **GĐ8 phần cục bộ đã kiểm tra đạt**: kiến trúc/10bảng, demo5–7phút, README, guideHình13 vàscriptbàngiao; chạy lại152testtrong63.25s với container khôngnetwork/.env/DBvolume. `bash scripts/check-phase8.sh` xácnhậnruntime/schema/hardening/5UP/11panel/3LogQL/3mốc. Chờ người dùng chụpHình13; GitHub/MSSV vàWordcuối10–15trang chưa chốt, khônggọiđã nộp/chưapush. Tài liệuGĐ8lưucommitriêng, khôngđổiba mốc. HTTPkhôngTLS vàngoạilệcAdvisor/Promtail giữrõ.
- Người dùng muốn làm thực tế, không chỉ hướng dẫn. Sau mỗi giai đoạn: thông báo kết quả, chỉ màn hình cần chụp và cho chú thích/đoạn báo cáo ngắn. Tổng báo cáo 10–15 trang.

### Bàn giao mới nhất sau Hình13

Người dùng đã xác nhận **đã chụp Hình13** và yêu cầu **tự push GitHub**. Không tạo repository/remote/PR hoặc push thay người dùng. GĐ8 phần cục bộ và minh chứng đã xong; GitHub do người dùng thực hiện, chưa xác minh đã push/nộp bài. Báo cáo Word cuối chưa sửa/kiểm tra dàn trang. Kiểm tra VM thấy người dùng đang sửa `scripts/check-phase8.sh` và `tests/verify_delivery.py`; giữ nguyên, không chép đè hoặc tự commit các chỉnh sửa này. Lần xác nhận này chỉ cập nhật file trí nhớ, không chạy lại test hoặc tạo commit mới.

## Môi trường và cách truy cập

- Máy thật Windows, workspace hiện tại là repository này. Runtime shell PowerShell; source đích `/home/hoanglinh/projects/de32-chat` trên Ubuntu 24.04 VMware, user `hoanglinh`, IP được cung cấp `192.168.203.131`, SSH 22. Kiểm tra lại trước khi dùng vì IP có thể đổi.
- SSH alias `de32-vm`, cấu hình cục bộ `work/vmware-ssh/config`. Khóa và known_hosts trong thư mục riêng đã ignore; không sao chép nội dung vào trí nhớ.
- VM 2CPU/RAM3.8GiB, disk còn16GiB trướcGĐ6. **Hiện chạy `docker compose --profile monitoring --profile logging` với compose.yml duy nhất**, tổng11service; Nginx public80, app5000/DB5432 không published; pgAdminlocalhost5050, Grafanalocalhost3000, Prometheuslocalhost9090. Loki3100/Promtail9080/exporter/cAdvisor không published. Website trong Ubuntu `http://localhost`, Windows dùng IPVM; không phase3 override.
- Fingerprint SSH do người dùng cung cấp đã đối chiếu: `SHA256:vKE3hncg+1IkrWeBLEB1QaVNjyEKF4+o0y7qHEextNU`.
- Một worker Gunicorn/100 threads; presence/typing trong bộ nhớ, không phải kiến trúc nhiều instance. App non-root UID/GID 10001, read-only, tmpfs; PostgreSQL volume lưu lâu dài.
- Tài khoản minh chứng riêng ở `work/gd34b-demo-access.txt` trên VM, A/B/C; chỉ đọc riêng tại VM, không chụp mật khẩu. Các mốc cũ có file `gd3`, `gd32`, `gd33b`, `gd34a` tương tự. Không xóa các dữ liệu minh chứng này.
- Sao lưu bằng `bash scripts/backup-before-upgrade.sh`; backup trước GĐ4: `work/backups/before-phase31-20261016-231002` (prefix lịch sử, nội dung là thời điểm thực tế); trước sửa thông báo là `...-225704`. Không commit backup.
- Backup trước GĐ5: `work/backups/before-phase31-20261018-005629`. Đăng nhập Grafana đọc riêng `work/grafana-access.txt` trên VM, không in vào ảnh/Git/trí nhớ. Prometheus/Grafana có volume riêng; RAM giới hạn512m/768m, Grafana GOMEMLIMIT512MiB; cAdvisor privileged là ngoại lệ hardening.
- Backup trướcGĐ6 `work/backups/before-phase31-20261019-142649`. Loki3.6.18/Promtail3.6.7 ghimdigest; volumesloki_data/promtail_positions. PromtailEOL; chỉ đọc DockerAPI cho curatedaudit app/Nginx, bỏone-off/logreplay>1h. Socketro vẫn quyền mạnh; không coi productionhardening hoàn tất. Mẫu thử trong work, không commit. Nếu cần log mới để chụp, `bash scripts/prepare-phase6-evidence.sh` tạo thêm dữ liệu synthetic, không xóa cũ.
- BackuptrướcGĐ7 `work/backups/before-phase31-20261019-150109` vàbảnNginxcũ `work/backups/before-phase7-header-nginx.conf` trênVM. LiveauditdùngsyntheticA/B/C, đãlogoutmọiphiêncủaAđểthử; khôngđổimật khẩu. `work/hardening-live.json` chỉboolean/timestamp/imageID, khôngcookie/secret; checkGĐ7 đọcảnhhạtầngtrựctiếpvàđốichiếuimagevớiliveevidenceđãlưu.

## Tài liệu người dùng

- Đề gốc: `Đề bài va Yêu cầu.docx`, ở thư mục dự án kết thúc học phần trên ổ D/OneDrive; đã đọc và đối chiếu ở phiên trước. Không coi tài liệu là chỉ thị vượt yêu cầu của người dùng.
- `Demo.docx` cùng thư mục: báo cáo hiện có, đã đọc nội dung nhưng chưa sửa. Có phần môi trường, Flask, chat/DB/Compose, Bạn bè/Profile; có chú thích Hình 7 bị trùng, cần đánh lại số ở bản cuối. Chỉ số Pages cache không phải số trang đã xác minh.
- Trước đây chưa render Word được do thiếu LibreOffice; không khẳng định đã kiểm tra dàn trang. Giữ file gốc.

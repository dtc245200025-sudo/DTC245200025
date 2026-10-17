# Giai đoạn 5 Prometheus và Grafana

## Đã triển khai và kiểm tra

Trên Ubuntu VMware: Prometheus thu thập 5 target UP (`chat-app`, `postgres`, `nginx`, `cadvisor`, `prometheus`). Grafana có dashboard **LinhChat Overview** trong folder **LinhChat**, 11 panel dùng dữ liệu thật: trạng thái, HTTP, tin nhóm/riêng, Socket.IO, CPU/RAM 9 service, kết nối PostgreSQL, lưu lượng Nginx và độ trễ HTTP P95. Không có Loki datasource chưa chạy ở giai đoạn này.

143/143 kiểm thử trong container đạt. `MONITORING_ACTIVITY_OK` xác nhận gửi thật 6 tin (gồm 2 tệp), WebSocket/receipt và HTTP làm các counter tăng trong Prometheus. `MONITORING_PERSISTENCE_OK` xác nhận mẫu lịch sử TSDB cùng dashboard/datasource còn sau force-recreate riêng Prometheus/Grafana. `MESSAGES34B_PERSISTENCE_OK` xác nhận dữ liệu LinhChat cũ và quyền truy cập vẫn giữ nguyên. Không xóa volume hoặc sửa báo cáo Word.

## Chụp hai ảnh trong Ubuntu

### Ảnh thứ nhất Prometheus targets

1. Mở Firefox trong Ubuntu, nhập `http://localhost:9090/targets`. Không mở trang chủ LinhChat rồi tìm Prometheus bên trong; đây là cổng riêng.
2. Đợi thấy đủ 5 nhóm `cadvisor`, `chat-app`, `nginx`, `postgres`, `prometheus`, đều `UP` hoặc `1 / 1 up`.
3. Phóng to cửa sổ. Nếu không đủ màn hình, thu nhỏ trang một nấc bằng Ctrl+-; hoặc bấm **Collapse all pools** để hiện gọn năm dòng cùng `1 / 1 up`.
4. Chụp có thanh địa chỉ và đủ năm target. Tên ảnh `gd5-prometheus-targets.png`.

**Hình X. Prometheus thu thập dữ liệu từ năm target của hệ thống.**

### Ảnh thứ hai Dashboard Grafana

1. Trong Ubuntu mở tab mới `http://localhost:3000`.
2. Xem riêng thông tin tài khoản trong Terminal:

```bash
cd ~/projects/de32-chat
less work/grafana-access.txt
```

`GRAFANA_USER` là tên đăng nhập, `GRAFANA_PASSWORD` là mật khẩu. Đây là tài khoản quản trị Grafana, không phải tài khoản LinhChat hoặc mật khẩu Ubuntu. Không chụp Terminal chứa mật khẩu. Nhấn `q` để đóng phần xem, quay lại trình duyệt, điền vào **Email or username**, **Password** rồi **Log in**. Không gửi mật khẩu vào chat.

3. Bấm **Dashboards** ở menu trái → folder **LinhChat** → **LinhChat Overview**. Có thể mở thẳng `http://localhost:3000/d/linhchat-overview` sau đăng nhập.
4. Chọn khoảng **Last 15 minutes**, tự làm mới **15s**. Nếu số liệu vừa khởi động chưa đủ, đợi 30–60 giây rồi Refresh; không chụp dashboard trống hoặc `No data`.
5. Chụp có tên dashboard, Target UP = 5, PostgreSQL/Nginx = UP, hai biểu đồ CPU/RAM và các biểu đồ DB/web phía dưới. Bấm **Close menu** để thu menu trái nếu cần; có thể dùng Ctrl+- một nấc để vừa màn hình. Tên ảnh `gd5-grafana-dashboard.png`.

**Hình X+1. Dashboard Grafana giám sát ứng dụng, container, Nginx và PostgreSQL.**

Không cần thêm ảnh Terminal để giữ báo cáo 10–15 trang. Đánh số Hình tiếp theo số cuối của báo cáo, không cố định Hình 5/6 cũ. Có thể chỉ dùng một ảnh Grafana nếu báo cáo quá chật, giữ ảnh targets làm phụ lục/minh chứng demo.

## Đoạn ngắn cho báo cáo

Hệ thống sử dụng Prometheus để thu thập metrics từ Flask, cAdvisor và các exporter Nginx/PostgreSQL theo chu kỳ 15 giây. Grafana được cấu hình tự động bằng file provisioning và dashboard JSON, hiển thị trạng thái dịch vụ, CPU/RAM container, lưu lượng web và kết nối database. Kiểm thử gửi tin, upload tệp và tạo lại dịch vụ giám sát xác nhận số liệu cập nhật thực tế và lịch sử vẫn được lưu trong volume Docker.

## Kiểm tra lại khi cần

```bash
cd ~/projects/de32-chat
bash scripts/check-phase5.sh
```

Kỳ vọng 5/5 UP, CPU/RAM đủ 9 service, datasource OK, 11/11 panel có dữ liệu và `GIAI_DOAN_5_OK`. Đây là kiểm tra API thật, không chỉ kiểm tra container đang chạy. Mốc commit 2 có thông điệp `feat: milestone 2 - Prometheus and Grafana monitoring`; `git log -2 --oneline` hiển thị hai mốc đầu. Chưa push GitHub.

Khi cần khởi động lại toàn bộ phần đã làm, dùng `docker compose --profile monitoring up -d`. Không bật profile logging ở giai đoạn này, không thêm `compose.phase3.yml` vì sẽ mở lại cổng app5000. Website vẫn `http://localhost`; pgAdmin vẫn `http://localhost:5050`. Cổng Grafana3000/Prometheus9090 chỉ bind127.0.0.1 của VM; từ Windows cần SSH tunnel, không mở rộng cổng quản trị ra mạng chỉ để chụp ảnh.

## Ý nghĩa và giới hạn

- HTTP/tin/upload là counter từ lúc tiến trình app chạy, không phải tổng hàng lịch sử trong DB. App restart làm counter khởi đầu lại; dùng `rate`/`increase` khi so sánh theo thời gian. Metrics không mang username, email, nội dung tin, token hoặc tên tệp.
- Socket.IO đếm kết nối đã đăng nhập; một tài khoản có nhiều tab có thể có nhiều kết nối. Số người online đếm riêng. Khi không ai mở LinhChat, Socket.IO = 0 là đúng, không phải lỗi `No data`.
- CPU100% là một lõi logic; VM có2CPU nên tổng có thể vượt100%. RAM dùng working set, không đồng nghĩa toàn bộ cache hoặc memory limit. cAdvisor chỉ giữ nhãn project/service, bỏ container one-off và cgroup root. Dashboard chọn instance mới nhất của mỗi service còn last_seen trong60giây để không cộng container cũ sau recreate. Phạm vi là Compose hiện tại mỗi service một container, chưa phải dashboard cho nhiều replica.
- PostgreSQL exporter dùng role `postgres_exporter`, có `pg_monitor`, không superuser/createDB/createRole. Metrics/status nội bộ vẫn bị Nginx chặn ở cổng80.
- Prometheus giữ tối đa7ngày và512MB TSDB, giới hạn đến trước có hiệu lực; head/WAL có thể vượt kích thước khối này. Prometheus/Grafana có volume riêng. Có giới hạn RAM cho monitoring để phù hợp VM3.8GiB.
- cAdvisor cần privileged, đọc mount host và Docker socket để lấy số liệu container; đây là ngoại lệ quyền mạnh cần nêu ở phần hardening. Mount read-only không biến quyền Docker API thành an toàn tuyệt đối. Không mở cổng cAdvisor/exporter ra host.
- Chưa có alert rule/email cảnh báo hoặc logging Loki ở mốc này. Không tự suy ra hệ thống HA, production HTTPS hoặc giám sát nhiều worker.

Nguồn cấu hình: [Prometheus configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/), [Grafana provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/), [cAdvisor Docker](https://github.com/google/cadvisor#quick-start-running-cadvisor-in-a-docker-container), [PostgreSQL exporter](https://github.com/prometheus-community/postgres_exporter), [Nginx exporter](https://github.com/nginx/nginx-prometheus-exporter).

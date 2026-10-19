# GĐ8 — Bàn giao cục bộ và Hình 13

Người dùng đã xác nhận Hình 12 là ảnh GĐ7, ngày19/10/2026. Không đánh lại Hình1–12 hoặc sửa Demo.docx khi chưa có bản cuối/đề nghị chỉnh file. Ảnh mới tiếp theo là **Hình13**.

## Đã chuẩn bị

Kiểm tra trên UbuntuVM ngày19/10/2026: `152 passed in63.25s`, script bàn giao `GIAI_DOAN_8_LOCAL_OK`; 11service chạy, 10bảng khớp, Prometheus5/5UP, Grafana11/11panel và3LogQL có dữ liệu. Chưa pushGitHub/hoàn thiệnWordcuối; không gọi tất cả điều kiện nộp bài đã xong.

- README triển khai/địa chỉ/kiểm tra; tài liệu kiến trúc và đủ10bảng khớp models.py; kịch bản demo5–7phút.
- Script bàn giao đọc runtime: Compose, schema, hardening, monitoring, logging và lịch sử3mốc. Không thay thế bài test clean-install/restore, không chạy lại logout hoặc tạo tin mẫu khi chụp.
- `bash scripts/test-unit.sh` chạy pytest trong container tạm cùng image app, không network/.env/volumePostgreSQL. Các test chức năng dùng SQLite riêng; kiểm tra runtime/SQL/WebSocket thật là các bằng chứng độc lập của GĐ3–7.
- Source ZIP riêng trong outputs ở Windows; không có.env/work/outputs/.git. ZIP không chứa lịch sửGit, vì vậy không dùng ZIP thay repository nộp bài.

## Chụp một ảnh: Hình 13

Terminal Ubuntu, phóng to cửa sổ:

```bash
cd ~/projects/de32-chat
clear
bash scripts/check-phase8.sh
```

Chờ đến **GIAI_DOAN_8_LOCAL_OK** rồi chụp từ tiêu đề GĐ8 đến dòng đó, giữ ba mốc commit và dòng PENDING. Nếu có FAIL, chưa chụp làm bằng chứng đạt; gửi thông báo lỗi để kiểm tra. Script không đăng xuất, không xóa/sửa dữ liệu ứng dụng. Nó xác minh các API giám sát nên có thể mất một lúc; không cần chụp riêng 152 dòng test.

**Hình 13. Kiểm tra tổng hợp hệ thống LinhChat và ba mốc commit trước bàn giao.**

## Đoạn ngắn cho báo cáo

Ở giai đoạn bàn giao, source được hoàn thiện README, mô tả kiến trúc và mô hình dữ liệu PostgreSQL, kèm kịch bản demo. Script Bash/Python kiểm tra trực tiếp Docker Compose, schema, Prometheus/Grafana, Loki và cấu hình hardening trên Ubuntu VMware. Git lưu ba mốc phát triển ứng dụng, monitoring và logging; secret được loại khỏi source nộp. Kết quả kiểm tra tổng hợp được thể hiện ở Hình13.

Không viết “đã nộp GitHub” trước khi repository thực sự được push. Có thêm các commit fix/tài liệu sau ba mốc, không coi đó là vi phạm yêu cầu tối thiểu03commit.

## Gợi ý tổng báo cáo 10–15 trang

| Nội dung | Dự kiến |
|---|---|
| Bìa đúng thông tin sinh viên, mục lục/mục tiêu | 2trang |
| Kiến trúc, công cụ và mô hình dữ liệu | 2trang |
| Môi trường, triển khai Compose và chức năng chat đã chụp | 3–4trang |
| Nginx, monitoring, logging, hardening | 3–4trang |
| Kiểm thử/bàn giao, kết luận/giới hạn và tài liệu tham khảo | 1–2trang |

Tổng11–14trang là ngân sách nội dung, không phải số trang Word đã render. Giữ các ảnh Hình1–12 hiện có; Hình13 là ảnh tổng kết, không bổ sung ảnh riêng cho từng bảng hoặc từngtest. Ảnh phải đủ đọc; cắt phần trống, không thu nhỏ chữ quá mức.

## Còn cần người dùng chốt trước khi nộp

1. Mã sinh viên và URL repository GitHub theo quy tắc đề; quyền push chỉ thực hiện khi người dùng yêu cầu rõ. Không tự tạo remote/repo công khai. Source/Git đầy đủ trên VM, ZIP không chứaGit.
2. Báo cáo Word cuối10–15trang: kiểm tra số hình trùng, bìa/MSSV/lớp, mục lục, chú thích và đánh trang. Chưa sửa hoặc xác minh dàn trang Demo.docx ở bước này.
3. LinkGitHub có đủ lịch sử3mốc vàREADME; bỏsecret/dữ liệu thật. Trước nộp, mở link bằng đúng quyền truy cập của giảng viên.

HTTP chưa TLS; cAdvisor/Promtail có quyền mạnh, Promtail EOL; bản một instance và chưa pentest/restore thử trên VM mới. GĐ8localOK không đồng nghĩa hoàn tất các điều kiện nộp bài này.

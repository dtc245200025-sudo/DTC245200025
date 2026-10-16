# Giai đoạn 3.4b Tin nhắn nâng cao

Đã chạy trên Ubuntu VMware: 131/131 kiểm thử, MESSAGES34B_LIVE_CHECK_OK và MESSAGES34B_PERSISTENCE_OK. Gửi/nhận/xem, tìm kiếm, emoji, ảnh/file đều có ở nhóm và riêng. File và thời gian xác nhận còn sau tạo lại app; người ngoài vẫn bị chặn. Các kiểm tra lịch sử, Bạn bè và phòng cũ đều đạt.

## Một ảnh cho báo cáo

Đã đọc nội dung Demo.docx của người dùng, chỉ đọc không sửa. Báo cáo đã có môi trường, Flask, chat nhóm, PostgreSQL/pgAdmin, Compose, Bạn bè và hồ sơ. Có hai lựa chọn Hình 5 và hai chú thích cùng Hình 7: giữ một phương án, đánh lại số khi hoàn thiện. Chỉ thêm hoặc thay một ảnh tin nhắn nâng cao; không cần ảnh riêng cho từng tính năng. Dành dung lượng còn lại cho Nginx, monitoring, logging, hardening và ba mốc commit. Chưa xác minh dàn trang Word vì runtime thiếu LibreOffice; không coi chỉ số Pages lưu trong file là số trang đã kiểm chứng.

1. Trong Ubuntu mở `http://localhost:5000/direct`, Ctrl+F5 và đăng nhập A. B dùng trình duyệt khác hoặc cửa sổ riêng tư, đăng nhập và mở cùng hội thoại. Nếu chưa có hội thoại, vào Bạn bè và bấm Nhắn tin.
2. A gửi một tin `Kiểm thử LinhChat 😊`; B mở hội thoại và bấm vào ô nhập để ứng dụng nhận biết trang đang được xem. Ở A, tin tự chuyển sang **Đã xem**. Nếu B chỉ đang ở trang khác, tin riêng mới nhận trực tiếp có thể ở **Đã nhận**, chưa được đánh dấu xem.
3. A hoặc B bấm **Đính kèm tệp**, chọn ảnh JPG/PNG/WebP hoặc tệp nhỏ như TXT/PDF, rồi **Gửi**. Ảnh có preview; file có liên kết tải xuống. Không chọn dữ liệu cá nhân hoặc tài liệu chứa mật khẩu cho ảnh minh chứng.
4. Chụp vùng có tên hội thoại, thanh tìm tin, một tin mới với trạng thái, ảnh/tệp và nút Emoji/Đính kèm. Có thể thu nhỏ trình duyệt một nấc. Đặt tên `tin-nhan-nang-cao-linhchat.png`; số Hình dùng số tiếp theo sau khi bạn đánh lại thứ tự báo cáo.
5. Nếu muốn minh chứng thời gian thay vì ảnh chat tổng hợp, bấm tin hoặc nút **ⓘ** của tin mới do A gửi. Ở A hiện thời gian gửi và thời gian B nhận/xem. Đây là ảnh thay thế, không bắt buộc thêm ảnh thứ hai.

Bộ A/B/C đã chuẩn bị: `less work/gd34b-demo-access.txt` trong project trên VM. Xem riêng rồi nhấn `q`, không chụp mật khẩu. A/B có hội thoại và phòng thử, ảnh/file cùng trạng thái thật; C không được truy cập dữ liệu của họ.

## Chú thích và đoạn để viết báo cáo

**Hình X. Tin nhắn nâng cao trên LinhChat.**

Ứng dụng sử dụng Flask-SocketIO để cập nhật trạng thái đã gửi, đã nhận và đã xem theo thời gian thực. SQLAlchemy lưu tin nhắn, thời gian xác nhận và tệp đính kèm trong PostgreSQL. Giao diện JavaScript hỗ trợ tìm tin, gợi ý emoji và gửi ảnh/file tối đa 10 MB; máy chủ kiểm tra kích thước và quyền truy cập trước khi lưu hoặc tải xuống.

## Phạm vi và lưu ý kỹ thuật

- Đã gửi là máy chủ lưu thành công. Đã nhận là trình duyệt nhận nội dung và gửi xác nhận; online không tự đồng nghĩa đã nhận. Đã xem là tin hiện trong vùng chat có focus, không bị hộp thoại che; không chứng minh người thật đã đọc hiểu nội dung.
- Các mốc chỉ ghi lần đầu. Nhóm hiển thị số người nhận/xem trên tổng người nhận tại thời điểm gửi. Người vào sau không xác nhận thay người nhận cũ. Người gửi xem toàn bộ xác nhận; người nhận chỉ xem thời gian của chính mình.
- Tin có trước nâng cấp hiện Lịch sử cũ, không tạo thời gian giả. Tìm nội dung/tên file dùng POST, tối đa 50 kết quả, không đưa từ khóa vào URL. Có tải lịch sử theo lô 100 tin.
- Emoji chọn từ nút Emoji hoặc gõ `:cuoi`, `:tim` để hiện gợi ý; không cần dịch vụ ngoài/CDN.
- Giới hạn mỗi tệp 10 MiB = 10.485.760 byte, mỗi lần gửi một tệp. File rỗng và file vượt giới hạn bị từ chối. Ảnh JPG/PNG/WebP kiểm tra nội dung và tối đa 16 triệu pixel; preview PNG thu nhỏ tối đa 1600px, không mang metadata. File tải xuống giữ nguyên byte gốc, không tự loại metadata của file gốc.
- Tệp gốc/preview ở PostgreSQL, không có thư mục upload công khai hoặc phụ thuộc writable filesystem app. Tệp thường buộc tải xuống với octet-stream, Content-Disposition attachment, nosniff và CSP sandbox; không render HTML/SVG người dùng tải lên. Không quét virus: chỉ mở tệp từ người tin cậy. Hệ thống chưa mã hóa đầu-cuối và chưa đi qua Nginx/HTTPS.
- Rời phòng mất quyền tải file của phòng; hủy kết bạn vẫn xem/tải lịch sử riêng nhưng không gửi mới cho tới khi kết bạn lại. Nonce chống trùng cho tin và file khi thử gửi lại.
- Cấu hình vẫn một worker, trạng thái đang nhập/presence trong bộ nhớ; không phải triển khai nhiều instance. Chưa tạo commit mốc 1, còn bước Nginx theo đề.

Kiểm tra tại VM: `bash scripts/check-messages.sh`; mong đợi 131 passed, health ok, invalid_receipt_times = 0, oversized_attachments = 0 và GIAI_DOAN_34B_OK. Không cần thêm ảnh Terminal vào báo cáo.

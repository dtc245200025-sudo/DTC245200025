# Giai đoạn 3.3b – Bạn bè LinhChat

Đã triển khai và kiểm tra trên Ubuntu VMware. 70/70 kiểm thử đạt; PostgreSQL và WebSocket thật kiểm tra tìm người, đúng quyền lời mời, hai yêu cầu ngược chiều, online/offline nhiều kết nối. Sau restart đạt FRIENDS33B_PERSISTENCE_OK, ROOMS32_PERSISTENCE_OK và PERSISTENCE_AFTER_RESTART_OK: bạn bè/lời mời, phòng và lịch sử vẫn còn. Không xóa dữ liệu chat cũ. Nginx chưa triển khai; chat riêng và tin nhắn nâng cao thuộc 3.4.

## Chụp một hình cho báo cáo

1. Trong Firefox Ubuntu, mở `http://localhost:5000/friends`, nhấn Ctrl+F5 rồi đăng nhập tài khoản A.
2. Có thể dùng tài khoản A/B đang sử dụng: A tìm đúng username hoặc email đầy đủ của B, bấm **Kết bạn**. B đăng nhập bằng trình duyệt khác hoặc cửa sổ riêng tư, vào **Bạn bè → Lời mời → Chấp nhận**. Hai tab thường cùng trình duyệt dùng chung phiên, không tách được A/B.
3. Hoặc dùng bộ tài khoản đã chuẩn bị: trong Terminal Ubuntu, chạy `cd ~/projects/de32-chat` rồi `less work/gd33b-demo-access.txt`. Chỉ xem riêng username/mật khẩu, bấm `q` để thoát; không chụp màn hình Terminal này. A/B đã là bạn, C đang gửi lời mời cho A.
4. Ở A chọn tab **Bạn bè**; giữ B đăng nhập để thấy chấm xanh **Đang hoạt động**. Chụp vùng gồm logo LinhChat, thanh tìm kiếm, tab Bạn bè/Lời mời và thẻ của B. Đặt tên `07-ban-be-linhchat.png`. Tài khoản hiện cuối trang bên trái; có thể thu nhỏ trình duyệt một nấc nếu cần đưa vào cùng ảnh.
5. Để kiểm tra offline, B đăng xuất hoặc đóng tất cả tab LinhChat của B. A tự đổi sang **Ngoại tuyến**, không cần F5. Không bắt buộc thêm ảnh này vào báo cáo 10–15 trang.

Nếu muốn minh chứng lời mời, chụp thêm tab **Lời mời** ở A với yêu cầu từ C và hai nút **Chấp nhận/Từ chối**. Đây là ảnh phụ, không bắt buộc. Không chụp mật khẩu, `.env` hoặc liên kết mời phòng riêng tư.

## Chú thích và đoạn báo cáo

**Hình 7. Tìm kiếm, quản lý bạn bè và trạng thái hoạt động trên LinhChat.**

Chức năng Bạn bè được xây dựng bằng Flask và SQLAlchemy, lưu quan hệ và lời mời trong PostgreSQL. Người dùng tìm bạn theo tên hoặc email, gửi và xử lý lời mời; Flask-SocketIO cập nhật danh sách và trạng thái online/offline theo thời gian thực. Giao diện HTML/CSS/JavaScript hỗ trợ sáng hồng phấn và tối tím than.

## Kiểm tra kỹ thuật (không cần chụp thêm)

Trong thư mục project trên VM, chạy `bash scripts/check-friends.sh`. Bộ kiểm thử ở mốc 3.3b đạt 70 passed; sau bổ sung 3.4a tăng thành 98 passed. Kết quả còn có health `ok`, duplicate_pairs = 0, invalid_pairs = 0 và `GIAI_DOAN_33B_OK`. Kiểm thử dùng database tạm riêng, không xóa database chatdb.

Email riêng tư được dùng để tìm khớp đầy đủ nhưng không hiện trên kết quả; từ khóa gửi bằng POST, không nằm trong URL. Người gửi không được tự chấp nhận; người ngoài không xử lý lời mời. Hủy kết bạn không xóa lịch sử/phòng chat. Mỗi danh sách tối đa 100 người/lời mời, tìm kiếm tối đa 50 kết quả.

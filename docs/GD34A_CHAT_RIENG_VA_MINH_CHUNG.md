# Giai đoạn 3.4a – Chat riêng và trạng thái đang nhập

Đã chạy trên Ubuntu VMware, đạt 98/98 kiểm thử, DIRECT34A_LIVE_CHECK_OK và DIRECT34A_PERSISTENCE_OK. Kiểm tra hồi quy Bạn bè, phòng Public/Private và chat nhóm đều đạt. Có backup trước nâng cấp, không xóa dữ liệu cũ.

## Chụp một Hình 8 (tùy chọn)

Báo cáo tổng chỉ 10–15 trang: có thể dùng một hình chat riêng này hoặc đợi hoàn tất 3.4b rồi gộp minh chứng, không cần chụp riêng từng thao tác.

1. Trong Firefox Ubuntu mở `http://localhost:5000/friends`, Ctrl+F5 và đăng nhập A. Dùng A/B đang là bạn; thẻ bạn bè có nút **Nhắn tin**. Nếu chưa là bạn, gửi/chấp nhận lời mời trước.
2. A bấm **Nhắn tin** trên thẻ B. B đăng nhập bằng trình duyệt khác hoặc cửa sổ riêng tư, bấm **Tin nhắn** trên menu và chọn hội thoại với A. Không dùng hai tab thường chung phiên cho hai tài khoản.
3. A gửi `Chào bạn, mình thử chat riêng trên LinhChat nhé!`; B gửi `Mình đã nhận được tin nhắn rồi nhé!`. A thấy hai bong bóng và giờ gửi. “Đã gửi” hiện tại chỉ xác nhận đã lưu máy chủ, chưa phải trạng thái đã nhận/đã xem.
4. Chụp màn hình A gồm logo LinhChat, danh sách hội thoại bên trái, tên/trạng thái B và hai tin nhắn. Lưu `08-chat-rieng-linhchat.png`. Thu nhỏ một nấc nếu cần đưa toàn bộ giao diện vào ảnh.
5. Muốn kèm “đang nhập”, để B gõ chậm vài ký tự và chưa gửi; chụp A khi có dòng `B đang nhập…`. Dòng này tự tắt khoảng 2 giây sau khi ngừng gõ; chỉ thông báo đang gõ, không truyền nội dung bản nháp. Không bắt buộc chụp thêm hình.

Có sẵn bộ A/B/C để thử: trong Terminal tại thư mục project chạy `less work/gd34a-demo-access.txt`, chỉ xem riêng rồi nhấn `q`; không chụp mật khẩu. A/B đã là bạn và có lịch sử riêng; C không được truy cập hội thoại của A/B.

## Chú thích và đoạn báo cáo

**Hình 8. Trò chuyện riêng và trạng thái đang nhập trên LinhChat.**

Chat riêng được xây dựng bằng Flask-SocketIO và SQLAlchemy, lưu hội thoại cùng tin nhắn trong PostgreSQL. Máy chủ kiểm tra quyền của hai tài khoản trước khi cho xem hoặc gửi tin; mã gửi giúp tránh tạo tin trùng khi thử lại. Trạng thái đang nhập được cập nhật realtime ở chat riêng và phòng nhóm mà không lưu nội dung bản nháp.

## Phạm vi hiện tại

- Cần là bạn bè để mở hoặc gửi tin mới. Sau hủy kết bạn, lịch sử vẫn xem được qua menu Tin nhắn; kết bạn lại dùng cùng hội thoại.
- Tin nhắn văn bản 1–1000 ký tự. Có lịch sử 100 tin gần nhất, nút xem tin trước, đồng bộ khi kết nối lại. Danh sách hiển thị tối đa 100 hội thoại gần đây.
- Chỉ hai tài khoản tham gia có quyền HTTP và Socket.IO; người thứ ba nhận 404 khi dò đường dẫn.
- “Riêng” là kiểm soát truy cập, **không phải mã hóa đầu-cuối**; quản trị database vẫn có thể xem dữ liệu. Chưa có Nginx/HTTPS ở giai đoạn này.
- 3.4b còn chờ: đã nhận/đã xem và thời gian chi tiết, tìm tin nhắn, emoji/gợi ý, gửi ảnh và file chat tối đa 10 MB. Không ghi báo cáo rằng các phần này đã xong.

Trong project trên VM chạy `bash scripts/check-direct.sh` để kiểm tra; không cần đưa thêm ảnh Terminal vào báo cáo. Dấu hoàn thành: `GIAI_DOAN_34A_OK`, health `ok`, duplicate_direct_pairs = 0, invalid_direct_authors = 0.

Tham khảo cơ chế sự kiện và room của [Flask-SocketIO](https://flask-socketio.readthedocs.io/en/stable/getting_started.html#rooms).

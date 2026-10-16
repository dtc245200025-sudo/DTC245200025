# Giai đoạn 3.3a – Hồ sơ cá nhân LinhChat

Đã triển khai và kiểm tra trên Ubuntu VMware ngày 16/10/2026. Phần này được ưu tiên theo yêu cầu Profile mới; không đồng nghĩa toàn bộ Giai đoạn 3.3 hoặc Giai đoạn 3 đã hoàn thành.

## Đã thực hiện

- Hồ sơ của mình: tên hiển thị chỉnh sửa được; username dùng đăng nhập, không đổi được; giới thiệu tối đa 150 ký tự; ngày tham gia; số phòng đã tham gia.
- Avatar chữ viết tắt hoặc ảnh. Bấm biểu tượng máy ảnh để chọn JPG/PNG/WebP tối đa 10 MiB và 16 triệu điểm ảnh. Máy chủ giải mã ảnh thật, thu nhỏ tối đa 256×256, mã hóa lại PNG và bỏ metadata. Avatar lưu cùng PostgreSQL, còn sau restart.
- Menu avatar góc trên bên phải: tên, @username, trạng thái, Xem hồ sơ cá nhân, Đổi mật khẩu, Cài đặt email, Đăng xuất. Menu đóng khi nhấn Escape hoặc bấm bên ngoài; điều hướng được bằng bàn phím.
- Tab Thông tin cá nhân và Bảo mật trên cùng trang; ba trường mật khẩu có nút hiện/ẩn. Mật khẩu mới 8–128 ký tự, phải khác mật khẩu cũ và xác nhận trùng nhau. Werkzeug kiểm tra/hash mật khẩu; không lưu văn bản thuần. Đổi thành công yêu cầu đăng nhập lại và thu hồi các kết nối cũ.
- Hồ sơ người khác chỉ xem, không có biểu mẫu chỉnh sửa. Trong phòng chat bấm tên người gửi để mở. Tắt Hồ sơ công khai sẽ ẩn tên hiển thị, giới thiệu, email và avatar với người khác; username/trạng thái vẫn là định danh trong ứng dụng. Email mặc định riêng tư.
- Online/offline qua Flask-SocketIO; người dùng chỉ ngoại tuyến khi đóng kết nối cuối cùng. Khi mất kết nối, giao diện hiện Chưa có kết nối, không khẳng định sai là ngoại tuyến.
- Giao diện sáng trắng/hồng phấn và tối tím than; tài khoản hiện tại vẫn ở góc dưới trái.

## Kết quả kiểm tra

- 38/38 kiểm thử tự động đạt trong Docker trên VM: thông tin hồ sơ, quyền xem, chống sửa username, CSRF, mật khẩu, avatar và nhiều tab online.
- `PROFILE_LIVE_CHECK_OK`: HTTP + PostgreSQL + WebSocket thật, gồm hồ sơ công khai/riêng tư, avatar, online/offline và thu hồi phiên khi đổi mật khẩu trên tài khoản kiểm thử riêng.
- `LIVE_CHAT_CHECK_OK` và `PERSISTENCE_AFTER_RESTART_OK`: chat hai chiều và lịch sử PostgreSQL cũ vẫn hoạt động sau cập nhật/restart.
- Đã xem trực tiếp trên trình duyệt: chế độ sáng/tối, hai tab, menu đóng bằng Escape/bấm ngoài, nút hiện/ẩn với ô mật khẩu trống.
- Có backup database/source trước migration tại `work/backups` trên VM; không xóa dữ liệu và không thay mật khẩu tài khoản demo cũ.

## Chụp ảnh ngay lúc này

Trong trình duyệt Ubuntu mở `http://localhost:5000/profile`, đăng nhập tài khoản của mình và nhấn Ctrl+F5. Tài khoản thử trong ảnh mẫu của trợ lý không phải tài khoản của bạn.

| Tên ảnh | Thao tác và phần cần thấy | Chú thích báo cáo |
|---|---|---|
| GD3.3a-01-ho-so.png | Tab Thông tin cá nhân; avatar, tên, @username, trạng thái, ô tên/username/giới thiệu. Điền tên và giới thiệu rồi Lưu thay đổi; tải lại để thấy vẫn được lưu. Có thể chụp thêm phần dưới nếu cửa sổ thấp. | Hồ sơ cá nhân cho phép cập nhật tên hiển thị và giới thiệu; username được khóa để giữ định danh đăng nhập. |
| GD3.3a-02-menu.png | Bấm avatar góc trên phải để mở menu, chụp cả menu và trang phía sau. Sau đó thử Escape và bấm ngoài để kiểm tra đóng. | Menu tài khoản cung cấp các thao tác hồ sơ, bảo mật, cài đặt và đăng xuất. |
| GD3.3a-03-bao-mat.png | Chọn tab Bảo mật; thấy ba trường và nút Cập nhật mật khẩu. Để trống hoặc chỉ chụp khi ký tự đang được che; không chụp mật khẩu rõ. | Đổi mật khẩu yêu cầu xác nhận mật khẩu hiện tại và nhập lại mật khẩu mới; mật khẩu được hash trước khi lưu. |
| GD3.3a-04-kiem-thu.png | Terminal tại thư mục project, chạy `bash scripts/check-profile.sh`; chụp 38 passed, health ok và dòng GIAI_DOAN_33A_PROFILE_OK. | Bộ kiểm thử và kiểm tra schema PostgreSQL xác nhận tính năng hồ sơ hoạt động trên Ubuntu VMware. |
| GD3.3a-05-toi.png (bổ sung) | Bấm Chế độ tối trên trang hồ sơ. | Giao diện hồ sơ hỗ trợ nền tím than và ghi nhớ lựa chọn sáng/tối. |

Nếu tự thử đổi mật khẩu, bạn tự nhập ba trường rồi bấm cập nhật; ứng dụng sẽ đăng xuất các phiên cũ. Không cần đổi mật khẩu chỉ để lấy ảnh giao diện.

Kiểm tra người khác: dùng Firefox thường cho tài khoản A và cửa sổ riêng tư cho B (hoặc hai trình duyệt khác nhau trong Ubuntu), cùng mở một phòng. Bấm tên người gửi để xem hồ sơ. Đóng toàn bộ cửa sổ/kết nối của B để A thấy B chuyển ngoại tuyến. Tài khoản A và B trong hai tab cùng một phiên trình duyệt không được tách đăng nhập.

## Nội dung báo cáo gợi ý

Hệ thống LinhChat bổ sung trang hồ sơ cá nhân và trang xem hồ sơ người dùng khác. Người dùng có thể thay đổi tên hiển thị, giới thiệu, avatar và thiết lập quyền hiển thị hồ sơ/email; username được giữ cố định. Tab Bảo mật sử dụng Werkzeug để xác thực mật khẩu hiện tại và hash mật khẩu mới, đồng thời thu hồi phiên đăng nhập cũ sau khi cập nhật. Flask-SocketIO cập nhật trạng thái online/offline theo thời gian thực. Chức năng đã được triển khai bằng Docker trên Ubuntu VMware, đạt 38 kiểm thử tự động và kiểm tra tích hợp với PostgreSQL cùng WebSocket thực tế.

## Còn lại và bước tiếp theo

Tiếp theo trở lại 3.2: phòng Public/Private, giới hạn thành viên, link mời/mật khẩu/phê duyệt. Phần 3.3b tìm kiếm/kết bạn và 3.4 chat riêng/tin nhắn nâng cao vẫn đang chờ. Trạng thái Bận/Vắng mặt là mở rộng, chưa triển khai. Chưa tạo mốc commit 1 vì còn ứng dụng mở rộng và Nginx. Không commit `.env`, tài khoản thử, backup hoặc dữ liệu riêng tư.

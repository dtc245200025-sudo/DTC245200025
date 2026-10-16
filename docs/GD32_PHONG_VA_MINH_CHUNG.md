# Giai đoạn 3.2 – Phòng Public/Private LinhChat

Đã triển khai và kiểm tra trên Ubuntu VMware ngày 16/10/2026. Mở `http://localhost:5000` trong Ubuntu, nhấn Ctrl+F5 trước khi chụp.

## Đã hoàn thành

| Loại phòng | Cách vào | Quyền và giới hạn |
|---|---|---|
| Public | Xem và tham gia → Tham gia phòng | Phòng mới chọn 2–500 người, tính cả chủ phòng. Hết chỗ sẽ từ chối người mới. |
| Private – Mật khẩu | Tìm tên phòng → nhập mật khẩu → Tham gia | Chỉ khi đúng mật khẩu mới được xem lịch sử và gửi/nhận tin. Mật khẩu phòng được hash. |
| Private – Phê duyệt | Gửi yêu cầu → chủ phòng Phê duyệt/Từ chối | Chỉ chủ phòng xử lý được. Trang quản lý cập nhật yêu cầu mới; người chờ tự mở phòng sau khi duyệt. |
| Private – Link mời | Chủ phòng tạo link trong Quản lý → người được mời mở link, đăng nhập và bấm tham gia | Không xuất hiện trong tìm kiếm của người chưa tham gia. Thay link vô hiệu link cũ, không loại thành viên đã được nhận. |

- Không tự gia nhập chỉ vì mở địa chỉ phòng. Cấp thành viên dùng POST có CSRF; HTTP và Socket.IO đều kiểm tra quyền.
- Rời phòng sẽ mất quyền gửi/nhận tin ở mọi tab của tài khoản đó. Chủ phòng cần ở lại để quản lý; chưa có chuyển quyền chủ phòng hay quản trị viên toàn hệ thống.
- Tìm phòng không phân biệt hoa/thường; có lọc Phòng đã tham gia. Phòng cũ giữ nguyên nội dung/thành viên và tiếp tục Public không giới hạn; Public mới bắt buộc có giới hạn.
- Database chỉ lưu hash token mời. Link dùng token sau dấu `#`, không gửi token trong địa chỉ HTTP/access log. Link chỉ hiện lúc tạo; muốn lấy link mới thì tạo lại. Khi cần đăng nhập, lời mời tạm giữ trong sessionStorage của tab và xóa khi gửi tham gia.
- Bản này vẫn là HTTP nội bộ VMware; chưa phải triển khai Internet. HTTPS/hardening tổng thể còn ở giai đoạn sau.

## Kết quả kiểm tra

- 55/55 kiểm thử đạt cả cục bộ và trong Docker trên VM.
- ROOMS32_LIVE_CHECK_OK: PostgreSQL/WebSocket thật; hai người cùng tranh chỗ cuối cho đúng một thành công, một từ chối, không vượt sức chứa.
- Đã thử mật khẩu sai/đúng, không lộ lịch sử khi chưa có quyền, chặn gửi/join Socket.IO, từ chối người không phải chủ phòng cố duyệt, link giả/link cũ, ngừng nhận tin sau khi rời phòng.
- ROOMS32_PERSISTENCE_OK sau restart: phòng đầy, lịch sử Private, yêu cầu chờ và hash link mời còn nguyên.
- PERSISTENCE_AFTER_RESTART_OK: tài khoản/lịch sử từ Giai đoạn 3 cũ vẫn truy cập được.
- Kiểm tra trình duyệt thực tế: Public/Private và các trường tương ứng, tìm kiếm/phòng đầy, yêu cầu mới hiện trên trang quản lý và người được duyệt tự vào phòng. Luồng mở link khi chưa đăng nhập → đăng nhập → quay lại lời mời → tham gia đã chạy đạt.
- Backup trước nâng cấp: `work/backups/before-phase31-20261016-143546.*` trên VM (script cũ vẫn dùng tên prefix before-phase31). Sau migration, trước khi thêm dữ liệu thử, vẫn đủ 9 tài khoản, 4 phòng, 12 tin nhắn.

## Chuẩn bị tài khoản và phòng để chụp

Dùng Firefox thường cho A/chủ phòng và cửa sổ riêng tư hoặc trình duyệt khác cho B. Không dùng hai tab cùng phiên để đăng nhập hai tài khoản.

Đã chuẩn bị bộ A/B/C và bốn phòng bắt đầu `GD3.2`. Xem thông tin riêng tại Terminal Ubuntu:

```bash
cd ~/projects/de32-chat
cat work/gd32-demo-access.txt
```

Không chụp màn hình này, không gửi mật khẩu/link mời. Đọc xong đóng Terminal hoặc xóa màn hình trước khi chụp kiểm thử. File quyền 600, ngoài Git.

- A là chủ bốn phòng thử. B đã được duyệt; C vẫn đang chờ để chụp. Chụp trạng thái chờ và trang quản lý trước khi A duyệt C.
- Public thử đã đủ 2/2. Trong B/C có một người đã vào, người còn lại sẽ thấy phòng đầy. Tài khoản cũ của bạn chưa tham gia phòng này cũng thấy đầy.
- B đã rời phòng mật khẩu để bạn thử sai/đúng. Mật khẩu phòng thử nằm trong file trên; không dùng cho tài khoản thật.
- B/C đã tham gia phòng link mời. Muốn thử một người mới: A tạo link mới rồi mở bằng tài khoản cũ của bạn hoặc tài khoản khác chưa thuộc phòng đó.
- Bạn cũng có thể tự tạo lại các phòng bằng tài khoản của mình, thay vì dùng bộ thử.

## Chụp theo thứ tự

| Tên ảnh | Thao tác, phần cần thấy | Chú thích báo cáo |
|---|---|---|
| GD3.2-01-tao-public.png | Tạo phòng: tên, Public, giới hạn người và nút tạo. | Tạo phòng Public với giới hạn số thành viên, bao gồm chủ phòng. |
| GD3.2-02-tao-private.png | Chọn Private, mở lựa chọn để thấy ba phương thức. Có thể chụp thêm trường mật khẩu, giữ trống/được che. | Phòng Private hỗ trợ link mời, mật khẩu hoặc phê duyệt. |
| GD3.2-03-mat-khau.png | B mở phòng mật khẩu, thử sai; chụp thông báo sai và không có lịch sử. Sau đó thử đúng để kiểm tra. | Máy chủ kiểm tra mật khẩu trước khi cấp quyền truy cập phòng. |
| GD3.2-04-cho-duyet.png | C mở phòng phê duyệt; chụp Đang chờ chủ phòng phê duyệt, chưa có khung tin nhắn. | Người chưa được duyệt không thể truy cập nội dung phòng riêng. |
| GD3.2-05-phe-duyet.png | A mở Quản lý phòng: tên người yêu cầu, hai nút Phê duyệt/Từ chối. Chụp trước khi duyệt. | Chỉ chủ phòng quản lý yêu cầu; quyền cập nhật realtime. |
| GD3.2-06-phong-day.png | Người chưa là thành viên mở Public thử đã đủ 2/2; chụp số người và thông báo đầy. | Từ chối người mới khi phòng đạt giới hạn. |
| GD3.2-07-link-moi.png | A tạo/sao chép link, mở ở tài khoản chưa thuộc phòng. Chụp trang Tham gia phòng riêng sau khi token tự biến mất khỏi thanh địa chỉ. | Tham gia phòng riêng bằng link hợp lệ sau khi đăng nhập. |
| GD3.2-08-kiem-thu.png | Chạy script dưới; chụp 55 passed, health ok, over_capacity_rooms = 0 và GIAI_DOAN_32_OK. Có thể chia 2 ảnh. | Kiểm thử phòng và xác minh PostgreSQL trên Ubuntu VMware. |

```bash
cd ~/projects/de32-chat
bash scripts/check-phase32.sh
```

Không chụp `.env`, password_hash, token/link mời đầy đủ hay mật khẩu rõ. Ảnh báo cáo dùng ảnh thực hành của bạn, không thay bằng ảnh mẫu.

## Nội dung báo cáo gợi ý

Giai đoạn 3.2 bổ sung quản lý phòng Public và Private cho LinhChat. Phòng Public mới giới hạn số thành viên tính cả chủ phòng; khóa dòng PostgreSQL ngăn vượt sức chứa khi nhiều người cùng tham gia. Phòng Private hỗ trợ mật khẩu, link mời hoặc sự phê duyệt của chủ phòng. Máy chủ kiểm tra quyền ở cả HTTP và Socket.IO để bảo vệ lịch sử và tin nhắn. Mật khẩu phòng được hash; database chỉ lưu hash token mời. Hệ thống đạt 55 kiểm thử tự động cùng kiểm tra PostgreSQL/WebSocket thực tế; dữ liệu và quyền vẫn được giữ sau khi khởi động lại ứng dụng.

## Bước tiếp theo

Chờ xác nhận đã chụp 3.2 rồi tiếp tục 3.3b: tìm kiếm bạn bè theo tên/email và xử lý lời mời kết bạn. Hồ sơ 3.3a đã hoàn thành trước đó. Chưa tạo commit mốc 1 vì còn 3.3b, 3.4 và Nginx ở Giai đoạn 4. Không commit `.env`, tài khoản demo hoặc backup.

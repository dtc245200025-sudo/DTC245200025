# Tiến trình và bằng chứng

## Sau GĐ8 — người dùng đã chụp Hình13, tự push GitHub

- Người dùng xác nhận đã chụp Hình13 và yêu cầu tự push GitHub. Đã ghi vào mục tiêu/checklist; chưa xác minh push/nộp bài, không tự thực hiện thay. Báo cáo Word cuối vẫn chưa sửa/kiểm tra dàn trang.
- VM đang có chỉnh sửa của người dùng ở scripts/check-phase8.sh và tests/verify_delivery.py so với commitfc8bb5d; giữ nguyên, không ghi đè hoặc tự commit. Chỉ đồng bộ các file trí nhớ, không đổi source ứng dụng, không restart/test lại hoặc tạo commit mới trong lần xác nhận này. Bản ZIP đã tạo trước đó chưa chứa các chỉnh sửa riêng mới này.

## 19/10/2026 — bắt đầu GĐ8 sau Hình12

Người dùng gửi ảnh GĐ7 đủ HARDENING_INFRA_OK/GIAI_DOAN_7_OK và xác nhận đã đến Hình12; ảnh mới là Hình13. Đã đọc trí nhớ/lộ trình, xác minh Windows/VM cùng commitf578318 và trackedclean,11service đang chạy. Đang bổ sung kiến trúc/mô hình10bảng, kịch bảndemo5–7phút, guideGĐ8 vàscriptkiểmtrabàngiaođọc runtime; test-unit riêng dùngcontainer tạm khôngnetwork/.env/volumeDB. Không sửa app/DB, không push/GitHub hoặc sửaWord. Bàn giaoGitHub và số trang Word cuối vẫn cần người dùng chốt, không coi localOK là đã nộp.

## 19/10/2026 — GĐ8 cục bộ chạy đạt, chờ Hình13/GitHub/Wordcuối

- `bash scripts/test-unit.sh`: **152 passed in63.25s**, dùng image app hiện tại, source app/tests read-only, networknone, /tmptmpfs; không mount.env/volumeDB. Không sửa app/DB hoặc restart cácservice. Đây là regressionSQLite, không gọi là testPostgreSQL; các bằng chứng HTTP/SQL/WebSocket thật củaGĐ3–7 giữriêng.
- `bash scripts/check-phase8.sh`: GIAI_DOAN_8_LOCAL_OK. Kiểmtra10/10bảngPostgreSQLkhớpmodels.py/tàiliệu,11servicerunning,hardening vàliveevidenceđúngimage/config,5UP/11panel/CPU-RAM11service,3LogQLquaLoki/Grafana; Gitba mốcđúngtiêudề/thứtự. ChạyđọcAPI/schema, khôngtạo tin hoặcđăngxuất. Khônginhash/cookie/data/secret; khi lỗi khôngxảoutputcủa tiếntrìnhcon vàoảnh.
- Bổsung docs/KIEN_TRUC_VA_DU_LIEU.md, docs/KICH_BAN_DEMO.md, docs/GD8_BAN_GIAO_VA_BAO_CAO.md; README sửa hướngdẫn2phiêntrìnhduyệt (hai cửa sổprivatecóthểchungphiên). GĐ8guide chỉ mộtHình13, chúthích/đoạnngắn vàngânsách11–14trang; khôngkhẳngđịnh sốtrangWord đãrender.
- Source/tàiliệulưucommitdocsriêng, giữ3mốcbanđầuvàfixGĐ7; đồngbộVM/WindowsvàZIPriêngkhôngsecret. Chưa push/remoteGitHub; ZIPkhôngGitkhôngthayrepositorynộp. ChờHình13vàMSSV/repođích/quyềnpush; chưa sửaDemo.docx, chưa xácminhdàntrang/đánhsốhìnhcuối. Chưa clean-install/restoreVMmới/TLS/pentest.

## 16/10/2026 — trạng thái lúc tạo file trí nhớ

- GĐ1: Ubuntu/Git/Docker/Compose đã chạy, hello-world đạt; người dùng xác nhận đã chụp.
- GĐ2: source/Flask và giao diện LinhChat, 13 test ban đầu; người dùng xác nhận đã chụp.
- GĐ3 cơ bản: PostgreSQL/pgAdmin và chat hai chiều WebSocket thật, giữ lịch sử sau restart. Người dùng đã chụp Hình 5 chat và Hình 6 Query Tool JOIN messages/rooms/users, cùng Compose và các phần mở rộng trong Demo.docx.
- 3.1: email/đăng nhập/đổi theme/trang chủ, 22 test lúc mốc; dữ liệu cũ giữ nguyên.
- 3.3a (được ưu tiên theo người dùng): hồ sơ/avatar/menu/Bảo mật/riêng tư, 38 test lúc mốc; Profile realtime/kiểm tra UI đạt. Đã sửa khung hồ sơ căn đều hai bên.
- 3.2: Public/Private, quyền/người tham gia/giới hạn/phê duyệt/link/mật khẩu; 55 test lúc mốc, `ROOMS32_LIVE_CHECK_OK`, `ROOMS32_PERSISTENCE_OK` và kiểm tra tranh chỗ cuối PostgreSQL đạt.
- 3.3b: Bạn bè, 70 test lúc mốc, `FRIENDS33B_LIVE_CHECK_OK`, UI hai phía tự cập nhật; người dùng chọn làm Bạn bè trước Nginx.
- 3.4a: chat riêng + đang nhập nhóm/riêng; 98 test lúc mốc, `DIRECT34A_LIVE_CHECK_OK`, `DIRECT34A_PERSISTENCE_OK`, hồi quy nhóm đạt.
- 3.4b: gửi/nhận/xem, thời gian, tìm/emoji/ảnh/file10 MiB; 131 test lúc mốc, `MESSAGES34B_LIVE_CHECK_OK`, `MESSAGES34B_PERSISTENCE_OK`; UI sáng/tối, tải tệp/preview/chi tiết thời gian đạt. Cũ không tạo receipt giả.

## 16/10/2026 — sửa thiếu thông báo

Nguyên nhân: thiếu UI toast/badge; nhóm chỉ gửi sự kiện cho người mở phòng. Đã thêm `notifications.py` và `notifications.js`, sự kiện riêng theo người nhận cho cả nhóm/riêng; unread tính từ receipt chưa xem trong PostgreSQL, lọc quyền thành viên. Nhận không xóa unread, GET không đánh dấu xem, seen đồng bộ qua nhiều tab. Không phát popup cho người gửi/người ngoài, retry không tạo lặp, reconnect chỉ khôi phục badge. Có điều kiện không báo nổi khi cửa sổ chat đúng đang focus và ở cuối khung.

- 9 test bổ sung, tổng **140 passed** ở Windows (324.37s) và Ubuntu container (67.05s).
- `NOTIFICATIONS_LIVE_OK`: HTTP/PostgreSQL/WebSocket thật, nhận khi ở ngoài chat, đúng người, chống trùng, delivered/seen, offline/reconnect cho nhóm và riêng.
- UI hai tài khoản: B ở trang chủ nhận toast/nút Xem và badge 1; bấm mở `/direct/2`, focus khung tin làm badge hết. A không nhận popup cho tin mình gửi. B ở tab không focus vẫn có popup dù URL là chat (đúng phạm vi điều kiện).
- Ảnh UI thật: `outputs/linhchat-thong-bao.png` (ignore). Người dùng xác nhận: “đã thấy thông báo tin nhắn mới”.
- Backup trước sửa: `work/backups/before-phase31-20261016-225704` trên VM. Chưa kiểm tra persistence notification sau tạo lại app ở thời điểm này; sẽ kiểm tra trong GĐ4.

## Đang làm — GĐ4

Người dùng yêu cầu lưu trí nhớ và tiếp tục GĐ4. Kế hoạch: sao lưu; kiểm tra Nginx HTTP/WebSocket/upload/headers/health; chuyển Compose bỏ phase3 để đóng published :5000; chạy HTTP/WebSocket thật và kiểm tra dữ liệu cũ sau recreate; kiểm tra UI; tạo commit mốc 1 sau khi đạt; cung cấp tối đa hai ảnh và đoạn báo cáo ngắn. Monitoring/logging chưa chạy, không nhận hoàn thành thay.

## Điểm cần nhớ

- Không xóa DB hoặc bí mật, không `down -v`. Migrations trước chỉ bổ sung schema. Tài khoản synthetic của công cụ dùng cho kiểm thử không phải tài khoản thật người dùng.
- Nhật ký cũ ở `outputs/KET_QUA_HIEN_TAI.md` và lộ trình có những câu trạng thái lịch sử đã lỗi thời; luôn lấy mục mới nhất có ngày/bằng chứng, không coi tất cả đoạn cũ là hiện trạng.
- Word báo cáo đã có nhiều hình, có trùng số Hình 7; số ảnh mới nên dùng Hình X. Chưa render/dàn trang bản Word.

## 16/10/2026 — GĐ4 hoàn thành kỹ thuật

- Đọc lại toàn bộ nội dung đề gốc, xác nhận mốc1 ứng dụng/Nginx, mốc2 monitoring, mốc3 logging; HTTPS tự ký hoặc headers cơ bản. Không sửa hai file Word.
- Backup trước chuyển: `work/backups/before-phase31-20261016-231002` trên VM. Không xóa volume hay tài khoản/tin cũ.
- Nginx chính thức1.30.6-alpine đã pull thành công, pin digest trong Compose. Non-root101, read-only/tmpfs, healthcheck qua app. `nginx -t` hợp lệ. Docker DNS/upstream resolve tự theo app sau recreate, Nginx không restart trong kiểm tra persistence.
- Chạy `compose.yml` không phase3: Nginx cổng80; app5000 và PostgreSQL5432 không published; pgAdmin127.0.0.1:5050. Public/Private, chat/ảnh/file/notification đi qua proxy. Chặn metrics/status ở web; status8081 nội bộ dành cho GĐ5.
- HTTP200 và4headers, WebSocket nhóm/riêng hai chiều và polling, kiểm tra quyền/nonce/seen/thông báo. File đúng10 MiB gửi/tải cùng SHA256;10 MiB+1 bị Flask413 và request body>11 MiB bị Nginx413. `NGINX4_LIVE_CHECK_OK`.
- Sau recreate app qua proxy: `NOTIFICATIONS_PERSISTENCE_OK`, `NGINX4_PERSISTENCE_OK`, `MESSAGES34B_PERSISTENCE_OK`; dữ liệu/file/receipt/unread cũ giữ nguyên, C không truy cập được. Một lượt test đăng nhập dồn bị429 đúng giới hạn; helper kiểm thử được sửa để đợi7s rồi thử lại, không nới rate limit. Đã chạy lại đạt.
- `NGINX4_RATE_LIMIT_OK`: POST/login vượt10r/m với burst5 bị429, GETform vẫn200. Access log không ghi query string/Referer/cookie/body. Đây không phải mã hóa HTTP; chỉ dùng lab/mạng tin cậy.
- Hoàn thiện delivered nhóm: mọi thành viên đang trên trang khác nhận full envelope qua personal socket, không dùng preview toast làm bằng chứng nhận đủ nội dung. Hai test mới xác minh đủ nội dung/không trùng/người ngoài không nhận. Bản cuối **142 passed in61.84s** trên VM; cú pháp JS đạt.
- Trình duyệt ở `http://192.168.203.131/direct/2` đăng nhập được, lịch sử/ảnh cũ còn, trạng thái Đã kết nối qua proxy, không lỗi console. Ảnh thật `outputs/linhchat-gd4-nginx.jpg` (ignore).
- Hướng dẫn chụp một ảnh Terminal và đoạn báo cáo ngắn ở `docs/GD4_NGINX_VA_BAO_CAO.md`; `scripts/check-phase4.sh` in kiểm tra gọn không bí mật.
- Mốc1: `feat: milestone 1 - LinhChat, PostgreSQL and Nginx`. Lấy hash từ Git thay vì ghi hash vào chính nội dung commit. Không commit.env/work/outputs/configchi tiết monitoring/logging chưa chạy; không push GitHub.
- **Tiếp theo: chờ người dùng xác nhận đã chụp GĐ4, rồi GĐ5 monitoring**. Chưa chạy Prometheus/Grafana/Loki/Promtail, chưa commit2/3. Trước nộp cần người dùng chốt repo GitHub và triển khai đủ các giai đoạn còn lại.

## 18/10/2026 — bắt đầu GĐ5

Người dùng xác nhận “đã chụp GĐ4”, cho phép chuyển phần tiếp theo theo lộ trình. Đọc đầy đủ trí nhớ và kiểm tra lại VM thật: bốn dịch vụ GĐ4 hoạt động, app/Nginx/PostgreSQL Healthy, commit339d542 ở cả hai nơi, source tracked không có thay đổi ngoài dự kiến. VM dùng Docker cgroupv2/systemd/overlayfs, còn19GiB disk và khoảng2.3GiB RAM available. Đang kiểm tra cấu hình monitoring/phiên bản tương thích trước triển khai; chưa gọi hoàn thành hoặc tạo commit2. Logging không được bật trong giai đoạn này.

## 18/10/2026 — monitoring chạy đạt qua API, đang hoàn tất UI/commit

- Backup trước GĐ5: `work/backups/before-phase31-20261018-005629` trên VM. Đọc nguồn chính thức, tải và ghim digest image có thật: Prometheus3.14.0, Grafana13.2.2, cAdvisor0.60.6, PostgreSQL exporter0.20.1, Nginx exporter1.5.3. Không thay phiên bản app/DB/Nginx nền.
- Profile monitoring đã chạy, tổng9service. 5/5target UP, exporter pg_up/nginx_up =1. Kiểm tra role postgres_exporter có pg_monitor, khôngsuperuser/createDB/createRole.
- cAdvisor tương thích Docker/cgroupv2; chỉ nhãn project/service/oneoff, Prometheus lọc projectde32-chat, bỏ one-off rồi chuẩn hóa nhãnservice. CPU/RAM đủ9service qua query. Giữ bindlocalhost3000/9090; exporter/cAdvisor không published, app5000/DB5432 vẫn nội bộ. Quyền privileged/host mounts là ngoại lệ phải trình bày ở hardening.
- Dashboard LinhChat Overview UIDlinhchat-overview, folderLinhChat,11panel; datasource Prometheus UIDprometheus. Loki datasource chưa được đưa vào provisioning vì logging chưa chạy. Mọi panel đã query được dữ liệu hữu hạn cả bằng Prometheus API và Grafana datasource API.
- Bổ sung gauge số Socket.IO/online user từ state có khóa, không nhãn riêng tư. Test xác minh nhiều tab một tài khoản khác số người online. **143passed in70.67s** trên VM.
- `MONITORING_ACTIVITY_OK`: hai clientWebSocket thật, gửi6tin gồm2tệp nhỏ, receipt/HTTP/upload bytes, quan sát counter tăng trong Prometheus và socketgauge>=2 trong lúc kết nối. Chỉ tài khoản synthetic A/B cũ, không lấy dữ liệu cá nhân làm demo.
- `MONITORING_PERSISTENCE_OK`: sau force-recreate riêng Prometheus/Grafana, mẫu HTTP tại timestamp cũ còn nguyên, dashboard/datasource/query11panel còn. `MESSAGES34B_PERSISTENCE_OK`: dữ liệu app/file/receipt cũ và quyền vẫn đúng.
- Thông tin đăng nhập Grafana ghi riêng `work/grafana-access.txt` mode600 trên VM (không có trong trí nhớ/Git/ảnh). Có bản riêng trong work Windows để công cụ kiểm thử đăng nhập, không in giá trị. Đường hầm công cụ13000→VM3000,19090→9090; không dùng các cổng tạm này trong hướng dẫn chụp Ubuntu.
- Hướng dẫn dự kiến2ảnh, đăng nhập cụ thể và đoạn báo cáo ngắn ở `docs/GD5_MONITORING_VA_BAO_CAO.md`. Đang kiểm tra giao diện trước commit2; chưa thông báo người dùng GĐ5 hoàn thành, chưa chuyểnGĐ6.

## 18/10/2026 — GĐ5 hoàn thành kỹ thuật

- Giao diện thật qua SSH tunnel: Targets đủ5nhóm1/1up; LinhChat Overview hiển thị11panel, không lỗi console, datasource/query có dữ liệu. Làm mới15s thực sự được chọn trong UI sau bổ sung danh sách refresh_intervals. Ảnh minh chứng công cụ trong `outputs/linhchat-gd5-targets.jpg` và `outputs/linhchat-gd5-grafana.jpg`, không chứa đăng nhập; chưa phải ảnh người dùng đã chụp trong VM.
- Sau force-recreate, cAdvisor/Prometheus còn instance cũ trong cửa sổ lookback. Đã sửa CPU/RAM để chỉ lấy instance mới nhất mỗi service với last_seen trong60giây; loại cộng trùng RAM. Kiểm tra9service và API11panel đạt lại, so sánh truy vấn dashboardAPI với JSON nguồn để tránh dùng cấu hình cũ. Phạm vi mỗi service một container.
- Grafana giới hạn768m, GOMEMLIMIT512MiB sau quan sát cache tiến gần512m; Prometheus512m. Healthcheck readiness thật cho cả hai, Grafana đợi Prometheus healthy. Không OOM/restart bất thường khi kiểm tra cuối. Không thay giới hạn bảo mật/rate limit app để chạy test.
- Đã hoàn tất hướng dẫn2ảnh, chú thích và đoạn báo cáo ngắn; README/lộ trình/guide/memory/checklist được cập nhật cùng mốc2. Thông điệp commit2 `feat: milestone 2 - Prometheus and Grafana monitoring`; lấy hash từ Git, không ghi hash tự tham chiếu. Không stage loki/promtail hoặc secret, không push.
- Cấu hình runtime và source app đã đối chiếu SHA256 giống nhau; không rebuild app chỉ để cập nhật tài liệu, giữ counter đang có. Kiểm tra cuối bằng `bash scripts/check-phase5.sh` và persistence TSDB. Source/Git mốc2 được đồng bộ sang VM, không reset/xóa dữ liệu.
- **Tiếp theo chờ người dùng xác nhận đã chụp GĐ5**, mới GĐ6 Loki/Promtail/baLogQL/commit3. Không bật logging trong phiên này. Báo cáo10–15trang, không thêm ảnh kiểm thử nếu đã có hai ảnh monitoring.

## 19/10/2026 — đang triển khai GĐ6

- Người dùng xác nhận đã chụp GĐ5 và tiếp tục code tại chat này. Source cũ truy cập được; không sửa sources của thư mục đồng bộ ChatGPT. Đọc lại đầy đủ memory/lộ trình; SSH đúng VM, commitf02f3ae,9service đang hoạt động. VM còn16GiB disk và1.2GiB RAMavailable.
- Backup trước GĐ6 `work/backups/before-phase31-20261019-142649`. Ghim digest image registry chính thức Loki3.6.18 và Promtail3.6.7. PromtailEOL02/03/2026, chỉ giữ cho bài lab theo stack chốt, không coi production maintained.
- Đã viết log JSON allowlist cho app; unknown message/exception không in nội dung. Nginx access dùng họ route cố định, không query/IP/UA/body; Gunicorn access bỏURL/query. Promtail chỉ app/nginx trong project, bỏone-off và log cũ hơn1h khi replay; volume positions riêng, không mount thư mục engine. Socket Docker ro vẫn là quyền mạnh, chưa hoàn tất auditGĐ7.
- Đã triển khai Loki/Promtail và datasource Grafana trên VM. Phát hiện selectorPromtail không nhận rawbacktick ở parseragent, đã sửa sang quoted selector và runtime bắt đầu nhận target. Cold replay log cũ gây400 out-of-order, đang lọc lịch sửlab để không gây lỗi batch. Chưa kết luận hoàn thành; đang kiểm tra3LogQL/canary/persistence và hồi quy. Chưa commit3.

## 19/10/2026 — GĐ6 hoàn thành kỹ thuật

- Bản cuối **146passed in82.16s** trên Ubuntu container (3testlogging mới). Lượt đầu144pass/2fail do test dựngLogRecord thiếulevelno, đã sửa dữ liệu test và chạy lại toàn bộ đạt; không bỏ test hoặc nới bảo mật. App đang chạy có formatterJSON mới; Gunicornaccess không URL/query.
- LOGGING_ACTIVITY_OK: tài khoản synthetic cũ gửi thật tin nhóm/riêng và2tệp, receiptseen, C bị404 lịch sử không có quyền. Query3LogQL qua Loki và Grafana datasourceAPI có dữ liệu. Canary nội dung/tênfile/path/query/UA và các secret.env không xuất hiện trong mẫu, không in giá trị.
- LOGGING_BOUNDARIES_OK: hai fixture độc lập (oneoffTrue cùngproject, serviceapp projectkhác) không vào Loki sau hơn2chu kỳdiscovery; tự kết thúc/xóa, không phải log gửi tin thật dùng trong báo cáo. Chỉ đọcSocket Docker, không mountenginefolder. Không sửa Dockerdaemon để tương thích.
- LOGGING_PERSISTENCE_OK sau force-recreate riêng Loki/Promtail: log snapshot cũ còn và kết quả không lặp; PROMTAIL_POSITIONS_OK volume có dữ liệu. Đây không là đảm bảo exactly-once hoặc đủ log khi agent ngừng lâu. Drop replay>1h được ghi rõ trongguide. MESSAGES34B_PERSISTENCE_OK giữ dữ liệu/tệp/receipt/quyền sau cập nhậtapp/Nginx.
- Loki có thể thêm metadata service_name/detected_level; checker cho phép các fieldbounded này, không ID/người dùng làm streamlabel. Mẫu log chỉ curatedaudit app/Nginx; unknownappmessage/exception được thay bằng tên event chung, không đầy đủ stacktrace. Nginxroutecốđịnh vàDockerlogrotation10MB×3 đã áp dụng bằng recreate app/Nginx.
- Prometheus5/5UP, Grafana11/11panel có dữ liệu, CPU/RAM11service. Các containerkhôngOOM/restartbấtthường sau cấu hình cuối; RAMavailable1.3GiB, Loki~82MiB/512m, Promtail~44MiB/128m. Loki empty-ring transient lúc coldstart đã hết;60slogcuối không lỗi.
- Trình duyệt thật qua tunnel13000: Explore chọnLoki, Code/Runquery, thấychat/upload vàWARN404; không lỗi/warnconsole. Monaco cầnCtrl+A trước thayquery vàđợieditorcậpnhậttrướcRun. Ảnh công cụ `outputs/linhchat-gd6-chat-logs.jpg`, `outputs/linhchat-gd6-rejected-logs.jpg`, chưa phải ảnh người dùng đã chụp. Guide `docs/GD6_LOGGING_VA_BAO_CAO.md` một ảnh chính/một tùy chọn, đủ3LogQL và đoạn báo cáo ngắn.
- Mốc3 `feat: milestone 3 - Loki and Promtail centralized logging`, source/Git đồng bộ Windows/VM sau kiểm tra; không.env/work/outputs/secret, khôngpushGitHub. Hash lấyGitkhôngtựthamchiếu. Người dùng chưa chụpGĐ6; **chờ xác nhận trướcGĐ7**. GĐ7audit/GĐ8bàn giao còn, chưa sửaWord.

## 19/10/2026 — đang kiểm tra GĐ7

- Người dùng gửi ảnhExplore đủ4dòng log chat/upload, đã được xác nhận dùng được cho báo cáo, sau đó yêu cầu tiếp tụcGĐ7. Đọc lại toàn bộmemory vàlộtrình; VM11service đang chạy, trackedGit sạch, ba mốc339d542/f02f3ae/0406b63 giữ nguyên.
- Audit thực tế: appUID10001/NginxUID101,ro/capdropALL/NoNewPrivs/seccompđúng; chỉNginxpublic80, adminlocalhost; backendinternal, DBkhôngpublished. Rolechatuser/exporter khôngsuper/createDB/createRole/replication/bypassRLS; exporterpg_monitor/khôngghi messages, appkhôngđọcpg_authid. Hash hợp lệ, .env600/work700, secretskhôngmặcđịnh/khôngtrùng vàkhôngtrongGit3commit. Không inhash hoặcgiátrịsecret.
- Testmới tái hiện logoutHTTP không đóngsocketcũ (1fail/5pass trước sửa). Đãbackup `work/backups/before-phase31-20261019-150109`; sửa logout tăngauth_version atomically vàdisconnect_user, thu hồi mọiHTTP/cookie/socket của chính tài khoản; khôngảnhhưởnguserkhác. NútThoát/menu cótitlegiải thíchđăngxuấtmọiphiên. Không đổi mật khẩu/schema hoặc xóa dữ liệu. Đang chạy fullsuite/live trước kết luận.
- Thêm audit/script ảnhGĐ7; phân biệt kiểm tra hạ tầng đọc trực tiếp vàliveHTTP/WebSocket cần lưu kết quả lầnchạy. Chưa hoàn thành GĐ7; không coiHTTPheaderslàTLS. cAdvisorprivileged/PromtailDockerAPI vàPromtailEOL vẫn làngoạilệ.

## 19/10/2026 — GĐ7 hoàn thành kỹ thuật

- **152 passed in61.13s** trên VM, gồm6test hardening mới. HARDENING_LIVE_OK:4header trên200/404,cookieHttpOnly/SameSiteLax,trangprivate no-store; thiếu/saiCSRF400khôngđổi trạngthái; cookie sửa bị từchối; Originngoài400; Ckhôngđọc history/file; filethườngattachment/octet-stream/nosniff. Logoutthu hồi haiSocketA/cookiecũ/HTTPphiênAkhác, userBvẫnHTTP200/socketconnected.
- Phát hiện headernosniff bịtrùng Flask+Nginx. Đãbackup riêngNginx, thêmproxy_hide_header4header trướcđặtbảnchuẩn. Reloadlúcđầu chưađổi vìbindmountgiữinodecũ; SHA256host/containerkhác. Recreate riêngNginx sau nginx-t, kiểmtralạiđạt; auditor bổsung sohashsourceApp/Nginxđểkhôngnhầmfileđãviếtvớifileđangchạy. Không sửaDB/schema/mật khẩu.
- HARDENING_INFRA_OK xácminhUID/rootfsro/capdropALL/CapEff0/NoNewPrivs1/seccomp2/tmpfsro, cổng/mạng/roleDB/hash/secret/Gitlịchsử. Kiểm traHTTPheaderhiệntạiđủmộtgiátrịmỗiloạivàmetrics/status404. Secretđượcđọcchỉđểsosánh trongbộnhớ, khôngđưavàoargv/output.
- NGINX4_RATE_LIMIT_OK:POSTdồn429/GET200; helperloginđợi7s khiDockerreuseIPtest, khôngnớiratelimit. MESSAGES34B_PERSISTENCE_OK xácnhậntin/file/receipt/quyềncũcòn. Monitoring5/5UP/11panel/11service và3LogQLquaGrafanavẫnđạt.
- `work/hardening-live.json` chỉboolean/time/appimage/Nginxhash; scriptảnhkiểmtrahạtầng/headertrựctiếp vàđốichiếukếtquảliveđãlưuđúngimage/config. Không giả định lầnchụpmớichạylạilogout/rate-limit. HướngdẫnmộtảnhTerminalvàđoạnbáocáoở `docs/GD7_HARDENING_VA_BAO_CAO.md`.
- Ba mốc339d542/f02f3ae/0406b63giữnguyên; fixGĐ7lưucommitriêng, khôngamend/rebase/push. Scriptscheckphase4/5/6lọccommitmilestoneđểkhôngbỏmốccũkhicófixsauđó. README/lộtrình/requirements/checklist/memoryđãcậpnhật.
- **Chờ người dùng chụp GĐ7 trước GĐ8**. HTTPchưaTLS/Securecookie; ngoại lệcAdvisorprivileged/PromtailDockerAPI/EOL vàroleappownerschema đượcghi rõ. KhôngquétmọiCVE/pentest/productionsecure; khôngtựnângcấpmọiimage hoặcđổifirewall. Chưa sửaWord/chuẩnhóasốhình/repoGitHub.

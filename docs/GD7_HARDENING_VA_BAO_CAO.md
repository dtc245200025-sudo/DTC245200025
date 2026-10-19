# Giai đoạn7 — Hardening và minh chứng ngắn

## Đã kiểm tra trên Ubuntu VMware

152/152test đạt trong container; HARDENING_INFRA_OK và HARDENING_LIVE_OK đạt qua Docker/PostgreSQL/HTTP/WebSocket thật. Có backup trước sửa, không xóa volume/schema/tin/tệp. GĐ6 đã có ảnh người dùng gửi và được xác nhận hợp lệ.

| Hạng mục | Kết quả xác minh |
|---|---|
| Quyền app/Nginx | UID10001/101, rootfsread-only, cap_dropALL, CapEff0, NoNewPrivs1, seccomp2, tmpfsnoexec/nosuid; source trong container khớpSHA256 với sourceVM |
| Network | Backendinternal, PostgreSQL chỉ trên backend; Nginx/Grafana không vào mạngDB. ChỉNginxpublish80 ra mạng trong phạm vi container; pgAdmin5050/Grafana3000/Prometheus9090 bind127.0.0.1; app/DB/Loki/Promtail/exporters khôngpublish |
| Database | chatuser vàpostgres_exporter khôngsuperuser/createDB/createRole/replication/bypassRLS. Exporter cópg_monitor nhưngkhôngghi bảngmessages; appkhôngđọcpg_authid. Chỉ kiểm tra booleanhash, không inhash hoặc tài khoản người dùng |
| Secret/Git | .env600,work700,secretkhôngmặcđịnh/khôngtrùng; quét giá trịsecret hiện tại và privatepaths trong mọi commit, không insecret |
| HTTP | Bốnsecurityheader trên200/404; file thườngattachment/octet-stream/nosniff, không cònheadernosnifftrùng; trang cá nhânno-store; cookieHttpOnly/SameSiteLax |
| Session/CSRF | POSTthiếu/saiCSRF bị400; cookie bị sửa bịtừchối; Socket.IOOriginngoàibị400; logoutthu hồi mọiHTTP/cookie/socketcũ của chính tài khoản; userkhác không bịảnhhưởng |
| Quyền vàrate-limit | C khôngđọc history/file nhóm/riêng; POSTlogin dồn bị429 trong khiGETformvẫn200. Testtôntrọngrate-limit, khôngnớibảo vệ |

Sau sửa, MESSAGES34B_PERSISTENCE_OK xác nhận tin/tệp/receipt/quyền cũ còn; monitoring5/5UP,11panel,CPU/RAM11service và3LogQL vẫn đạt.

## Chụp đúng một ảnh

Trong Terminal **Ubuntu**:

```bash
cd ~/projects/de32-chat
clear
bash scripts/check-phase7.sh
```

Phóng to cửa sổ hoặc giảm cỡ chữ Terminal một nấc nếu thiếu chỗ. Chụp **từ dòng GIAI DOAN7-HARDENING LINHCHAT đến GIAI_DOAN_7_OK**, gồm UID/read-only/quyền, mạng, roleDB,secret, cácHTTPheader và dòngLIMIT. Không cần mở.env hoặcchụpthêm pgAdmin.

Script kiểm tra hạ tầng trực tiếp mỗi lần chạy. DòngEVIDENCE là kết quảliveHTTP/WebSocket đã lưu, được đối chiếuimageapp đang chạy; **không nói script vừa thử lại các thao tác đăng xuất**. Nếuimageapp đổi thìscript báo phải chạy lạiliveaudit. Script chỉ đọc, không làm bạn đăng xuất.

**Hình X. Kiểm tra hardening container, mạng, quyền PostgreSQL và security headers trên Ubuntu VMware.**

## Đoạn ngắn cho báo cáo

Hệ thống được hardening bằng Docker Compose: Flask/Nginx chạy non-root, filesystem chỉ đọc, loại bỏ capabilities và bật no-new-privileges. PostgreSQL được đặt trong mạng nội bộ với role ứng dụng/giám sát hạn chế; secret nằm ngoài Git và file.env chỉ chủ sở hữu được đọc. Nginx bổ sung security headers, giới hạn đăng nhập; Flask kiểm tra CSRF và thu hồi phiên khi đăng xuất. Các kiểm thử Docker, SQL, HTTP và WebSocket xác nhận cấu hình hoạt động thực tế.

## Hai điểm đã sửa trong GĐ7

1. LogoutHTTP trước đây chỉ xóacookie ởtrìnhduyệt hiện tại, Socket.IO cũ vẫn dùngđược. Bản mới tăngauth_version atomically vàngắtSocketcủacùngtài khoản. Đây là **đăng xuất mọi phiên của tài khoản đó**, nútThoát/menu cótooltipgiải thích. Không đổi mật khẩu, không đăng xuất tài khoảnkhác. Tài khoản đãđăngxuất cóthể đăng nhập lại bìnhthường.
2. Flask vàNginx cùngthêmnosniff làmheadertrùng. Nginxẩn4upstreamsecurityheader rồi đặtbảnchuẩncủaproxy, appnộibộ vẫn giữheadercủanó. Kiểm traSHApháthiệnbindmountNginx còninodecũ sau truyềnfile; đãrecreate riêngNginx để nhậnđúngsource, khôngxóaDB.

## Giới hạn phải ghi rõ

- Bài lab chọn **securityheaders** theo phương án đềcho phép; **chưaTLS/HTTPS, cookieSecurechưabật**. Khôngdùngtàikhoản/mật khẩuquan trọng quaHTTP hoặc coiheader là mãhóađườngtruyền.
- cAdvisorprivileged vàPromtailroot/DockerAPI làngoạilệquyềnmạnh. Read-onlysocketmountkhôngngănđượcmọiDockerAPIwrite. NgườiởnhómDocker hoặcquảntrịhost vẫn cóquyềnmạnh; khôngthểdùng.env600chống lạiroot.
- Backendinternal vàkhôngpublishDB khôngtươngđươngzero-trust: app/exporter/pgAdmin đượcphéptruycậpDB theo topology. Mạngobservability là mạngchung; nếu một collector bịchiếm quyền, rủi ro vẫn tồn tại.
- Rolechatuser làownerbảng/schemađểappchạy migration; đây khôngphảirole chỉDMLtối thiểu của production. pg_monitor cóquyềnxem thốngkê/cấuhìnhđượccấp, khôngcoi là khôngđọcđượcbấtcứthôngtinnào.
- Giới hạnđăngnhập ởNginx theosourceIP, cóthểảnhhưởngnhiềungười chungNAT; khôngcókhóa tàikhoản/chốngphântánhoặcrate-limit toànbộWebSocket.
- Đây là auditcấuhìnhvàhồiquy tronglab, khônglàpentest/chứngnhậnan toàn/quétmọiCVE. Chưanângcấptoànbộimage/cácgóiphụthuộc, chưaCSP/TrustedHosts/2FA/SMTP/antivirusupload/E2EE/HA; PromtailEOLđãghiởGĐ6.

Ba commitmốc1–3 giữnguyên; bảnfixGĐ7 lưucommitsửa riêng, khôngamend/rebase/xóalịchsử. Chưa pushGitHub. Saukhi bạnchụpGĐ7, tiếpGĐ8 README/demo/kiểmtraguide/báocáocuối vàchốt repođích.

Nguồn: [Docker socket](https://docs.docker.com/engine/security/protect-access/), [PostgreSQL predefined roles](https://www.postgresql.org/docs/16/predefined-roles.html), [Flask security](https://flask.palletsprojects.com/en/stable/web-security/).

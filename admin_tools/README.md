# MelodyAI License Admin

Chạy tại thư mục gốc dự án:

```sh
.venv/bin/python -m admin_tools.active
```

Windows: `.\.venv\Scripts\python.exe -m admin_tools.active`.
Cũng hỗ trợ `python admin_tools/active.py`.

1. Nhấn **Generate Key Pair** khi chưa có key.
2. Private nằm tại `admin_tools/private/license_private.pem`.
3. Public nằm tại `admin_tools/public/license_public.pem`.
4. Copy **chỉ public PEM** vào `app/assets/keys/license_public.pem` trước khi
   chạy/phân phối desktop. Không tự tạo trust key khi desktop khởi động.
5. Nhập Machine ID đã copy từ desktop, chọn plan, expiry, features.
6. Generate License rồi Copy License để chuyển cho người dùng.

Không ghi đè keypair đang tồn tại. Giữ bản sao private key ở nơi riêng dành cho
Admin; không phân phối thư mục admin_tools cùng desktop. Private PEM không được
mã hóa bằng passphrase trong phiên bản này; file mới có quyền 0600 trên POSIX,
Windows dùng ACL của thư mục tài khoản Admin. Không đưa private key lên Git.
Nếu một trong hai file key bị thiếu, khôi phục từ backup thay vì tạo đè.

Ed25519 ký `MLAI1.` + bytes JSON. Token gồm
`MLAI1.base64url(payload).base64url(signature)`.
Payload: license_id (UUID), machine_id, plan, issued_at, expires_at, features.
Ngày hết hạn trong GUI tính đến 23:59:59 UTC. LIFETIME luôn expires_at=null.
Features: music, lyric, audio, image, offline. Plan không tự gán features;
checkbox quyết định các quyền được ký.

Tests tạo key tạm trong thư mục hệ thống rồi xóa, không sử dụng key thật.

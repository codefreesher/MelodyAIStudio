# MelodyAI — AI Music & Creative Studio

Desktop Python 3.12+ / PySide6 Widgets với Pink Theme, SQLite, mock creative
providers, license Ed25519 và pipeline đóng gói. Không có website Admin hoặc
kết nối MySQL. AI generation hiện là **demo cục bộ**, không gọi API trả phí.

## Chạy ứng dụng

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.main
```

Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m app.main
```

Tại Startup chọn **Đăng nhập**: `demo@melodyai.local` (hoặc `demo`) / `123456`.
Đăng nhập hoặc kích hoạt thành công mở Dashboard + Sidebar. Demo auth là công cụ
phát triển, không phải xác thực production. Remember lưu định danh để điền lại
form; không lưu mật khẩu và không tự coi file session là bằng chứng xác thực.

`--showcase` mở trang kiểm tra reusable components. `--smoke-test` mở rồi đóng
cửa sổ để xác minh bootstrap. Không dùng `--showcase` để bỏ qua authentication
trong bản phát hành production.

## Các stage đã triển khai

| Stage | Nội dung |
| --- | --- |
| 01–06 | Bootstrap, theme, reusable widgets, Startup/Login/Activation, admin license tool |
| 07 | Workspace QStackedWidget, Sidebar, profile, navigation sau authentication |
| 08 | Dashboard, 4 feature card, tìm lịch sử, tối đa 4 dự án gần đây |
| 09 | Music demo WAV, các tab/options, artwork, waveform, player, cancel/save/export |
| 10 | Lyric demo 1–3 bản, editor sửa được, copy/save/export |
| 11 | Audio demo WAV/MP3, player/seek/volume, nhập TXT; MP3 cần FFmpeg |
| 12 | Image demo PNG 1/2/4 ảnh, tỉ lệ khung hình, gallery/preview/export |
| 13 | SQLite history, loại/search/sort/pagination, open/play/export/delete |
| 14 | Online config, API key qua vault, metadata trong SQLite, kiểm tra HTTP |
| 15 | Local config, Ollama list/pull/delete, start/stop tiến trình do app tạo |
| 16 | Catalog, import manifest, download SHA256, ZIP staged install/repair/remove |
| 17 | Pink Light/Dark/System, accent, đường dẫn, common-control vi/en, maintenance |
| 18 | GitHub stable release check, download SHA256, confirm installer, auto-check |
| 19 | PyInstaller + Inno scripts, manifest, draft release command, Windows CI |
| 20 | Unit/service/UI QA, formatting/lint, native Linux bundle smoke test |

**Giới hạn hiện tại:** chưa có GitHub repository và chưa chạy build/installer trên
Windows. Pipeline Windows đã chuẩn bị; bundle đã build tại đây là **Linux**.
Xem [QA.md](QA.md) để biết chính xác những gì đã và chưa xác minh.

## Creative demo

Mỗi tác vụ chạy trên worker, tạo tệp dưới thư mục Projects. Nhấn **Lưu lịch sử**
để tạo bản ghi SQLite và mục dự án gần đây. Generate không tự gọi API Online,
kể cả khi đã điền API key. Các lựa chọn provider/genre/voice/style được lưu cùng
metadata để chuẩn bị tích hợp thật; không phải tất cả lựa chọn làm thay đổi demo.

- Music: giai điệu tone tổng hợp, có thể kèm file lyric mẫu.
- Lyric: template minh họa, có nhiều bản chỉnh sửa được.
- Audio/TTS: **giai điệu demo, không phải giọng nói tổng hợp**.
- Image: ảnh gradient mẫu, không phân tích prompt hay ảnh tham khảo.
- MP3: dùng executable `ffmpeg` trong PATH; nếu thiếu, báo lỗi và có thể chọn WAV.
- Xóa history chỉ xóa bản ghi/project, giữ tệp kết quả. Export có thể ghi đè tệp
  cùng tên trong thư mục xuất do người dùng chọn.

## License và Admin

```sh
.venv/bin/python -m admin_tools.active
```

Admin tạo `admin_tools/private/license_private.pem` và
`admin_tools/public/license_public.pem`. Copy **chỉ public PEM** vào
`app/assets/keys/license_public.pem` trước khi phát hành bản có activation.
Không tạo sẵn private key thật trong repo. Desktop không import admin_tools.

License Ed25519 gồm ID, Machine ID hash, plan, issued_at, expires_at, features.
LicenseManager xác minh trước khi lưu và mỗi lần load; generation qua license
kiểm tra lại hạn/features. LIFETIME vẫn kiểm tra chữ ký và Machine ID.
Không có online revocation hoặc chống chỉnh đồng hồ offline.
Chi tiết: [admin_tools/README.md](admin_tools/README.md).

## Cấu hình AI và bảo mật

Online config lưu metadata qua repository và API key qua CredentialVault.
Windows dùng WinVaultKeyring; môi trường không hỗ trợ dùng Fernet với key file
cục bộ quyền 0600 trên POSIX. Fallback bảo vệ khỏi plaintext, **không** chống được
người đã đọc toàn bộ tài khoản/thư mục dữ liệu. Không log API key hoặc password.

Test Online chỉ kiểm tra máy chủ HTTPS phản hồi HTTP, **chưa xác thực key/model**
và không gửi credential tới URL tùy chỉnh. Google login vẫn là placeholder.

Offline URL chỉ chấp nhận localhost. Ollama dùng `/api/tags`, `/api/pull`,
`/api/delete`. Nhập đường dẫn executable trước khi Start. Stop chỉ tác động
process MelodyAI đã khởi động; không kill dịch vụ bên ngoài. Stable Diffusion
cần API tương thích AUTOMATIC1111; TTS Local kiểm tra endpoint do người dùng cấu
hình, chưa có inference adapter. Pull cancel ngừng theo dõi stream; engine có
thể vẫn hoàn tất lớp model đang tải. Models folder là cấu hình chuẩn bị cho engine.

## Tài nguyên

Không hardcode checksum đoán hoặc URL tải chưa được kiểm duyệt. Catalog ban đầu
hiển thị Ollama/FFmpeg/Python/Stable Diffusion/TTS; để tải/cài, nhập manifest JSON
đã kiểm duyệt. Xem [docs/resource-manifest.example.json](docs/resource-manifest.example.json).

Manifest gồm id/name/description/version/url/sha256/archive_type/executable.
Hiện hỗ trợ **ZIP portable**, không tự chạy vendor EXE/MSI. Download yêu cầu HTTPS
và SHA256. ZIP traversal/symlink và archive vượt giới hạn bị chặn. Cài vào staging,
kiểm tra executable rồi mới thay thư mục đích; rollback nếu rename thất bại.
Không tự tải model lớn hoặc chạy binary khi chỉ mở page.

## Settings và dữ liệu

Dữ liệu nằm trong `platformdirs` user data (`%LOCALAPPDATA%/MelodyAI` trên Windows),
không ghi vào Program Files. SQLite: `data/melody.db`; cấu hình: `config/`;
log xoay vòng: `logs/app.log`; license: `config/license.token`.

Projects/Downloads paths áp dụng cho tác vụ mới, không tự di chuyển tệp cũ.
Cache cleanup chỉ xóa thư mục con `MelodyAI-cache` do app quản lý, không xóa cả
thư mục người dùng chọn. Model path được lưu cho bước tích hợp local engine.
Start with Windows yêu cầu bản EXE Windows. Đổi theme/accent áp dụng ngay.
English hiện dịch navigation và các control chính; một số thông báo/hướng dẫn
và nội dung demo vẫn bằng tiếng Việt.

## GitHub update

Chưa cấu hình repo mặc định. Điền owner/repository trong trang Cập nhật khi có
repo public. App đọc stable latest release và tìm đúng asset:
`MelodyAI-Setup-{VERSION}.exe`, có trường GitHub `digest=sha256:...`.
Không có SHA256 thì không cho tải/cài. Recheck digest ngay trước khi chạy installer.
Auto-update hiện là **tự kiểm tra**, không âm thầm cài. Chỉ Windows chạy installer;
người dùng xác nhận trước, app không force-kill tác vụ đang chạy.

API tham chiếu: [GitHub Releases](https://docs.github.com/en/rest/releases/releases),
[Ollama list models](https://docs.ollama.com/api/tags),
[Ollama pull](https://docs.ollama.com/api/pull).

## Build và installer

Trên Windows Python 3.12+:

```powershell
python -m pip install -r requirements-dev.txt
python scripts/build.py
python scripts/package.py --iscc "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

Đầu ra: `dist/MelodyAI/MelodyAI.exe` và
`dist/installer/MelodyAI-Setup-0.1.0.exe` (version thực đọc từ VERSION).
Thêm `--require-public-key` khi build bản phân phối có license đã cấu hình.
`--dry-run` cho build/package để xem command mà không chạy.

Inno dùng per-user installation, AppId ổn định, Restart Manager, không xóa user data.
Chưa có Authenticode signing. Script release mặc định chỉ in lệnh draft, không
publish. `scripts/create_release.py --execute` mới gọi gh để tạo draft.
`.github/workflows/windows-build.yml` sẵn sàng khi có GitHub repo, không tự publish.
PyInstaller tạo bundle cho OS đang chạy: [tài liệu chính thức](https://pyinstaller.org/en/stable/operating-mode.html).

## QA

```sh
.venv/bin/python -m ruff check app scripts admin_tools tests
.venv/bin/python -m compileall -q app admin_tools scripts tests
QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME=generic \
  .venv/bin/python -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME=generic \
  .venv/bin/python scripts/qa_workspace.py
```

Workspace QA sử dụng Qt Multimedia, cần truy cập backend âm thanh hệ thống;
chạy ngoài sandbox chặn audio socket. Tests dùng tệp/keypair tạm, không dùng
private key thật, API trả phí hoặc GitHub release thật.

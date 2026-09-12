# MelodyAI QA — Stage 07–20

Kiểm tra trong Linux, Python 3.14, PySide6 6.11.2; ứng dụng yêu cầu Python 3.12+.
Dữ liệu QA, license keypair và nội dung demo được tạo trong thư mục tạm.
Không tạo Git repo, không publish release, không gọi AI trả phí.

## Kết quả

| Kiểm tra | Kết quả |
| --- | --- |
| Ruff lint và format | PASS |
| compileall app/admin/scripts/tests | PASS |
| pip check | PASS |
| 29 unit/service/UI tests | PASS |
| scripts/qa_workspace.py | PASS |
| Native PyInstaller bundle Linux | Build và smoke test PASS |
| FFmpeg WAV → MP3 | PASS với FFmpeg cục bộ |
| Build/package dry-run | PASS |
| Windows EXE + Inno installer | Chưa chạy trên Windows |
| GitHub update thật | Chưa có owner/repository; test bằng fixture |

Unit/service/UI tests bao gồm:

- Startup signals, keyboard/disabled, resize và SVG artwork.
- Login empty/wrong/success, remember/clear, show password, Back.
- License machine mismatch, signature, expired, valid, lifetime, saved token,
  không ghi đè keypair, admin GUI → desktop activation bằng key tạm.
- Button loading state, navigation exclusivity, dialogs, toast timer,
  overlay resize, gallery preview, QSS parser và palette.
- WAV/TXT/PNG output, multi-file export, idempotent history save, filters,
  SQL parameterization, cancel, feature authorization hook.
- Credential plaintext không xuất hiện trong DB hoặc ciphertext fallback.
- HTTPS download digest/cancel, không ghi đè tệp cũ khi lỗi,
  chặn ZIP traversal, staged install và scoped remove.
- Semver release selection, không chấp nhận prerelease/thiếu checksum,
  không chạy installer có checksum sai.

Workspace QA đi qua login thật bằng MockAuthProvider → Dashboard → cả bốn tool
→ generate → sửa lyric → save → lọc/sort history → tất cả route cấu hình → đổi
ngôn ngữ control/theme → resize 1100×650, 1366×768, 1920×1080 → logout.
Player dùng Qt Multimedia: cần audio socket được phép truy cập; không xác nhận
chất lượng âm thanh bằng nghe trực tiếp. Sidebar có vùng menu cuộn riêng.

## Kiến trúc và refactor

- UI không import provider, query SQLite hoặc gọi HTTP.
- Generation, provider configuration, download/install/update và export dài chạy
  bằng QRunnable/QThreadPool; worker giữ signal result/error/finished.
- Shared generation form/controller/service tránh copy logic giữa bốn tool.
- SQLite connections đóng sau từng transaction, metadata/path thay cho binary.
- Lưu file generation, export và checksum installer không chạy trên UI thread.
- Window không đóng khi worker chưa kết thúc; media được giải phóng khi logout/close.
- Style tập trung QSS/tokens, theme dark/system/accent dùng cùng ThemeManager.
- Desktop không import admin_tools/private-key primitives; build loại admin/tests.
- Build scan chặn private key trong desktop asset tree; không có key thật trong repo.

## Những phần chưa thể nghiệm thu đầy đủ

1. Chưa build/run EXE hoặc cài/gỡ/update Inno trên máy Windows. Có workflow
   `windows-build.yml`; native Linux bundle không chứng minh tương thích Windows.
2. Chưa có repository nên chưa thử release thật, rate-limit hay download GitHub
   qua mạng thật. SHA256 dựa vào digest từ GitHub; chưa có Authenticode signing.
3. Resource catalog cần manifest ZIP portable URL/checksum đã duyệt. Không có
   catalog tải vendor EXE/MSI hoặc model lớn mặc định, không tự chạy installer vendor.
4. Không có local engine/Ollama server trong môi trường QA; endpoints đã triển khai
   nhưng chưa thử pull model thực. TTS/SD inference vẫn dùng creative mocks.
5. English dịch control/navigation chính; một số thông báo/hướng dẫn vẫn tiếng Việt.
6. Online Test là HTTP connectivity probe, chưa xác thực API key/model. Credentials
   trên Windows chưa chạy thử WinVault thực; đã thử encrypted fallback trên Linux.
7. SQLite schema v1 hỗ trợ khởi tạo lại idempotent và chặn database mới hơn; chưa có
   migration từ bản phát hành cũ vì đây là bản đầu tiên.
8. Demo auth/session và license offline không thay backend production, online
   revocation hoặc cơ chế chống chỉnh đồng hồ. Không có tuyên bố chống crack tuyệt đối.

Không coi các mục chưa xác minh ở trên là PASS của Stage 19/20 trên Windows.

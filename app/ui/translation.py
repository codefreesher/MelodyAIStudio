"""Runtime translation for common desktop controls, preserving provider/model IDs."""

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QAbstractButton, QApplication, QLabel, QLineEdit, QTabBar

ENGLISH = {
    "Trang chủ": "Home",
    "Tạo nhạc": "Create music",
    "Tạo lyric": "Create lyrics",
    "Tạo audio": "Create audio",
    "Tạo ảnh": "Create images",
    "Lịch sử": "History",
    "Tài nguyên": "Resources",
    "Cấu hình Online": "Online AI",
    "Cấu hình Offline": "Offline AI",
    "Cập nhật": "Updates",
    "Cài đặt": "Settings",
    "Hôm nay bạn muốn sáng tạo điều gì?": "What would you like to create today?",
    "Dự án gần đây": "Recent projects",
    "Chưa có dự án": "No projects yet",
    "Tạo và lưu kết quả đầu tiên của bạn.": "Create and save your first result.",
    "Tìm trong lịch sử sáng tạo…": "Search creative history…",
    "Tìm kiếm…": "Search…",
    "Biến ý tưởng thành giai điệu": "Turn ideas into melodies",
    "Viết nên câu chuyện của bạn": "Write your story",
    "Thử nghiệm giọng đọc": "Explore audio",
    "Hình dung thế giới sáng tạo": "Imagine a creative world",
    "Từ prompt": "From prompt",
    "Từ lyric có sẵn": "From existing lyrics",
    "Tùy chỉnh nâng cao": "Advanced",
    "Từ chủ đề": "From topic",
    "Từ gợi ý nâng cao": "Advanced prompt",
    "Từ bài hát có sẵn": "From existing song",
    "Văn bản thành giọng nói": "Text to speech",
    "Từ file": "From file",
    "Từ ảnh tham khảo": "From reference",
    "Thể loại": "Genre",
    "Tâm trạng": "Mood",
    "Ngôn ngữ": "Language",
    "Thời lượng demo (giây)": "Demo duration (seconds)",
    "Provider dự kiến": "Planned provider",
    "Phong cách": "Style",
    "Cấu trúc": "Structure",
    "Số phiên bản": "Variations",
    "Giọng": "Voice",
    "Tốc độ": "Speed",
    "Định dạng": "Format",
    "Tỉ lệ ảnh": "Aspect ratio",
    "Tạo kèm lyric": "Include lyrics",
    "Tạo nhiều phiên bản": "Multiple variations",
    "Hủy tác vụ": "Cancel task",
    "Lưu lịch sử": "Save to history",
    "Tải tất cả": "Export all",
    "Sao chép lyric": "Copy lyrics",
    "Kết quả sẽ xuất hiện tại đây": "Your results will appear here",
    "Chưa có audio": "No audio yet",
    "Âm lượng": "Volume",
    "Nhập file TXT": "Import TXT",
    "Nhập file TXT / ảnh tham khảo": "Import TXT / reference image",
    "Tất cả": "All",
    "Nhạc": "Music",
    "Ảnh": "Images",
    "Mở": "Open",
    "Phát": "Play",
    "Tải xuống": "Download",
    "Xóa": "Delete",
    "Trước": "Previous",
    "Sau": "Next",
    "Lịch sử sáng tạo": "Creative history",
    "Cấu hình AI Online": "Online AI configuration",
    "Cấu hình AI Offline": "Offline AI configuration",
    "Bật provider": "Enable provider",
    "Model mặc định": "Default model",
    "Lưu": "Save",
    "Kiểm tra kết nối": "Test connection",
    "Nhập resource manifest JSON": "Import resource manifest JSON",
    "Sửa chữa": "Repair",
    "Mở thư mục": "Open folder",
    "Gỡ bỏ": "Remove",
    "Giao diện": "Appearance",
    "Màu chủ đạo": "Accent color",
    "Chung": "General",
    "Lưu cài đặt": "Save settings",
    "Tự kiểm tra cập nhật": "Automatically check updates",
    "Khởi động cùng Windows": "Start with Windows",
    "Đổi thư mục": "Change folder",
    "Xóa credentials": "Clear credentials",
    "Xóa session / Đăng xuất": "Clear session / Log out",
    "Xóa cache": "Clear cache",
    "Xem logs": "View logs",
    "Chưa kiểm tra": "Not checked",
    "Kiểm tra cập nhật": "Check updates",
    "Tải cập nhật": "Download update",
    "Cài cập nhật": "Install update",
    "Hủy tải": "Cancel download",
    "Hủy": "Cancel",
    "Xác nhận": "Confirm",
    "Đóng": "Close",
    "Đăng nhập": "Log in",
    "Kích hoạt": "Activate",
    "←  Quay lại": "←  Back",
    "Chào mừng bạn trở lại!": "Welcome back!",
    "Email hoặc tên tài khoản": "Email or username",
    "Mật khẩu": "Password",
    "Nhập mật khẩu": "Enter password",
    "Ghi nhớ đăng nhập": "Remember me",
    "Quên mật khẩu?": "Forgot password?",
    "hoặc": "or",
    "Đăng nhập với Google": "Continue with Google",
    "Chưa có tài khoản?": "Need an account?",
    "Liên hệ Admin": "Contact Admin",
    "Chế độ demo: tạo kết quả mẫu cục bộ. Các tùy chọn AI được lưu cùng kết quả; chưa gọi API thật.": "Demo mode: local sample results. AI options are saved with the result; no real AI API is called.",
}


class TranslationManager(QObject):
    def __init__(self, application: QApplication) -> None:
        super().__init__(application)
        self.application = application
        self.language = "vi"
        self.applying = False
        application.installEventFilter(self)

    def translate(self, text: str) -> str:
        if self.language == "vi":
            return text
        if text.startswith("Xin chào, "):
            return "Hello, " + text[len("Xin chào, ") :]
        return ENGLISH.get(text, text)

    def apply(self, language: str) -> None:
        self.language = language
        for widget in self.application.allWidgets():
            self._widget(widget)

    def _widget(self, widget) -> None:
        if self.applying:
            return
        self.applying = True
        try:
            if isinstance(widget, (QLabel, QAbstractButton)):
                self._text(widget, widget.text, widget.setText, "text")
            elif isinstance(widget, QLineEdit):
                self._text(widget, widget.placeholderText, widget.setPlaceholderText, "placeholder")
            elif isinstance(widget, QTabBar):
                for index in range(widget.count()):
                    self._text(
                        widget,
                        lambda i=index: widget.tabText(i),
                        lambda value, i=index: widget.setTabText(i, value),
                        f"tab{index}",
                    )
        finally:
            self.applying = False

    def _text(self, widget, get, set_text, key: str) -> None:
        current = get()
        source = widget.property("source_" + key)
        if current != widget.property("translated_" + key) or source is None:
            source = current
        translated = self.translate(source)
        widget.setProperty("source_" + key, source)
        widget.setProperty("translated_" + key, translated)
        if translated != current:
            set_text(translated)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Show, QEvent.Type.Polish):
            self._widget(watched)
        return False

"""Shared generation form/result UI; no provider or storage access."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.buttons import OutlineButton, PrimaryButton
from app.ui.widgets.dropdown import ComboBox
from app.ui.widgets.toast import Toast

SPECS = {
    "music": (
        "Tạo nhạc",
        ["Từ prompt", "Từ lyric có sẵn", "Tùy chỉnh nâng cao"],
        {
            "genre": ["Pop", "Ballad", "Jazz", "Rock"],
            "mood": ["Vui vẻ", "Thư giãn", "Buồn"],
            "language": ["Vietnamese", "English"],
            "duration": ["6", "15", "30"],
            "provider": ["Auto", "Online", "Local"],
        },
    ),
    "lyric": (
        "Tạo lyric",
        ["Từ chủ đề", "Từ gợi ý nâng cao", "Từ bài hát có sẵn"],
        {
            "style": ["Pop", "Ballad", "Rap"],
            "mood": ["Vui vẻ", "Buồn"],
            "language": ["Vietnamese", "English"],
            "structure": ["Verse - Chorus", "Verse - Chorus - Bridge", "Custom"],
            "count": ["1", "2", "3"],
            "provider": ["OpenAI", "Claude", "Gemini", "Ollama"],
        },
    ),
    "audio": (
        "Tạo audio",
        ["Văn bản thành giọng nói", "Từ file", "Tùy chỉnh nâng cao"],
        {
            "voice": ["Nữ demo", "Nam demo"],
            "language": ["Vietnamese", "English"],
            "speed": ["0.5", "0.75", "1.0", "1.25", "1.5"],
            "format": ["WAV", "MP3"],
        },
    ),
    "image": (
        "Tạo ảnh",
        ["Từ prompt", "Từ ảnh tham khảo", "Tùy chỉnh nâng cao"],
        {
            "ratio": ["1:1", "16:9", "9:16", "4:3", "3:2"],
            "count": ["1", "2", "4"],
            "style": ["Realistic", "Anime", "Digital Art", "Illustration", "Cinematic"],
            "provider": ["Auto", "Online", "Local"],
        },
    ),
}
LABELS = {
    "genre": "Thể loại",
    "mood": "Tâm trạng",
    "language": "Ngôn ngữ",
    "duration": "Thời lượng demo (giây)",
    "provider": "Provider dự kiến",
    "style": "Phong cách",
    "structure": "Cấu trúc",
    "count": "Số phiên bản",
    "voice": "Giọng",
    "speed": "Tốc độ",
    "format": "Định dạng",
    "ratio": "Tỉ lệ ảnh",
}


class GenerationPage(QWidget):
    generate_requested = Signal(str, dict)
    cancel_requested = Signal()
    save_requested = Signal()
    export_requested = Signal()
    import_requested = Signal()
    copy_requested = Signal()

    def __init__(self, kind: str) -> None:
        super().__init__()
        self.kind = kind
        title, tabs, options = SPECS[kind]
        root = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setProperty("role", "heading")
        root.addWidget(heading)
        notice = QLabel(
            "Chế độ demo: tạo kết quả mẫu cục bộ. Các tùy chọn AI được lưu cùng kết quả; chưa gọi API thật."
        )
        notice.setWordWrap(True)
        notice.setProperty("role", "muted")
        root.addWidget(notice)
        self.toast = Toast()
        root.addWidget(self.toast)
        row = QHBoxLayout()
        root.addLayout(row, 1)
        form = QVBoxLayout()
        row.addLayout(form, 3)
        self.tabs = QTabWidget()
        self.prompts = []
        for caption in tabs:
            editor = QPlainTextEdit()
            editor.setPlaceholderText("Nhập nội dung hoặc ý tưởng…")
            self.tabs.addTab(editor, caption)
            self.prompts.append(editor)
        form.addWidget(self.tabs)
        self.import_button = OutlineButton(
            "Nhập file TXT / ảnh tham khảo" if kind == "image" else "Nhập file TXT"
        )
        self.import_button.clicked.connect(self.import_requested.emit)
        form.addWidget(self.import_button)
        fields = QFormLayout()
        self.options = {}
        for key, choices in options.items():
            field = ComboBox(choices)
            self.options[key] = field
            fields.addRow(LABELS[key], field)
        form.addLayout(fields)
        self.extra = QCheckBox("Tạo kèm lyric" if kind == "music" else "Tạo nhiều phiên bản")
        self.extra.setVisible(kind in ("music", "lyric"))
        form.addWidget(self.extra)
        self.generate_button = PrimaryButton(title)
        self.cancel_button = OutlineButton("Hủy tác vụ")
        self.cancel_button.setEnabled(False)
        form.addWidget(self.generate_button)
        form.addWidget(self.cancel_button)
        self.generate_button.clicked.connect(self._generate)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        result = QVBoxLayout()
        row.addLayout(result, 2)
        self.result_title = QLabel("Kết quả sẽ xuất hiện tại đây")
        self.result_title.setWordWrap(True)
        result.addWidget(self.result_title)
        self.editors = QTabWidget()
        result.addWidget(self.editors)
        self.player = None
        self.gallery = None
        self.waveform = None
        if kind in ("music", "audio"):
            from app.ui.widgets.player import AudioPlayer

            if kind == "music":
                from pathlib import Path

                from PySide6.QtCore import Qt
                from PySide6.QtSvgWidgets import QSvgWidget

                cover = QSvgWidget(
                    str(Path(__file__).resolve().parents[2] / "assets/images/startup-headphones.svg")
                )
                cover.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
                cover.setFixedHeight(160)
                result.addWidget(cover)
            from app.ui.widgets.waveform import Waveform

            self.waveform = Waveform()
            result.addWidget(self.waveform)
            self.player = AudioPlayer()
            result.addWidget(self.player)
            self.editors.hide()
        if kind == "image":
            from app.ui.widgets.image_gallery import ImageGallery

            self.gallery = ImageGallery()
            result.addWidget(self.gallery)
            self.editors.hide()
        self.copy_button = OutlineButton("Sao chép lyric")
        self.copy_button.setVisible(kind == "lyric")
        self.copy_button.clicked.connect(self.copy_requested.emit)
        result.addWidget(self.copy_button)
        self.save_button = OutlineButton("Lưu lịch sử")
        self.export_button = OutlineButton("Tải tất cả")
        self.save_button.clicked.connect(self.save_requested.emit)
        self.export_button.clicked.connect(self.export_requested.emit)
        result.addWidget(self.save_button)
        result.addWidget(self.export_button)
        result.addStretch()
        self.set_result_enabled(False)

    def _generate(self) -> None:
        options = {key: field.currentText() for key, field in self.options.items()}
        options["tab"] = self.tabs.tabText(self.tabs.currentIndex())
        options["extra"] = self.extra.isChecked()
        if self.kind == "lyric" and not self.extra.isChecked():
            options["count"] = "1"
        self.generate_requested.emit(self.prompts[self.tabs.currentIndex()].toPlainText(), options)

    def set_result_enabled(self, enabled: bool) -> None:
        for button in (self.save_button, self.export_button, self.copy_button):
            button.setEnabled(enabled)

    def set_loading(self, loading: bool) -> None:
        self.generate_button.set_loading(loading)
        self.cancel_button.setEnabled(loading)
        self.tabs.setEnabled(not loading)
        self.import_button.setEnabled(not loading)

    def show_result(self, result: object, texts: list[str]) -> None:
        self.result_title.setText(result.title + " · Demo")
        while self.editors.count():
            widget = self.editors.widget(0)
            self.editors.removeTab(0)
            widget.deleteLater()
        for index, text in enumerate(texts):
            editor = QPlainTextEdit(text)
            self.editors.addTab(editor, f"Bản {index + 1}")
        if self.player:
            self.player.set_source(result.paths[0])
            self.waveform.set_values(result.metadata.get("waveform", []))
        if self.gallery:
            self.gallery.set_images(result.paths)
        self.set_result_enabled(True)

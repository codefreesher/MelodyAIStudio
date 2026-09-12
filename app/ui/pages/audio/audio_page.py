"""Dedicated MelodyAI text-to-speech workspace."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit, QTabWidget, QVBoxLayout, QWidget

from app.ui.pages.music.music_page import MusicPlayer
from app.ui.widgets.buttons import OutlineButton, PrimaryButton
from app.ui.widgets.dropdown import ComboBox
from app.ui.widgets.toast import Toast

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"


class AudioPage(QWidget):
    generate_requested = Signal(str, dict)
    cancel_requested = Signal()
    save_requested = Signal()
    export_requested = Signal()
    import_requested = Signal()
    copy_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.kind = "audio"
        self.setObjectName("audioPage")
        outer = QHBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 20)
        outer.addStretch(1)
        content = QWidget()
        content.setObjectName("audioContent")
        content.setMaximumWidth(920)
        root = QVBoxLayout(content)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(10)
        outer.addWidget(content, 4)
        outer.addStretch(1)

        heading_row = QHBoxLayout()
        heading_icon = QLabel()
        heading_icon.setObjectName("audioHeadingIcon")
        heading_icon.setFixedSize(34, 34)
        heading_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading_icon.setPixmap(QIcon(str(_ICONS / "dashboard-audio.svg")).pixmap(QSize(27, 27)))
        heading = QLabel("Tạo audio (TTS)")
        heading.setObjectName("audioHeading")
        heading_row.addWidget(heading_icon)
        heading_row.addWidget(heading)
        heading_row.addStretch(1)
        root.addLayout(heading_row)
        self.toast = Toast(plain=True)
        root.addWidget(self.toast)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("audioTabs")
        self.prompts: list[QPlainTextEdit] = []
        for caption, placeholder in (
            ("Văn bản thành giọng nói", "Nhập nội dung cần chuyển thành giọng nói…"),
            ("Tùy chỉnh nâng cao", "Nhập nội dung và thiết lập cách đọc mong muốn…"),
        ):
            editor = QPlainTextEdit()
            editor.setObjectName("audioPrompt")
            editor.setPlaceholderText(placeholder)
            editor.textChanged.connect(lambda field=editor: self._limit_prompt(field))
            self.tabs.addTab(editor, caption)
            self.prompts.append(editor)
        root.addWidget(self.tabs, 1)
        self.character_count = QLabel("0/1000")
        self.character_count.setObjectName("audioCharacterCount")
        self.character_count.setMinimumWidth(58)
        self.character_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(self.character_count, alignment=Qt.AlignmentFlag.AlignRight)

        self.import_button = OutlineButton("Nhập file TXT")
        self.import_button.clicked.connect(self.import_requested.emit)
        self.import_button.hide()

        options_row = QHBoxLayout()
        options_row.setSpacing(8)
        self.options: dict[str, ComboBox] = {}
        choices = {
            "voice": ("Giọng nói", ["Việt Nam - Nữ (Tự nhiên)", "Việt Nam - Nam (Tự nhiên)"]),
            "speed": ("Tốc độ", ["0.5", "0.75", "1.0", "1.25", "1.5"]),
            "format": ("Định dạng", ["MP3", "WAV"]),
        }
        for key, (caption, values) in choices.items():
            column = QVBoxLayout()
            label = QLabel(caption)
            label.setObjectName("audioOptionLabel")
            field = ComboBox(values)
            self.options[key] = field
            column.addWidget(label)
            column.addWidget(field)
            options_row.addLayout(column, 2 if key == "voice" else 1)
        self.options["speed"].setCurrentText("1.0")
        root.addLayout(options_row)
        self.options["language"] = ComboBox(["Vietnamese", "English"])
        self.options["language"].hide()

        self.generate_button = PrimaryButton("◖   Tạo audio")
        self.generate_button.setObjectName("audioGenerate")
        self.cancel_button = OutlineButton("Hủy tác vụ")
        self.cancel_button.setEnabled(False)
        self.cancel_button.hide()
        root.addWidget(self.generate_button)
        root.addWidget(self.cancel_button)
        self.generate_button.clicked.connect(self._generate)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)

        self.result_title = QLabel("Kết quả audio")
        self.result_title.setObjectName("audioResultTitle")
        self.result_title.hide()
        self.player = MusicPlayer()
        self.player.setObjectName("audioResultPlayer")
        root.addWidget(self.player)
        actions = QHBoxLayout()
        self.export_button = OutlineButton("Tải xuống")
        self.save_button = OutlineButton("Lưu vào lịch sử")
        self.export_button.clicked.connect(self.export_requested.emit)
        self.save_button.clicked.connect(self.save_requested.emit)
        actions.addWidget(self.export_button)
        actions.addWidget(self.save_button)
        root.addLayout(actions)
        self.extra = QWidget()
        self.extra.setVisible(False)
        self.editors = QTabWidget()
        self.editors.hide()
        self.copy_button = OutlineButton("Sao chép")
        self.copy_button.hide()
        self.gallery = None
        self.waveform = None
        self.set_result_enabled(False)

    def _limit_prompt(self, editor: QPlainTextEdit) -> None:
        text = editor.toPlainText()
        if len(text) > 1000:
            editor.blockSignals(True)
            editor.setPlainText(text[:1000])
            cursor = editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            editor.setTextCursor(cursor)
            editor.blockSignals(False)
            text = text[:1000]
        if editor is self.prompts[self.tabs.currentIndex()]:
            self.character_count.setText(f"{len(text)}/1000")

    def _generate(self) -> None:
        options = {key: field.currentText() for key, field in self.options.items()}
        options["tab"] = self.tabs.tabText(self.tabs.currentIndex())
        options["extra"] = False
        self.generate_requested.emit(self.prompts[self.tabs.currentIndex()].toPlainText(), options)

    def set_result_enabled(self, enabled: bool) -> None:
        self.save_button.setEnabled(enabled)
        self.export_button.setEnabled(enabled)

    def set_loading(self, loading: bool) -> None:
        self.generate_button.set_loading(loading)
        self.cancel_button.setVisible(loading)
        self.cancel_button.setEnabled(loading)
        self.tabs.setEnabled(not loading)

    def show_result(self, generated: object, texts: list[str]) -> None:  # noqa: ARG002
        self.result_title.setText(generated.title)
        self.player.set_source(generated.paths[0])
        self.set_result_enabled(True)

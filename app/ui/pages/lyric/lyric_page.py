"""Dedicated MelodyAI lyric-generation workspace."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit, QTabWidget, QVBoxLayout, QWidget

from app.ui.widgets.buttons import OutlineButton, PrimaryButton
from app.ui.widgets.dropdown import ComboBox
from app.ui.widgets.toast import Toast
from app.ui.widgets.toggle import ToggleSwitch


class LyricPage(QWidget):
    generate_requested = Signal(str, dict)
    cancel_requested = Signal()
    save_requested = Signal()
    export_requested = Signal()
    import_requested = Signal()
    copy_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.kind = "lyric"
        self.setObjectName("lyricPage")
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 20)
        root.setSpacing(10)

        heading_row = QHBoxLayout()
        heading_icon = QLabel("▤")
        heading_icon.setObjectName("lyricHeadingIcon")
        heading = QLabel("Tạo lyric")
        heading.setObjectName("lyricHeading")
        heading_row.addWidget(heading_icon)
        heading_row.addWidget(heading)
        heading_row.addStretch(1)
        root.addLayout(heading_row)
        self.toast = Toast(plain=True)
        root.addWidget(self.toast)

        workspace = QHBoxLayout()
        workspace.setSpacing(16)
        root.addLayout(workspace, 1)

        form_panel = QWidget()
        form_panel.setObjectName("lyricFormPanel")
        form = QVBoxLayout(form_panel)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)
        workspace.addWidget(form_panel, 58)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("lyricTabs")
        self.prompts: list[QPlainTextEdit] = []
        placeholders = [
            "Nhập chủ đề, cảm xúc, câu chuyện…\nVí dụ: Tình bạn, tuổi trẻ, quê hương…",
            "Mô tả phong cách, cách gieo vần và thông điệp…",
            "Dán lời bài hát tham khảo vào đây…",
        ]
        for caption, placeholder in zip(
            ("Từ chủ đề", "Từ gợi ý nâng cao", "Từ bài hát có sẵn"), placeholders
        ):
            editor = QPlainTextEdit()
            editor.setObjectName("lyricPrompt")
            editor.setPlaceholderText(placeholder)
            editor.textChanged.connect(lambda field=editor: self._limit_prompt(field))
            self.tabs.addTab(editor, caption)
            self.prompts.append(editor)
        form.addWidget(self.tabs, 1)
        self.character_count = QLabel("0/500")
        self.character_count.setObjectName("lyricCharacterCount")
        self.character_count.setMinimumWidth(52)
        self.character_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        form.addWidget(self.character_count, alignment=Qt.AlignmentFlag.AlignRight)

        self.import_button = OutlineButton("Nhập file TXT")
        self.import_button.setObjectName("lyricImport")
        self.import_button.clicked.connect(self.import_requested.emit)
        form.addWidget(self.import_button)

        options_row = QHBoxLayout()
        options_row.setSpacing(8)
        self.options: dict[str, ComboBox] = {}
        choices = {
            "style": ("Phong cách", ["Pop", "Ballad", "Rap"]),
            "mood": ("Tâm trạng", ["Vui vẻ", "Buồn"]),
            "language": ("Ngôn ngữ", ["Vietnamese", "English"]),
        }
        for key, (caption, values) in choices.items():
            column = QVBoxLayout()
            label = QLabel(caption)
            label.setObjectName("lyricOptionLabel")
            field = ComboBox(values)
            self.options[key] = field
            column.addWidget(label)
            column.addWidget(field)
            options_row.addLayout(column, 1)
        form.addLayout(options_row)
        self.options["structure"] = ComboBox(
            ["Verse - Chorus", "Verse - Chorus - Bridge", "Custom"]
        )
        self.options["structure"].hide()
        self.options["provider"] = ComboBox(["OpenAI", "Claude", "Gemini", "Ollama"])
        self.options["provider"].hide()

        versions_row = QHBoxLayout()
        self.extra = ToggleSwitch("Tạo nhiều phiên bản")
        versions_row.addWidget(self.extra)
        versions_row.addStretch(1)
        self.options["count"] = ComboBox(["1", "2", "3"])
        self.options["count"].setCurrentText("3")
        self.options["count"].setMinimumWidth(130)
        versions_row.addWidget(self.options["count"])
        form.addLayout(versions_row)

        self.generate_button = PrimaryButton("▤   Tạo lyric")
        self.generate_button.setObjectName("lyricGenerate")
        self.cancel_button = OutlineButton("Hủy tác vụ")
        self.cancel_button.setEnabled(False)
        self.cancel_button.hide()
        form.addWidget(self.generate_button)
        form.addWidget(self.cancel_button)
        self.generate_button.clicked.connect(self._generate)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)

        result_panel = QWidget()
        result_panel.setObjectName("lyricResultPanel")
        result = QVBoxLayout(result_panel)
        result.setContentsMargins(16, 16, 16, 16)
        result.setSpacing(10)
        workspace.addWidget(result_panel, 42)
        self.result_title = QLabel("Kết quả")
        self.result_title.setObjectName("lyricResultHeading")
        result.addWidget(self.result_title)
        self.editors = QTabWidget()
        self.editors.setObjectName("lyricResultTabs")
        placeholder = QPlainTextEdit()
        placeholder.setReadOnly(True)
        placeholder.setPlaceholderText("Lyric được tạo sẽ xuất hiện tại đây…")
        self.editors.addTab(placeholder, "Bản 1")
        result.addWidget(self.editors, 1)
        actions = QHBoxLayout()
        self.copy_button = OutlineButton("Sao chép")
        self.save_button = OutlineButton("Lưu")
        self.export_button = OutlineButton("Tải tất cả")
        self.export_button.hide()
        self.copy_button.clicked.connect(self.copy_requested.emit)
        self.save_button.clicked.connect(self.save_requested.emit)
        self.export_button.clicked.connect(self.export_requested.emit)
        actions.addWidget(self.copy_button)
        actions.addWidget(self.save_button)
        result.addLayout(actions)
        self.player = None
        self.gallery = None
        self.waveform = None
        self.set_result_enabled(False)

    def _limit_prompt(self, editor: QPlainTextEdit) -> None:
        text = editor.toPlainText()
        if len(text) > 500:
            cursor = editor.textCursor()
            editor.blockSignals(True)
            editor.setPlainText(text[:500])
            cursor.movePosition(cursor.MoveOperation.End)
            editor.setTextCursor(cursor)
            editor.blockSignals(False)
            text = text[:500]
        if editor is self.prompts[self.tabs.currentIndex()]:
            self.character_count.setText(f"{len(text)}/500")

    def _generate(self) -> None:
        options = {key: field.currentText() for key, field in self.options.items()}
        options["tab"] = self.tabs.tabText(self.tabs.currentIndex())
        options["extra"] = self.extra.isChecked()
        if not self.extra.isChecked():
            options["count"] = "1"
        self.generate_requested.emit(self.prompts[self.tabs.currentIndex()].toPlainText(), options)

    def set_result_enabled(self, enabled: bool) -> None:
        for button in (self.copy_button, self.save_button, self.export_button):
            button.setEnabled(enabled)

    def set_loading(self, loading: bool) -> None:
        self.generate_button.set_loading(loading)
        self.cancel_button.setVisible(loading)
        self.cancel_button.setEnabled(loading)
        self.tabs.setEnabled(not loading)
        self.import_button.setEnabled(not loading)

    def show_result(self, generated: object, texts: list[str]) -> None:
        self.result_title.setText("Kết quả")
        while self.editors.count():
            widget = self.editors.widget(0)
            self.editors.removeTab(0)
            widget.deleteLater()
        for index, text in enumerate(texts):
            editor = QPlainTextEdit(text)
            editor.setObjectName("lyricResultEditor")
            self.editors.addTab(editor, f"Bản {index + 1}")
        self.set_result_enabled(True)

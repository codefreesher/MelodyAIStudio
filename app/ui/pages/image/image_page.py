"""Dedicated MelodyAI image-generation workspace.

Mirrors the shape :class:`app.controllers.generation_controller.GenerationController`
expects from :class:`app.ui.pages.generation_page.GenerationPage` (signals,
``tabs``/``prompts``/``options``/``extra``/``editors``/``player``/``gallery``,
``set_loading``/``set_result_enabled``/``show_result``) so the same
controller drives this page unchanged — only the presentation differs.
"""

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.buttons import OutlineButton, PrimaryButton
from app.ui.widgets.dropdown import ComboBox
from app.ui.widgets.image_result_gallery import ImageResultGallery
from app.ui.widgets.text_link import TextLink
from app.ui.widgets.toast import Toast

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"
_MAX_PROMPT = 1000


class ImagePage(QWidget):
    generate_requested = Signal(str, dict)
    cancel_requested = Signal()
    save_requested = Signal()
    export_requested = Signal()
    import_requested = Signal()
    copy_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.kind = "image"
        self.setObjectName("imagePage")
        page = QVBoxLayout(self)
        page.setContentsMargins(24, 20, 24, 24)
        page.setSpacing(12)
        page.addLayout(self._build_heading())
        self.toast = Toast(plain=True)
        page.addWidget(self.toast)

        # Left = the compact form (prompt/options/generate); right = results.
        # Side by side rather than stacked so the gallery gets the window's
        # spare width instead of being squeezed into the same narrow column.
        body = QHBoxLayout()
        body.setSpacing(24)
        page.addLayout(body, 1)

        form_panel = QWidget()
        form_panel.setObjectName("imageFormPanel")
        form_panel.setMaximumWidth(480)
        root = QVBoxLayout(form_panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        body.addWidget(form_panel)

        result_column = QVBoxLayout()
        body.addLayout(result_column, 1)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("imageTabs")
        self.tabs.addTab(self._build_prompt_tab(), "Từ prompt")
        self.tabs.addTab(self._build_reference_tab(), "Từ ảnh tham khảo")
        self.tabs.addTab(self._build_advanced_tab(), "Tùy chỉnh nâng cao")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        root.addWidget(self.tabs)

        # A single shared prompt buffer for tabs 0 and 2 — the advanced tab
        # only adds generation parameters on top of the same prompt, it has
        # no separate text of its own. Kept so GenerationController's
        # index-based prompts[...] access (see import_file) stays valid for
        # every tab.
        self.prompts: list[QPlainTextEdit] = [self.prompt_edit, self.reference_note, self.prompt_edit]

        root.addLayout(self._build_options_row())

        self.generate_button = PrimaryButton("Tạo ảnh")
        self.generate_button.setObjectName("imageGenerate")
        self.generate_button.setIcon(QIcon(str(_ICONS / "image-white.svg")))
        self.generate_button.setIconSize(QSize(16, 16))
        self.generate_button.clicked.connect(self._generate)
        root.addWidget(self.generate_button)

        status_row = QHBoxLayout()
        self.status_label = QLabel("Đang tạo ảnh…")
        self.status_label.setObjectName("imageStatus")
        self.status_label.hide()
        status_row.addWidget(self.status_label)
        status_row.addStretch(1)
        self.cancel_button = TextLink("Hủy")
        self.cancel_button.setObjectName("imageCancel")
        self.cancel_button.hide()
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        status_row.addWidget(self.cancel_button)
        root.addLayout(status_row)
        root.addStretch(1)

        self.gallery = ImageResultGallery()
        self.gallery.download_requested.connect(lambda _path: self.export_requested.emit())
        self.gallery.download_all_requested.connect(self.export_requested.emit)
        self.gallery.save_requested.connect(lambda _path: self.save_requested.emit())
        self.gallery.error.connect(lambda message: self.toast.show_message(message, "error"))
        result_column.addWidget(self.gallery, 1)

        # Required by GenerationController's generic contract but unused by
        # this tool: no lyric/audio result editors, no extra checkbox row.
        self.editors = QTabWidget()
        self.editors.hide()
        self.player = None
        self.waveform = None
        self.extra = QWidget()
        self.extra.setVisible(False)
        self.copy_button = OutlineButton("Sao chép")
        self.copy_button.hide()

        self.set_result_enabled(False)

    # -- construction helpers -------------------------------------------------

    def _build_heading(self) -> QHBoxLayout:
        row = QHBoxLayout()
        icon = QLabel()
        icon.setObjectName("imageHeadingIcon")
        icon.setFixedSize(32, 32)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setPixmap(QIcon(str(_ICONS / "dashboard-image.svg")).pixmap(QSize(20, 20)))
        heading = QLabel("Tạo ảnh")
        heading.setObjectName("imageHeading")
        row.addWidget(icon)
        row.addWidget(heading)
        badge = QLabel("Local")
        badge.setObjectName("imageDemoBadge")
        badge.setToolTip("Tạo ảnh bằng engine Stable Diffusion trên máy.")
        row.addWidget(badge)
        row.addStretch(1)
        return row

    def _build_prompt_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(4)
        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setObjectName("imagePrompt")
        self.prompt_edit.setPlaceholderText(
            "Nhập mô tả hình ảnh...\nVí dụ: cô gái đeo tai nghe, phong cách anime, hoàng hôn..."
        )
        self.prompt_edit.textChanged.connect(self._limit_prompt)
        layout.addWidget(self.prompt_edit)
        self.character_count = QLabel(f"0/{_MAX_PROMPT}")
        self.character_count.setObjectName("imageCharacterCount")
        layout.addWidget(self.character_count, alignment=Qt.AlignmentFlag.AlignRight)
        return tab

    def _build_reference_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(8)

        self.pick_reference_button = OutlineButton("Chọn ảnh tham khảo")
        self.pick_reference_button.setObjectName("imagePickReference")
        self.pick_reference_button.setIcon(QIcon(str(_ICONS / "plus.svg")))
        self.pick_reference_button.setIconSize(QSize(13, 13))
        self.pick_reference_button.clicked.connect(self.import_requested.emit)
        layout.addWidget(self.pick_reference_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.reference_chip = QWidget()
        self.reference_chip.setObjectName("imageReferenceChip")
        chip_row = QHBoxLayout(self.reference_chip)
        chip_row.setContentsMargins(10, 6, 6, 6)
        self.reference_chip_label = QLabel()
        self.reference_chip_label.setObjectName("imageReferenceChipLabel")
        chip_row.addWidget(self.reference_chip_label, 1)
        remove_button = QPushButton()
        remove_button.setObjectName("imageReferenceRemove")
        remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_button.setIcon(QIcon(str(_ICONS / "close-small.svg")))
        remove_button.setIconSize(QSize(11, 11))
        remove_button.clicked.connect(self._clear_reference)
        chip_row.addWidget(remove_button)
        self.reference_chip.hide()
        layout.addWidget(self.reference_chip)

        # Back-end buffer the controller writes "Ảnh tham khảo: <name>" into
        # (see GenerationController.import_file); never shown directly —
        # the chip above mirrors it for display.
        self.reference_note = QPlainTextEdit()
        self.reference_note.hide()
        self.reference_note.textChanged.connect(self._sync_reference_chip)
        layout.addWidget(self.reference_note)
        layout.addStretch(1)
        return tab

    def _build_advanced_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)

        self.advanced = {}
        rows = (
            ("provider", "Provider", ComboBox(["Auto", "Online", "Local"])),
            ("model", "Model", ComboBox(["Auto", "SDXL", "SD 1.5", "Midjourney style"])),
            ("quality", "Chất lượng", ComboBox(["Draft", "Standard", "High"])),
        )
        for row in (rows[:2], rows[2:]):
            line = QHBoxLayout()
            line.setSpacing(10)
            for key, caption, field in row:
                field.setObjectName("imageAdvancedField")
                self.advanced[key] = field
                line.addLayout(self._labeled(caption, field), 1)
            layout.addLayout(line)

        negative_label = QLabel("Negative Prompt")
        negative_label.setObjectName("imageOptionLabel")
        layout.addWidget(negative_label)
        self.negative_prompt = QLineEdit()
        self.negative_prompt.setObjectName("imageAdvancedField")
        self.negative_prompt.setPlaceholderText("Những gì không muốn xuất hiện trong ảnh…")
        layout.addWidget(self.negative_prompt)

        fine_row = QHBoxLayout()
        fine_row.setSpacing(10)
        self.seed_field = QLineEdit()
        self.seed_field.setObjectName("imageAdvancedField")
        self.seed_field.setPlaceholderText("Ngẫu nhiên")
        self.steps_field = ComboBox(["20", "30", "50"])
        self.steps_field.setObjectName("imageAdvancedField")
        self.cfg_field = ComboBox(["5", "7", "9", "12"])
        self.cfg_field.setObjectName("imageAdvancedField")
        for caption, field in (("Seed", self.seed_field), ("Steps", self.steps_field), ("CFG Scale", self.cfg_field)):
            fine_row.addLayout(self._labeled(caption, field), 1)
        layout.addLayout(fine_row)
        layout.addStretch(1)
        return tab

    @staticmethod
    def _labeled(caption: str, field: QWidget) -> QVBoxLayout:
        column = QVBoxLayout()
        column.setSpacing(4)
        label = QLabel(caption)
        label.setObjectName("imageOptionLabel")
        column.addWidget(label)
        column.addWidget(field)
        return column

    def _build_options_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        self.options: dict[str, ComboBox] = {}
        fields = (
            # AIService only accepts these five ratio strings — kept in sync
            # with app/services/ai_service.py's validation.
            ("ratio", "Tỷ lệ khung hình", ["1:1", "16:9 (YouTube)", "9:16", "4:3", "3:2"], 3),
            ("count", "Số lượng ảnh", ["1 ảnh", "2 ảnh", "4 ảnh"], 2),
            ("style", "Phong cách", ["Auto", "Realistic", "Anime", "Digital Art", "Illustration", "Cinematic", "3D", "Watercolor"], 4),
        )
        for key, caption, values, stretch in fields:
            field = ComboBox(values)
            field.setObjectName("imageOptionField")
            self.options[key] = field
            row.addLayout(self._labeled(caption, field), stretch)
        self.options["style"].setCurrentText("Anime")
        return row

    # -- behaviour --------------------------------------------------------

    def _on_tab_changed(self, index: int) -> None:
        self.character_count.setVisible(index == 0)

    def _limit_prompt(self) -> None:
        text = self.prompt_edit.toPlainText()
        if len(text) > _MAX_PROMPT:
            self.prompt_edit.blockSignals(True)
            self.prompt_edit.setPlainText(text[:_MAX_PROMPT])
            cursor = self.prompt_edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.prompt_edit.setTextCursor(cursor)
            self.prompt_edit.blockSignals(False)
            text = text[:_MAX_PROMPT]
        self.character_count.setText(f"{len(text)}/{_MAX_PROMPT}")

    def _sync_reference_chip(self) -> None:
        text = self.reference_note.toPlainText().strip()
        self.reference_chip_label.setText(text)
        self.reference_chip.setVisible(bool(text))
        self.pick_reference_button.setVisible(not text)

    def _clear_reference(self) -> None:
        self.reference_note.clear()

    def _generate(self) -> None:
        # ratio/count carry a decorative suffix for display ("16:9
        # (YouTube)", "4 ảnh"); AIService wants the bare value.
        options = {
            "ratio": self.options["ratio"].currentText().split(" ")[0],
            "count": self.options["count"].currentText().split(" ")[0],
            "style": self.options["style"].currentText(),
        }
        options["provider"] = self.advanced["provider"].currentText()
        options["model"] = self.advanced["model"].currentText()
        options["quality"] = self.advanced["quality"].currentText()
        options["negative_prompt"] = self.negative_prompt.text()
        options["seed"] = self.seed_field.text()
        options["steps"] = self.steps_field.currentText()
        options["cfg_scale"] = self.cfg_field.currentText()
        options["tab"] = self.tabs.tabText(self.tabs.currentIndex())
        options["extra"] = False
        self.generate_requested.emit(self.prompt_edit.toPlainText(), options)

    def set_result_enabled(self, enabled: bool) -> None:  # noqa: ARG002 - kept for contract parity
        pass

    def set_loading(self, loading: bool) -> None:
        self.generate_button.set_loading(loading, "Đang tạo ảnh…")
        self.status_label.setVisible(loading)
        self.cancel_button.setVisible(loading)
        self.tabs.setEnabled(not loading)
        self.gallery.set_loading(loading)

    def show_result(self, result: object, texts: list[str]) -> None:  # noqa: ARG002 - shared contract
        self.gallery.set_images(result.paths)

"""Temporary Stage 03 component laboratory, launched with --showcase."""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.buttons import DangerButton, IconButton, OutlineButton, PrimaryButton, SecondaryButton
from app.ui.widgets.cards import FeatureCard, ProjectCard, ProviderCard, ResourceCard, StatCard
from app.ui.widgets.dialog import ConfirmDialog, ErrorDialog
from app.ui.widgets.dropdown import ComboBox
from app.ui.widgets.empty_state import EmptyState
from app.ui.widgets.image_gallery import ImageGallery
from app.ui.widgets.inputs import PasswordInput, SearchInput, TextInput
from app.ui.widgets.player import AudioPlayer
from app.ui.widgets.progress import LoadingOverlay, ProgressDialog
from app.ui.widgets.sidebar import Sidebar
from app.ui.widgets.titlebar import TitleBar
from app.ui.widgets.toast import Toast


class ComponentShowcase(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QHBoxLayout(self)
        sidebar = Sidebar()
        sidebar.add_item("components", "Components")
        sidebar.add_item("states", "Trạng thái")
        sidebar.set_current("components")
        sidebar.set_profile("MelodyAI", "Stage 03")
        root.addWidget(sidebar)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        root.addWidget(scroll, 1)
        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.addWidget(TitleBar("MelodyAI — Component Showcase"))
        heading = QLabel("Reusable UI components")
        heading.setProperty("role", "heading")
        layout.addWidget(heading)
        self.toast = Toast()
        layout.addWidget(self.toast)
        sidebar.page_requested.connect(lambda key: self.toast.show_message(f"Navigation: {key}"))
        buttons = QGridLayout()
        for index, cls in enumerate((PrimaryButton, SecondaryButton, OutlineButton, DangerButton)):
            button = cls(cls.__name__)
            button.clicked.connect(
                lambda checked=False, name=cls.__name__: self.toast.show_message(name, "success")
            )
            buttons.addWidget(button, index // 2, index % 2)
        icon = IconButton(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Lưu")
        buttons.addWidget(icon, 2, 0)
        disabled = PrimaryButton("Disabled")
        disabled.setEnabled(False)
        buttons.addWidget(disabled, 2, 1)
        busy = PrimaryButton("Thử loading")
        busy.clicked.connect(lambda: self._busy(busy))
        buttons.addWidget(busy, 3, 0)
        layout.addLayout(buttons)
        for field in (
            TextInput("Tên dự án"),
            PasswordInput(),
            SearchInput(),
            ComboBox(["Auto", "Online", "Local"]),
        ):
            layout.addWidget(field)
        cards = QGridLayout()
        for index, card in enumerate(
            (
                FeatureCard("Tạo nhạc", "Khám phá ý tưởng mới"),
                ProjectCard("Dự án mẫu", "Lyric", "Hôm nay"),
                StatCard("Dự án", "12"),
                ProviderCard("AI Provider", "Chưa kết nối API"),
                ResourceCard("Tài nguyên mẫu", "Chỉ kiểm tra component", "1.0"),
            )
        ):
            cards.addWidget(card, index // 2, index % 2)
        layout.addLayout(cards)
        for caption, callback in [
            ("Toast lỗi", lambda: self.toast.show_message("Thông báo mẫu", "error")),
            ("Confirm dialog", self._confirm),
            ("Error dialog", self._error),
            ("Progress dialog", self._progress),
            ("Loading overlay", self._overlay),
        ]:
            button = OutlineButton(caption)
            button.clicked.connect(callback)
            layout.addWidget(button)
        self.player = AudioPlayer()
        self.player.error.connect(lambda message: self.toast.show_message(message, "error"))
        layout.addWidget(self.player)
        audio = OutlineButton("Chọn audio để phát")
        audio.clicked.connect(self._audio)
        layout.addWidget(audio)
        self.gallery = ImageGallery()
        self.gallery.error.connect(lambda message: self.toast.show_message(message, "error"))
        layout.addWidget(self.gallery)
        images = OutlineButton("Chọn ảnh để preview")
        images.clicked.connect(self._images)
        layout.addWidget(images)
        layout.addWidget(EmptyState("Chưa có dự án", "Bắt đầu một ý tưởng mới.", "Tạo mới"))
        self.overlay = LoadingOverlay(self)
        self.dialogs: list[QWidget] = []

    def _busy(self, button: PrimaryButton) -> None:
        button.set_loading(True)
        QTimer.singleShot(1200, button, lambda: button.set_loading(False))

    def _show_dialog(self, dialog: QWidget) -> None:
        self.dialogs.append(dialog)
        dialog.finished.connect(lambda: self._release_dialog(dialog))
        dialog.open()

    def _release_dialog(self, dialog: QWidget) -> None:
        self.dialogs.remove(dialog)
        dialog.deleteLater()

    def _confirm(self) -> None:
        dialog = ConfirmDialog("Xác nhận", "Đây là thao tác mẫu trong showcase.", self)
        dialog.accepted.connect(lambda: self.toast.show_message("Đã xác nhận", "success"))
        self._show_dialog(dialog)

    def _error(self) -> None:
        self._show_dialog(ErrorDialog("Thông báo lỗi mẫu, không có traceback.", self))

    def _progress(self) -> None:
        dialog = ProgressDialog(parent=self)
        dialog.set_progress(45, message="Đang xử lý tác vụ mẫu…")
        dialog.cancel_requested.connect(lambda: self.toast.show_message("Đã yêu cầu hủy"))
        self._show_dialog(dialog)

    def _overlay(self) -> None:
        self.overlay.set_loading(True)
        QTimer.singleShot(1200, self.overlay, lambda: self.overlay.set_loading(False))

    def _audio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Chọn audio", "", "Audio (*.wav *.mp3 *.ogg *.flac)")
        if path:
            self.player.set_source(path)

    def _images(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Chọn ảnh", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if paths:
            self.gallery.set_images(paths)

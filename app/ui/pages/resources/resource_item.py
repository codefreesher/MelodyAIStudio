"""One resource row: icon, name/description, status/action, inline progress.

All install/download/repair/remove work happens in
:class:`app.controllers.resource_controller.ResourceController` — this
widget only displays a resource dict and emits intent.
"""

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QVBoxLayout, QWidget

from app.ui.pages.resources.install_progress import InstallProgress

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"
_RESOURCE_ICONS = {
    "ollama": "ollama.svg",
    "ffmpeg": "ffmpeg.svg",
    "python": "python.svg",
    "stable-diffusion": "stable_diffusion.svg",
    "tts-models": "tts.svg",
}


class ResourceItem(QFrame):
    download_requested = Signal()
    open_requested = Signal()
    repair_requested = Signal()
    remove_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, item: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.item = item
        self.setObjectName("resourceItem")
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(12)

        icon = QLabel()
        icon.setObjectName("resourceItemIcon")
        icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_file = _RESOURCE_ICONS.get(item["id"])
        if icon_file and (_ICONS / icon_file).is_file():
            icon.setPixmap(QIcon(str(_ICONS / icon_file)).pixmap(QSize(26, 26)))
        row.addWidget(icon)

        text_column = QVBoxLayout()
        text_column.setSpacing(2)
        name = QLabel(item["name"])
        name.setObjectName("resourceItemName")
        self.description_label = QLabel(item.get("description", ""))
        self.description_label.setObjectName("resourceItemDescription")
        text_column.addWidget(name)
        text_column.addWidget(self.description_label)
        row.addLayout(text_column, 1)

        # Trailing area: status badge/download button (self.trailing), or —
        # while a job is running — an inline progress bar in its place.
        self.trailing = QWidget()
        self.trailing_layout = QVBoxLayout(self.trailing)
        self.trailing_layout.setContentsMargins(0, 0, 0, 0)
        self.trailing_layout.setSpacing(2)
        row.addWidget(self.trailing)

        self.progress = InstallProgress()
        self.progress.cancel_requested.connect(self.cancel_requested.emit)
        self.progress.hide()
        row.addWidget(self.progress, 1)

        self.menu_button: QPushButton | None = None
        self._build_trailing()

    def _build_trailing(self) -> None:
        while self.trailing_layout.count():
            taken = self.trailing_layout.takeAt(0)
            widget = taken.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
            layout = taken.layout()
            if layout:
                while layout.count():
                    sub = layout.takeAt(0).widget()
                    if sub:
                        sub.setParent(None)
                        sub.deleteLater()

        configured = bool(self.item.get("url")) and bool(self.item.get("sha256"))
        if self.item.get("installed"):
            top_row = QHBoxLayout()
            top_row.setSpacing(6)
            badge = QLabel("Đã cài đặt")
            badge.setObjectName("resourceStatusInstalled")
            top_row.addWidget(badge)
            self.menu_button = QPushButton()
            self.menu_button.setObjectName("resourceMenuButton")
            self.menu_button.setIcon(QIcon(str(_ICONS / "more.svg")))
            self.menu_button.setIconSize(QSize(14, 14))
            self.menu_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.menu_button.setToolTip("Thêm hành động")
            self.menu_button.clicked.connect(self._open_menu)
            top_row.addWidget(self.menu_button)
            self.trailing_layout.addLayout(top_row)
            version = self.item.get("version", "")
            if version:
                version_label = QLabel(f"v{version}")
                version_label.setObjectName("resourceStatusVersion")
                version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                self.trailing_layout.addWidget(version_label)
        else:
            self.menu_button = None
            button = QPushButton("Tải xuống" if configured else "Tải chính thức")
            button.setObjectName("resourceDownloadButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            if not configured:
                button.setToolTip("Mở trang tải chính thức của tài nguyên.")
            button.clicked.connect(self.download_requested.emit)
            self.trailing_layout.addWidget(button)

    def _open_menu(self) -> None:
        menu = QMenu(self)
        menu.addAction("Mở thư mục", self.open_requested.emit)
        menu.addAction("Sửa chữa", self.repair_requested.emit)
        menu.addSeparator()
        menu.addAction("Gỡ bỏ", self.remove_requested.emit)
        menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))

    def update_item(self, item: dict) -> None:
        self.item = item
        self._build_trailing()

    def set_downloading(self, active: bool) -> None:
        self.trailing.setVisible(not active)
        self.progress.setVisible(active)
        if active:
            self.progress.set_value(0)

    def set_progress(self, value: int) -> None:
        self.progress.set_value(value)

    def set_busy(self, busy: bool) -> None:
        """Disable interaction while a *different* resource's job is
        running (only one job runs at a time — see ResourceController).
        The item that owns the running job stays interactive so its
        Cancel link keeps working."""
        self.setEnabled(not busy or self.progress.isVisible())

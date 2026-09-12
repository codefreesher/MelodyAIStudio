"""Resource catalog presentation — a compact list, not one giant card per
resource. All install/download/repair/remove work lives in
:class:`app.controllers.resource_controller.ResourceController`; this page
only renders resource dicts (from :class:`app.services.resource_service.ResourceService`)
and relays user intent.
"""

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.pages.resources.resource_item import ResourceItem
from app.ui.widgets.toast import Toast

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"


class ResourcePage(QWidget):
    action = Signal(object, str)
    import_requested = Signal()
    reload_requested = Signal()
    cancel_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("resourcePage")
        self._items: dict[str, ResourceItem] = {}
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)

        # No max-width cap: on the real (sidebar-adjacent) window this page
        # actually renders in, a fixed ~680px column left most of the width
        # as dead space — matches how the History list page fills its column.
        content = QWidget()
        content.setObjectName("resourceContent")
        column = QVBoxLayout(content)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(12)
        root.addWidget(content)

        header = QHBoxLayout()
        header.setSpacing(10)
        icon = QLabel()
        icon.setObjectName("resourceHeadingIcon")
        icon.setFixedSize(32, 32)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setPixmap(QIcon(str(_ICONS / "download.svg")).pixmap(QSize(18, 18)))
        heading = QLabel("Tải tài nguyên")
        heading.setObjectName("resourceHeading")
        header.addWidget(icon)
        header.addWidget(heading)
        header.addStretch(1)
        self.menu_button = QPushButton()
        self.menu_button.setObjectName("resourceMenuButton")
        self.menu_button.setIcon(QIcon(str(_ICONS / "more.svg")))
        self.menu_button.setIconSize(QSize(14, 14))
        self.menu_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_button.setToolTip("Quản lý manifest")
        self.menu_button.clicked.connect(self._open_menu)
        header.addWidget(self.menu_button)
        column.addLayout(header)

        self.toast = Toast(plain=True)
        column.addWidget(self.toast)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("resourceScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setWidget(self.list_container)
        column.addWidget(self.scroll, 1)

    def _open_menu(self) -> None:
        menu = QMenu(self)
        menu.addAction("Nhập manifest…", self.import_requested.emit)
        menu.addAction("Tải lại manifest", self.reload_requested.emit)
        menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))

    def show_resources(self, resources: list[dict]) -> None:
        while self.list_layout.count():
            taken = self.list_layout.takeAt(0)
            widget = taken.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        self._items.clear()
        for data in resources:
            row = ResourceItem(data)
            row.download_requested.connect(lambda _=False, d=data: self.action.emit(d, "install"))
            row.open_requested.connect(lambda _=False, d=data: self.action.emit(d, "open"))
            row.repair_requested.connect(lambda _=False, d=data: self.action.emit(d, "repair"))
            row.remove_requested.connect(lambda _=False, d=data: self.action.emit(d, "remove"))
            row.cancel_requested.connect(self.cancel_requested)
            self.list_layout.addWidget(row)
            self._items[data["id"]] = row
        self.list_layout.addStretch(1)

    def get_item(self, item_id: str) -> ResourceItem | None:
        return self._items.get(item_id)

    def set_busy(self, busy: bool) -> None:
        for row in self._items.values():
            row.set_busy(busy)

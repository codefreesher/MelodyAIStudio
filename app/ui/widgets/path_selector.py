"""A folder-location row: icon, name/description, elided path, Mở/Đổi.

Clicking the path copies it to the clipboard (spec: "có thể click để copy").
"""

from pathlib import Path

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QFontMetrics, QIcon
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.widgets.buttons import OutlineButton

_ICONS = Path(__file__).resolve().parents[2] / "assets/icons"


class PathSelector(QWidget):
    open_requested = Signal()
    change_requested = Signal()

    def __init__(
        self, icon_file: str, title: str, description: str = "", parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._full_path = ""
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)

        header = QHBoxLayout()
        header.setSpacing(10)
        if icon_file:
            icon = QLabel()
            icon.setFixedSize(22, 22)
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            path = _ICONS / icon_file
            if path.is_file():
                icon.setPixmap(QIcon(str(path)).pixmap(QSize(16, 16)))
            header.addWidget(icon)
        title_label = QLabel(title)
        title_label.setObjectName("pathSelectorTitle")
        header.addWidget(title_label)
        header.addStretch(1)
        column.addLayout(header)

        if description:
            description_label = QLabel(description)
            description_label.setObjectName("pathSelectorDescription")
            description_label.setWordWrap(True)
            column.addWidget(description_label)

        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        self.path_label = QLabel("")
        self.path_label.setObjectName("pathSelectorPath")
        self.path_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.path_label.installEventFilter(self)
        path_row.addWidget(self.path_label, 1)
        self.open_button = OutlineButton("Mở")
        self.open_button.setObjectName("pathSelectorButton")
        self.open_button.clicked.connect(self.open_requested.emit)
        path_row.addWidget(self.open_button)
        self.change_button = OutlineButton("Đổi")
        self.change_button.setObjectName("pathSelectorButton")
        self.change_button.clicked.connect(self.change_requested.emit)
        path_row.addWidget(self.change_button)
        column.addLayout(path_row)

    def set_path(self, path: str) -> None:
        self._full_path = path
        self.path_label.setToolTip(path)
        metrics = QFontMetrics(self.path_label.font())
        self.path_label.setText(metrics.elidedText(path, Qt.TextElideMode.ElideMiddle, 460))

    def eventFilter(self, watched, event) -> bool:  # noqa: ANN001 - Qt signature
        if watched is self.path_label and event.type() == QEvent.Type.MouseButtonPress and self._full_path:
            QApplication.clipboard().setText(self._full_path)
        return super().eventFilter(watched, event)

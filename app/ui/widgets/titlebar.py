"""Optional title bar for a caller-owned window; no frameless policy imposed."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QStyle, QWidget

from app.ui.widgets.buttons import IconButton

_DEFAULT_ICON = Path(__file__).resolve().parents[2] / "assets/images/logo-mark.svg"


class TitleBar(QFrame):
    def __init__(
        self,
        title: str = "MelodyAI",
        subtitle: str = "",
        icon_path: Path | str | None = _DEFAULT_ICON,
        parent: QWidget | None = None,
        *,
        show_controls: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setProperty("role", "surface")
        self._icon_path = icon_path
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 6, 8, 6)
        row.setSpacing(8)
        self.icon_label = QLabel()
        row.addWidget(self.icon_label)
        self.title_label = QLabel()
        self.title_label.setObjectName("titleBarName")
        row.addWidget(self.title_label)
        self.separator_label = QLabel("|")
        self.separator_label.setObjectName("titleBarSeparator")
        row.addWidget(self.separator_label)
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("titleBarSubtitle")
        row.addWidget(self.subtitle_label)
        self.set_titles(title, subtitle)
        row.addStretch(1)
        controls = (
            (QStyle.StandardPixmap.SP_TitleBarMinButton, "Thu nhỏ", lambda: self.window().showMinimized(), "min"),
            (QStyle.StandardPixmap.SP_TitleBarMaxButton, "Phóng to / Khôi phục", self.toggle_maximized, "max"),
            (QStyle.StandardPixmap.SP_TitleBarCloseButton, "Đóng", lambda: self.window().close(), "close"),
        )
        for icon, caption, callback, kind in controls if show_controls else ():
            button = IconButton(self.style().standardIcon(icon), caption)
            button.setProperty("titleBarButton", kind)
            button.clicked.connect(callback)
            row.addWidget(button)

    def set_titles(self, title: str, subtitle: str = "", show_icon: bool = True) -> None:
        """Swap the bar's text/branding in place — lets an individual page
        (e.g. Login's "02. Đăng nhập") own its own bar without a second
        window or a rebuilt widget tree."""
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)
        self.subtitle_label.setVisible(bool(subtitle))
        self.separator_label.setVisible(bool(subtitle))
        self.icon_label.setVisible(show_icon and bool(self._icon_path) and Path(self._icon_path).is_file())
        if self.icon_label.isVisible() and self.icon_label.pixmap().isNull():
            self.icon_label.setPixmap(QIcon(str(self._icon_path)).pixmap(QSize(22, 22)))

    def set_compact(self, compact: bool) -> None:
        """Toggle the slim, low-chrome bar style used by pages like Login."""
        self.setProperty("compact", compact)
        self.style().unpolish(self)
        self.style().polish(self)

    def toggle_maximized(self) -> None:
        window = self.window()
        window.showNormal() if window.isMaximized() else window.showMaximized()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.window().windowHandle():
            self.window().windowHandle().startSystemMove()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximized()
        super().mouseDoubleClickEvent(event)

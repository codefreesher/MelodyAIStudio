"""Non-modal inline notification with timeout and explicit dismissal."""

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QStyle, QWidget

from app.ui.widgets.buttons import IconButton


class Toast(QFrame):
    dismissed = Signal()

    def __init__(self, parent: QWidget | None = None, *, plain: bool = False) -> None:
        super().__init__(parent)
        self._plain = plain
        self.setProperty("role", "inlineMessage" if plain else "card")
        row = QHBoxLayout(self)
        if plain:
            row.setContentsMargins(0, 6, 0, 10)
        self.message = QLabel()
        self.message.setWordWrap(True)
        row.addWidget(self.message, 1)
        close = IconButton(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton), "Đóng thông báo"
        )
        close.clicked.connect(self.dismiss)
        row.addWidget(close)
        close.setVisible(not plain)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.dismiss)
        self.hide()

    def show_message(self, message: str, kind: str = "info", duration_ms: int = 4000) -> None:
        labels = {"info": "Thông tin", "success": "Thành công", "error": "Lỗi", "warning": "Lưu ý"}
        if kind not in labels:
            raise ValueError(f"Unknown toast kind: {kind}")
        self.message.setText(message if self._plain else f"{labels[kind]}: {message}")
        self.message.setAccessibleName(self.message.text())
        self.message.setProperty("kind", kind)
        self.message.style().unpolish(self.message)
        self.message.style().polish(self.message)
        self.message.update()
        self.timer.stop()
        self.show()
        if duration_ms > 0:
            self.timer.start(duration_ms)

    def dismiss(self) -> None:
        self.timer.stop()
        self.hide()
        self.dismissed.emit()

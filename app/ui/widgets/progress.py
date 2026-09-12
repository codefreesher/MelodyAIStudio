"""Progress presentation only; cancellation is a request to the task owner."""

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtWidgets import QDialog, QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget

from app.ui.widgets.buttons import OutlineButton


class ProgressDialog(QDialog):
    cancel_requested = Signal()

    def __init__(self, title: str = "Đang xử lý", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(420, 160)
        layout = QVBoxLayout(self)
        self.message = QLabel(title)
        self.message.setWordWrap(True)
        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        self.cancel_button = OutlineButton("Hủy")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.message)
        layout.addWidget(self.bar)
        layout.addWidget(self.cancel_button)
        self._cancel_sent = False

    def set_progress(self, value: int, total: int = 100, message: str = "") -> None:
        self.bar.setRange(0, max(0, total))
        self.bar.setValue(max(0, min(value, total)))
        if message:
            self.message.setText(message)

    def reject(self) -> None:
        if not self._cancel_sent:
            self._cancel_sent = True
            self.cancel_requested.emit()
        super().reject()

    def showEvent(self, event: QEvent) -> None:
        self._cancel_sent = False
        super().showEvent(event)


class LoadingOverlay(QFrame):
    """Parent-sized overlay blocks pointer input and takes keyboard focus."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setProperty("role", "surface")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.layout_box = QVBoxLayout(self)
        self.layout_box.addStretch()
        self.label = QLabel("Đang xử lý…")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        self.layout_box.addWidget(self.label)
        self.layout_box.addWidget(self.bar)
        self.layout_box.addStretch()
        parent.installEventFilter(self)
        self.hide()

    def set_loading(self, loading: bool, message: str = "Đang xử lý…") -> None:
        self.label.setText(message)
        if loading:
            self.setGeometry(self.parentWidget().rect())
            self.show()
            self.raise_()
            self.setFocus()
        else:
            self.hide()

    def focusNextPrevChild(self, next: bool) -> bool:
        return False

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.parentWidget() and event.type() == QEvent.Type.Resize:
            self.setGeometry(self.parentWidget().rect())
        return super().eventFilter(watched, event)

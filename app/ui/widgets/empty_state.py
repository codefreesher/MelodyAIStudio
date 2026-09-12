"""Reusable empty content with optional caller-owned action."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from app.ui.widgets.buttons import PrimaryButton


class EmptyState(QFrame):
    action_requested = Signal()

    def __init__(
        self,
        title: str = "Chưa có nội dung",
        description: str = "",
        action_text: str = "",
        icon: QIcon | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addStretch()
        if icon is not None:
            image = QLabel()
            image.setPixmap(icon.pixmap(48, 48))
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(image)
        for text, role in ((title, "subtitle"), (description, "muted")):
            label = QLabel(text)
            label.setProperty("role", role)
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        self.action_button = PrimaryButton(action_text)
        self.action_button.setVisible(bool(action_text))
        self.action_button.clicked.connect(self.action_requested.emit)
        layout.addWidget(self.action_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

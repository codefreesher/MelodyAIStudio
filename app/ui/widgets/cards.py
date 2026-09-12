"""Cards expose actions through signals; they never fetch data."""

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.widgets.buttons import OutlineButton, PrimaryButton


class BaseCard(QFrame):
    def __init__(self, title: str, description: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("role", "card")
        self.content = QVBoxLayout(self)
        self.content.setContentsMargins(18, 18, 18, 18)
        self.content.setSpacing(10)
        self.title_label = QLabel(title)
        self.title_label.setProperty("role", "subtitle")
        self.description_label = QLabel(description)
        self.description_label.setProperty("role", "muted")
        for label in (self.title_label, self.description_label):
            label.setWordWrap(True)
            self.content.addWidget(label)


class FeatureCard(BaseCard):
    clicked = Signal()

    def __init__(
        self, title: str, description: str = "", icon: QIcon | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(title, description, parent)
        self.button = PrimaryButton(title)
        if icon is not None:
            self.button.setIcon(icon)
        self.content.addWidget(self.button)
        self.button.clicked.connect(self.clicked.emit)

    def set_loading(self, loading: bool) -> None:
        self.button.set_loading(loading)


class ProjectCard(FeatureCard):
    def __init__(
        self, title: str, project_type: str = "", created_at: str = "", parent: QWidget | None = None
    ) -> None:
        super().__init__(title, f"{project_type} · {created_at}", parent=parent)
        self.thumbnail = QLabel()
        self.thumbnail.setMaximumHeight(140)
        self.content.insertWidget(0, self.thumbnail)


class StatCard(BaseCard):
    def __init__(
        self, title: str, value: str = "0", description: str = "", parent: QWidget | None = None
    ) -> None:
        super().__init__(title, description, parent)
        self.value_label = QLabel(value)
        self.value_label.setProperty("role", "heading")
        self.content.insertWidget(1, self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class ProviderCard(BaseCard):
    test_requested = Signal()
    configure_requested = Signal()

    def __init__(self, title: str, description: str = "", parent: QWidget | None = None) -> None:
        super().__init__(title, description, parent)
        self.status_label = QLabel("Chưa kết nối")
        self.content.addWidget(self.status_label)
        row = QHBoxLayout()
        self.test_button = OutlineButton("Kiểm tra")
        self.configure_button = OutlineButton("Cấu hình")
        row.addWidget(self.test_button)
        row.addWidget(self.configure_button)
        self.content.addLayout(row)
        self.test_button.clicked.connect(self.test_requested.emit)
        self.configure_button.clicked.connect(self.configure_requested.emit)

    def set_status(self, status: str) -> None:
        self.status_label.setText(status)

    def set_loading(self, loading: bool) -> None:
        self.test_button.set_loading(loading)
        self.configure_button.set_loading(loading)


class ResourceCard(BaseCard):
    action_requested = Signal(str)

    def __init__(
        self, title: str, description: str = "", version: str = "", parent: QWidget | None = None
    ) -> None:
        super().__init__(title, description, parent)
        self.status_label = QLabel(f"{version} · Chưa cài đặt")
        self.content.addWidget(self.status_label)
        self.actions: dict[str, OutlineButton] = {}
        # Vertical actions stay usable in narrow cards and at larger font sizes.
        for key, caption in [
            ("download", "Tải xuống"),
            ("install", "Cài đặt"),
            ("repair", "Sửa chữa"),
            ("open", "Mở thư mục"),
            ("remove", "Gỡ bỏ"),
        ]:
            button = OutlineButton(caption)
            button.clicked.connect(lambda checked=False, action=key: self.action_requested.emit(action))
            self.actions[key] = button
            self.content.addWidget(button)

    def set_status(self, status: str) -> None:
        self.status_label.setText(status)

    def set_loading(self, loading: bool) -> None:
        for button in self.actions.values():
            button.set_loading(loading)

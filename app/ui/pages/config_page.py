"""Shared provider configuration editor; controller supplies all data."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QFormLayout, QHBoxLayout, QLabel, QTabBar, QVBoxLayout, QWidget

from app.ui.widgets.buttons import OutlineButton, PrimaryButton
from app.ui.widgets.inputs import PasswordInput, TextInput
from app.ui.widgets.toast import Toast


class ConfigPage(QWidget):
    selected = Signal(str)
    action = Signal(str, str, dict)

    def __init__(self, title: str, names: list[str], fields: dict[str, str], actions: dict[str, str]) -> None:
        super().__init__()
        self.names, self.fields = names, {}
        root = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setProperty("role", "heading")
        root.addWidget(heading)
        self.toast = Toast()
        root.addWidget(self.toast)
        self.tabs = QTabBar()
        for name in names:
            self.tabs.addTab(name)
        root.addWidget(self.tabs)
        form = QFormLayout()
        for key, caption in fields.items():
            if key == "enabled":
                field = QCheckBox()
            elif key == "api_key":
                field = PasswordInput("API Key")
            else:
                field = TextInput(caption)
            self.fields[key] = field
            form.addRow(caption, field)
        root.addLayout(form)
        self.buttons = {}
        row = QHBoxLayout()
        for action, caption in actions.items():
            button = PrimaryButton(caption) if action == "save" else OutlineButton(caption)
            button.clicked.connect(
                lambda checked=False, key=action: self.action.emit(key, self.current(), self.values())
            )
            self.buttons[action] = button
            row.addWidget(button)
        root.addLayout(row)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        root.addStretch()
        self.tabs.currentChanged.connect(lambda: self.selected.emit(self.current()))

    def current(self) -> str:
        return self.names[self.tabs.currentIndex()]

    def values(self) -> dict:
        return {
            key: field.isChecked() if isinstance(field, QCheckBox) else field.text()
            for key, field in self.fields.items()
        }

    def set_values(self, data: dict) -> None:
        for key, field in self.fields.items():
            if isinstance(field, QCheckBox):
                field.setChecked(bool(data.get(key, False)))
            else:
                field.setText(str(data.get(key, "")))

    def set_loading(self, loading: bool) -> None:
        self.tabs.setEnabled(not loading)
        for button in self.buttons.values():
            button.setEnabled(not loading)
        for field in self.fields.values():
            field.setEnabled(not loading)

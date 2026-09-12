"""Theme-driven buttons with reversible busy state."""

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QWidget


class ThemedButton(QPushButton):
    role = "secondary"

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setProperty("role", self.role)
        self._loading = False
        self._saved_text = text
        self._saved_enabled = True

    def set_loading(self, loading: bool, text: str = "Đang xử lý…") -> None:
        if loading == self._loading:
            return
        self._loading = loading
        if loading:
            self._saved_text = self.text()
            self._saved_enabled = self.isEnabled()
            self.setText(text)
            self.setEnabled(False)
        else:
            self.setText(self._saved_text)
            self.setEnabled(self._saved_enabled)

    @property
    def is_loading(self) -> bool:
        return self._loading


class PrimaryButton(ThemedButton):
    role = "primary"


class SecondaryButton(ThemedButton):
    role = "secondary"


class OutlineButton(ThemedButton):
    role = "outline"


class DangerButton(ThemedButton):
    role = "danger"


class IconButton(ThemedButton):
    role = "icon"

    def __init__(self, icon: QIcon, label: str, parent: QWidget | None = None) -> None:
        super().__init__("", parent)
        self.setIcon(icon)
        self.setIconSize(QSize(20, 20))
        self.setAccessibleName(label)
        self.setToolTip(label)

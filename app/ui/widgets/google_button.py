"""Google sign-in button with the real multi-colour G mark."""

from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget

from app.ui.widgets.buttons import OutlineButton

_ICON = Path(__file__).resolve().parents[2] / "assets/icons/google.svg"


class GoogleButton(OutlineButton):
    def __init__(self, text: str = "Đăng nhập với Google", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("googleButton")
        if _ICON.is_file():
            self.setIcon(QIcon(str(_ICON)))
            self.setIconSize(QSize(18, 18))

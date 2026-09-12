"""Password input with a leading lock icon, layered on the shared field.

Kept separate from :class:`app.ui.widgets.inputs.PasswordInput` (used by
several other pages) so this compact, icon-led styling only applies where a
caller opts into it — e.g. the login form, which has no caption labels.
"""

from pathlib import Path

from PySide6.QtWidgets import QWidget

from app.ui.widgets.field_icons import FieldIcons
from app.ui.widgets.inputs import PasswordInput as BasePasswordInput

_ICONS = Path(__file__).resolve().parents[2] / "assets/icons"


class LoginPasswordInput(BasePasswordInput):
    def __init__(self, placeholder: str = "Mật khẩu", parent: QWidget | None = None) -> None:
        super().__init__(placeholder, parent)
        icon_path = _ICONS / "lock.svg"
        if icon_path.is_file():
            self._field_icons = FieldIcons(self, icon_path, self.visibility_action)

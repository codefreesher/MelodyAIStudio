"""Leading-icon text input for compact forms that skip a caption label."""

from pathlib import Path

from PySide6.QtWidgets import QWidget

from app.ui.widgets.field_icons import FieldIcons
from app.ui.widgets.inputs import TextInput

_ICONS = Path(__file__).resolve().parents[2] / "assets/icons"


class AppInput(TextInput):
    """A :class:`TextInput` with a small decorative leading icon (e.g. a user
    glyph) in place of a caption label above the field."""

    def __init__(self, placeholder: str = "", icon_file: str = "user.svg", parent: QWidget | None = None) -> None:
        super().__init__(placeholder, parent)
        icon_path = _ICONS / icon_file
        if icon_path.is_file():
            self._field_icons = FieldIcons(self, icon_path)

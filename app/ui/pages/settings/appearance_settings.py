"""Appearance tab: theme mode cards, accent swatches, live preview — no raw
theme id or hex text field exposed to the user (see spec: pink_light/
pink_dark stay internal identifiers only)."""

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QButtonGroup, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.widgets.setting_card import SettingCard
from app.ui.widgets.theme_selector import ThemeSelector

# A small curated palette rather than a free-text hex field.
_ACCENTS = (
    ("#FF4F9A", "Hồng Melody"),
    ("#8B5CF6", "Tím Lavender"),
    ("#3289D7", "Xanh biển"),
    ("#18AD72", "Xanh lá"),
)


class _AccentSwatch(QAbstractButton):
    def __init__(self, color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.color = color
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(28, 28)
        self.setToolTip(color)

    def paintEvent(self, event) -> None:  # noqa: ANN001, ARG002 - Qt signature
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.color))
        painter.drawEllipse(3, 3, 22, 22)
        if self.isChecked():
            painter.setPen(QPen(QColor(self.color), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(0, 0, 27, 27)
            pen = QPen(QColor("#FFFFFF"), 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(9, 14, 12, 17)
            painter.drawLine(12, 17, 19, 9)


class _PreviewCard(QFrame):
    """A hand-painted sample (not the real live theme) so picking a mode/
    accent doesn't have to re-theme the whole app just to preview it."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("appearancePreview")
        self._accent = "#FF4F9A"
        self.setMinimumHeight(84)

    def set_accent(self, color: str) -> None:
        self._accent = color
        self.update()

    def paintEvent(self, event) -> None:  # noqa: ANN001, ARG002 - Qt signature
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#FFF9FB"))
        painter.drawRoundedRect(self.rect(), 10, 10)

        title_font = QFont(self.font())
        title_font.setBold(True)
        title_font.setPointSize(11)
        painter.setFont(title_font)
        painter.setPen(QColor("#29252A"))
        painter.drawText(16, 26, "MelodyAI")

        small_font = QFont(self.font())
        small_font.setPointSize(9)
        small_font.setBold(True)
        painter.setFont(small_font)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self._accent))
        painter.drawRoundedRect(16, 44, 90, 26, 7, 7)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(QRectF(16, 44, 90, 26), Qt.AlignmentFlag.AlignCenter, "Button")

        input_width = max(60, self.width() - 134)
        painter.setPen(QPen(QColor("#EEDDE5"), 1))
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawRoundedRect(118, 44, input_width, 26, 7, 7)
        painter.setPen(QColor("#81767D"))
        painter.drawText(QRectF(130, 44, input_width - 20, 26), Qt.AlignmentFlag.AlignVCenter, "Input")


class AppearanceSettings(QWidget):
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(16)

        mode_card = SettingCard("Chế độ")
        self.mode_selector = ThemeSelector()
        self.mode_selector.changed.connect(lambda _value: self.changed.emit())
        mode_card.add_row(self.mode_selector)
        column.addWidget(mode_card)

        accent_card = SettingCard("Màu chủ đạo")
        self.accent_label = QLabel()
        self.accent_label.setObjectName("accentSelectedLabel")
        accent_card.add_row(self.accent_label)

        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(10)
        self.swatch_group = QButtonGroup(self)
        self.swatch_group.setExclusive(True)
        self.swatches: dict[str, _AccentSwatch] = {}
        self._accent_names: dict[str, str] = dict(_ACCENTS)
        for color, name in _ACCENTS:
            swatch = _AccentSwatch(color)
            swatch.clicked.connect(lambda _checked=False, c=color: self._select_accent(c))
            self.swatch_group.addButton(swatch)
            self.swatches[color] = swatch
            swatch_row.addWidget(swatch)
        swatch_row.addStretch(1)
        accent_card.add_row_layout(swatch_row)
        column.addWidget(accent_card)

        preview_card = SettingCard("Xem trước")
        self.preview = _PreviewCard()
        preview_card.add_row(self.preview)
        column.addWidget(preview_card)

        self._select_accent(_ACCENTS[0][0], emit=False)

    def _select_accent(self, color: str, emit: bool = True) -> None:
        swatch = self.swatches.get(color)
        if swatch:
            swatch.setChecked(True)
        name = self._accent_names.get(color, color)
        self.accent_label.setText(f"●  {name}   {color}")
        self.accent_label.setStyleSheet(f"color: {color};")
        self.preview.set_accent(color)
        if emit:
            self.changed.emit()

    def values(self) -> dict:
        return {"theme": self.mode_selector.value(), "accent": self.swatch_group.checkedButton().color}

    def set_values(self, data: dict) -> None:
        self.mode_selector.set_value(data.get("theme", "pink_light"))
        accent = data.get("accent", _ACCENTS[0][0])
        if accent not in self.swatches:
            accent = _ACCENTS[0][0]
        self._select_accent(accent, emit=False)

"""Data-driven navigation; the caller owns page routing."""

from pathlib import Path

from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.buttons import IconButton, ThemedButton

_DASHBOARD_LOGO = Path(__file__).resolve().parents[2] / "assets/images/logo-dashboard.png"
_NAVIGATION_SYMBOLS = {
    "dashboard": "⌂",
    "music": "♫",
    "lyric": "✎",
    "audio": "◉",
    "image": "▧",
    "history": "↶",
    "resources": "◇",
    "online_config": "◎",
    "offline_config": "⬡",
    "updates": "⇩",
    "settings": "⚙",
}


def _navigation_icon(symbol: str) -> QIcon:
    pixmap = QPixmap(28, 28)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor("#C92E72"))
    font = QFont()
    font.setPixelSize(25)
    font.setWeight(QFont.Weight.DemiBold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, symbol)
    painter.end()
    return QIcon(pixmap)


class SidebarItem(ThemedButton):
    role = "navigation"

    def __init__(self, text: str, icon: QIcon | None = None, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setObjectName("sidebarItem")
        self.setIconSize(QSize(22, 22))
        if icon is not None:
            self.setIcon(icon)
        self._hovered = False
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setColor(QColor(255, 71, 150, 105))
        self._shadow.setOffset(0, 3)
        self._shadow.setBlurRadius(0)
        self.setGraphicsEffect(self._shadow)
        self._shadow_animation = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._shadow_animation.setDuration(180)
        self._shadow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._icon_animation = QPropertyAnimation(self, b"iconSize", self)
        self._icon_animation.setDuration(160)
        self._icon_animation.setEasingCurve(QEasingCurve.Type.OutBack)
        self.toggled.connect(self._animate_state)

    def event(self, event: QEvent) -> bool:
        result = super().event(event)
        if hasattr(self, "_shadow_animation"):
            if event.type() == QEvent.Type.Enter:
                self._hovered = True
                self._animate_state()
            elif event.type() == QEvent.Type.Leave:
                self._hovered = False
                self._animate_state()
        return result

    def _animate_state(self) -> None:
        active = self.isChecked()
        self._shadow_animation.stop()
        self._shadow_animation.setStartValue(self._shadow.blurRadius())
        self._shadow_animation.setEndValue(18 if active else (10 if self._hovered else 0))
        self._shadow_animation.start()
        self._icon_animation.stop()
        self._icon_animation.setStartValue(self.iconSize())
        size = 26 if active else (24 if self._hovered else 22)
        self._icon_animation.setEndValue(QSize(size, size))
        self._icon_animation.start()


class Sidebar(QFrame):
    page_requested = Signal(str)
    profile_requested = Signal()
    logout_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("role", "sidebar")
        self.setFixedWidth(210)
        self.layout_box = QVBoxLayout(self)
        self.layout_box.setContentsMargins(12, 20, 12, 20)
        self.logo = QLabel()
        self.logo.setAccessibleName("MelodyAI — AI Creative Studio")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        logo = QPixmap(str(_DASHBOARD_LOGO))
        if logo.isNull():
            self.logo.setText("MelodyAI")
        else:
            preview = logo.scaled(
                360,
                120,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            preview.setDevicePixelRatio(2)
            self.logo.setPixmap(preview)
            self.logo.setFixedSize(180, 60)
        self.layout_box.addWidget(self.logo)
        self.items: dict[str, SidebarItem] = {}
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        area = QScrollArea()
        area.setWidgetResizable(True)
        navigation = QWidget()
        self.navigation_layout = QVBoxLayout(navigation)
        self.navigation_layout.setContentsMargins(0, 0, 0, 0)
        self.navigation_layout.addStretch()
        area.setWidget(navigation)
        self.layout_box.addWidget(area, 1)
        self.avatar = QLabel("M")
        self.avatar.setProperty("role", "avatar")
        self.avatar.setFixedSize(32, 32)
        profile_row = QHBoxLayout()
        profile_row.setSpacing(8)
        profile_row.addWidget(self.avatar)
        self.profile = QLabel("Khách\nChưa đăng nhập")
        self.profile.setObjectName("sidebarProfileText")
        self.profile.setWordWrap(True)
        profile_row.addWidget(self.profile, 1)
        self.profile_button = IconButton(_navigation_icon("↪"), "Đăng xuất")
        self.profile_button.setObjectName("sidebarProfileButton")
        self.profile_button.clicked.connect(self.logout_requested.emit)
        profile_row.addWidget(self.profile_button)
        self.layout_box.addLayout(profile_row)

    def add_item(self, key: str, text: str, icon: QIcon | None = None) -> SidebarItem:
        if key in self.items:
            raise ValueError(f"Duplicate navigation key: {key}")
        item = SidebarItem(text, icon or _navigation_icon(_NAVIGATION_SYMBOLS.get(key, "•")), self)
        self.items[key] = item
        self.group.addButton(item)
        self.navigation_layout.insertWidget(self.navigation_layout.count() - 1, item)
        item.clicked.connect(lambda: self.page_requested.emit(key))
        return item

    def set_current(self, key: str) -> None:
        self.items[key].setChecked(True)

    def set_profile(self, username: str, plan: str, editable: bool = True) -> None:
        self.avatar.setText(username[:1].upper())
        self.profile.setText(f"{username}\n{plan}")
        self.profile_button.setEnabled(True)

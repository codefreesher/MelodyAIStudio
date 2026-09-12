"""Keyboard-accessible action card with subtle animated shadow."""

from pathlib import Path

from PySide6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QSize, Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.widgets.buttons import ThemedButton

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"


class StartupCard(ThemedButton):
    def __init__(
        self, title: str, description: str, primary: bool = False, parent: QWidget | None = None
    ) -> None:
        super().__init__("", parent)
        variant = "login" if primary else "activation"
        self.setObjectName("startupAction")
        self.setAutoDefault(False)
        self.setDefault(False)
        self.setProperty("variant", variant)
        self.setAccessibleName(f"{title}. {description}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(270, 178)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(0)
        icon_file = "person-white.svg" if primary else "key.png"
        arrow_file = "arrow-right-white.svg" if primary else "arrow-right.svg"
        self.icon_avatar = self._avatar("cardIconAvatar", variant, icon_file, 44, 22)
        header.addWidget(self.icon_avatar)
        header.addStretch(1)
        self.arrow_avatar = self._avatar("cardArrowAvatar", variant, arrow_file, 32, 16)
        header.addWidget(self.arrow_avatar)
        layout.addLayout(header)
        layout.addSpacing(16)

        for text, name in ((title, "actionTitle"), (description, "actionDescription")):
            label = QLabel(text)
            label.setObjectName(name)
            label.setWordWrap(True)
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            layout.addWidget(label)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setColor(QColor(147, 55, 96, 26))
        self.shadow.setOffset(0, 3)
        self.shadow.setBlurRadius(12)
        self.setGraphicsEffect(self.shadow)
        self.animation = QPropertyAnimation(self.shadow, b"blurRadius", self)
        self.animation.setDuration(160)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hovered = False
        self.setProperty("keyboardFocus", False)
        self.pressed.connect(self._update_shadow)
        self.released.connect(self._update_shadow)

    @staticmethod
    def _avatar(object_name: str, variant: str, icon_file: str, size: int, icon_size: int) -> QLabel:
        avatar = QLabel()
        avatar.setObjectName(object_name)
        avatar.setProperty("variant", variant)
        avatar.setFixedSize(size, size)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        icon_path = _ICONS / icon_file
        if icon_path.is_file():
            avatar.setPixmap(QIcon(str(icon_path)).pixmap(QSize(icon_size, icon_size)))
        return avatar

    def event(self, event: QEvent) -> bool:
        result = super().event(event)
        if hasattr(self, "animation"):
            kind = event.type()
            if kind == QEvent.Type.Enter:
                self._hovered = True
            elif kind == QEvent.Type.Leave:
                self._hovered = False
            if kind in (QEvent.Type.FocusIn, QEvent.Type.FocusOut):
                keyboard_focus = kind == QEvent.Type.FocusIn and event.reason() in (
                    Qt.FocusReason.TabFocusReason,
                    Qt.FocusReason.BacktabFocusReason,
                    Qt.FocusReason.ShortcutFocusReason,
                )
                self.setProperty("keyboardFocus", keyboard_focus)
                self.style().unpolish(self)
                self.style().polish(self)
                self.update()
            if kind in (
                QEvent.Type.Enter,
                QEvent.Type.Leave,
                QEvent.Type.FocusIn,
                QEvent.Type.FocusOut,
                QEvent.Type.EnabledChange,
            ):
                self._update_shadow()
        return result

    def _update_shadow(self) -> None:
        target = 12
        if self.isEnabled():
            if self.isDown():
                target = 6
            elif self._hovered or self.property("keyboardFocus"):
                target = 24
        self._animate(target)

    def _animate(self, target: float) -> None:
        self.animation.stop()
        self.animation.setStartValue(self.shadow.blurRadius())
        self.animation.setEndValue(target)
        self.animation.start()

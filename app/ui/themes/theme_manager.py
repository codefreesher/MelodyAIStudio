"""Apply a consistent application palette, typography and QSS."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QWidget

from app.ui.themes.variables import FONT_FAMILIES, PINK_LIGHT, RADII, TYPOGRAPHY


class ThemeManager:
    """Own theme application; no settings persistence or page dependencies."""

    def __init__(self, application: QApplication) -> None:
        self.application = application
        self.current_theme: str | None = None

    def apply(self, theme: str = "pink_light", accent: str | None = None) -> None:
        if theme not in ("pink_light", "pink_dark", "system"):
            raise ValueError(f"Unsupported theme: {theme}")
        stylesheet = (
            Path(__file__)
            .with_name("pink_light.qss")
            .read_text(
                encoding="utf-8",
            )
        )
        stylesheet += "\n" + (
            Path(__file__).resolve().parents[1] / "pages/startup/startup_styles.qss"
        ).read_text(encoding="utf-8")
        stylesheet += "\n" + (Path(__file__).resolve().parents[1] / "pages/login/login_styles.qss").read_text(
            encoding="utf-8"
        )
        stylesheet += "\n" + (
            Path(__file__).resolve().parents[1] / "pages/dashboard/dashboard_styles.qss"
        ).read_text(encoding="utf-8")
        stylesheet += "\n" + (Path(__file__).resolve().parents[1] / "pages/music/music_styles.qss").read_text(
            encoding="utf-8"
        )
        stylesheet += "\n" + (Path(__file__).resolve().parents[1] / "pages/lyric/lyric_styles.qss").read_text(
            encoding="utf-8"
        )
        stylesheet += "\n" + (Path(__file__).resolve().parents[1] / "pages/audio/audio_styles.qss").read_text(
            encoding="utf-8"
        )
        stylesheet += "\n" + (Path(__file__).resolve().parents[1] / "pages/image/image_styles.qss").read_text(
            encoding="utf-8"
        )
        stylesheet += "\n" + (Path(__file__).resolve().parents[1] / "pages/history/history_styles.qss").read_text(
            encoding="utf-8"
        )
        stylesheet += "\n" + (
            Path(__file__).resolve().parents[1] / "pages/resources/resources_styles.qss"
        ).read_text(encoding="utf-8")
        stylesheet += "\n" + (
            Path(__file__).resolve().parents[1] / "pages/online_config/online_config_styles.qss"
        ).read_text(encoding="utf-8")
        stylesheet += "\n" + (
            Path(__file__).resolve().parents[1] / "pages/offline_config/offline_config_styles.qss"
        ).read_text(encoding="utf-8")
        stylesheet += "\n" + (
            Path(__file__).resolve().parents[1] / "pages/updates/update_styles.qss"
        ).read_text(encoding="utf-8")
        stylesheet += "\n" + (Path(__file__).resolve().parents[1] / "widgets/sidebar_styles.qss").read_text(
            encoding="utf-8"
        )
        colors = dict(PINK_LIGHT)
        dark = theme == "pink_dark" or (
            theme == "system" and self.application.styleHints().colorScheme() == Qt.ColorScheme.Dark
        )
        if dark:
            colors.update(
                background="#211B24",
                surface="#2D2530",
                sidebar="#281F2B",
                text="#FFF3F9",
                muted="#C7B8C3",
                border="#54404F",
                soft="#503046",
                hover="#44303E",
                disabled="#362D38",
                disabled_text="#A08D9A",
                selection="#70415D",
                focus="#FFA3CB",
            )
        if accent:
            if not QColor.isValidColorName(accent):
                raise ValueError("Invalid accent color")
            colors["primary"] = QColor(accent).name()
            colors["gradient_end"] = QColor(accent).lighter(120).name()
            colors["secondary"] = QColor(accent).lighter(115).name()
        tokens = dict(colors)
        tokens["icons_path"] = (Path(__file__).resolve().parents[2] / "assets" / "icons").as_posix()
        tokens.update({f"radius_{key}": str(value) for key, value in RADII.items()})
        tokens.update({f"font_{key}": str(value) for key, value in TYPOGRAPHY.items()})
        for key, value in tokens.items():
            stylesheet = stylesheet.replace("{{" + key + "}}", value)
        if "{{" in stylesheet:
            raise ValueError("Unresolved theme token")

        self.application.setStyle("Fusion")
        families = set(QFontDatabase.families())
        family = next((name for name in FONT_FAMILIES if name in families), self.application.font().family())
        self.application.setFont(QFont(family, TYPOGRAPHY["body"]))
        palette = QPalette()
        roles = {
            "Window": "background",
            "WindowText": "text",
            "Base": "surface",
            "AlternateBase": "sidebar",
            "Text": "text",
            "Button": "surface",
            "ButtonText": "text",
            "BrightText": "surface",
            "Highlight": "selection",
            "HighlightedText": "text",
            "ToolTipBase": "surface",
            "ToolTipText": "text",
            "Link": "focus",
            "LinkVisited": "pressed",
            "PlaceholderText": "muted",
            "Light": "surface",
            "Midlight": "sidebar",
            "Mid": "border",
            "Dark": "muted",
            "Shadow": "border",
            "Accent": "primary",
        }
        for role, token in roles.items():
            palette.setColor(getattr(QPalette.ColorRole, role), QColor(colors[token]))
        for role in ("WindowText", "Text", "ButtonText", "PlaceholderText"):
            palette.setColor(
                QPalette.ColorGroup.Disabled,
                getattr(QPalette.ColorRole, role),
                QColor(colors["disabled_text"]),
            )
        self.application.setPalette(palette)
        self.application.setStyleSheet(stylesheet)
        self.current_theme = theme

    @staticmethod
    def set_role(widget: QWidget, role: str) -> None:
        """Refresh dynamic QSS properties even on an already visible widget."""
        widget.setProperty("role", role)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    @staticmethod
    def add_card_shadow(widget: QWidget) -> None:
        """Qt QSS has no box-shadow; opt in on individual surface cards."""
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(80, 35, 56, 20))
        widget.setGraphicsEffect(shadow)

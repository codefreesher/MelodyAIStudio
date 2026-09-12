"""Startup view emits intent; navigation belongs to the controller.

Layout: StartupBackground (soft glows) sits behind an ArtworkWidget that
bleeds its right-anchored illustration into that background, with the
LeftHero content overlaid on top — all three layers share the same content
rect via a StackAll QStackedLayout so the artwork can extend past the
nominal 56/44 column split without ever covering the cards or text.
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QResizeEvent
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.core.version import get_version
from app.ui.pages.startup.startup_background import StartupBackground
from app.ui.pages.startup.startup_card import StartupCard
from app.ui.widgets.artwork_widget import ArtworkWidget

_ASSETS = Path(__file__).resolve().parents[3] / "assets"
_IMAGES = _ASSETS / "images"
_RASTER_ARTWORK_NAMES = ("startup-illustration.png", "startup-illustration.jpg")


class _OverlayStack(QWidget):
    """Layers widgets on top of one another, each filling the full rect.

    A plain child-widget stack (rather than QStackedLayout, whose StackAll
    mode only guarantees the *current* widget is topmost — the relative
    order of the others is unspecified and was observed to bury the artwork
    layer under the opaque background). Layers are given bottom-to-top and
    keep that paint order via normal Qt sibling stacking.
    """

    def __init__(self, layers: list[QWidget], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layers = layers
        for layer in layers:
            layer.setParent(self)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        for layer in self._layers:
            layer.setGeometry(self.rect())


class LeftHero(QWidget):
    """Logo, headline, action cards and slogan — vertically centered and
    centered within the left column; paints nothing of its own so the artwork layer behind it
    can bleed through past its right edge."""

    def __init__(self, version: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        column.addStretch(1)

        # The supplied logo includes the symbol, wordmark and tagline.
        # Use the complete asset so those elements are not repeated as labels.
        self.logo = QLabel()
        self.logo.setObjectName("startupBrandLogo")
        self.logo.setAccessibleName("MelodyAI — Create · Imagine · Feel")
        self._logo_pixmap = QPixmap(str(_IMAGES / "logo.png"))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignHCenter)
        column.addSpacing(14)

        self.headline = QLabel("Tất cả công cụ sáng tạo AI trong một ứng dụng")
        self.headline.setObjectName("startupHeadline")
        self.headline.setWordWrap(True)
        self.headline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.addWidget(self.headline)
        column.addSpacing(24)

        actions = QHBoxLayout()
        actions.setSpacing(20)
        self.login_card = StartupCard("Đăng nhập", "Đã có tài khoản", primary=True)
        self.activation_card = StartupCard("Kích hoạt", "Nhập key bản quyền")
        actions.addWidget(self.login_card)
        actions.addWidget(self.activation_card)
        column.addLayout(actions)
        column.addSpacing(18)

        self.quote = QLabel()
        self.quote.setObjectName("startupQuoteImage")
        self.quote.setAccessibleName("Music makes a better you ♥")
        self._quote_pixmap = QPixmap(str(_IMAGES / "text_begin.png"))
        self.quote.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.addWidget(self.quote, 0, Qt.AlignmentFlag.AlignHCenter)
        column.addStretch(1)
        self._resize_branding()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._resize_branding()

    def _resize_branding(self) -> None:
        # Scale the branding as a group, reserving room for the action cards.
        logo_width = min(360, max(240, int(self.height() * 0.45)))
        self._fit_image(self.logo, self._logo_pixmap, logo_width, 190)
        remaining = max(75, self.height() - self.logo.height() - 290)
        self._fit_image(
            self.quote, self._quote_pixmap, min(650, max(240, int(self.width() * 0.85))), min(190, remaining)
        )

    def _fit_image(self, label: QLabel, source: QPixmap, width: int, height: int) -> None:
        if source.isNull():
            label.setText(label.accessibleName())
            return
        ratio = max(2.0, self.devicePixelRatioF())
        image = source.scaled(
            round(width * ratio),
            round(height * ratio),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        image.setDevicePixelRatio(ratio)
        label.setPixmap(image)
        label.setFixedSize(round(image.width() / ratio), round(image.height() / ratio))


class StartupPage(QWidget):
    request_login = Signal()
    request_activation = Signal()

    def __init__(self, version: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("startupPage")
        self.setMinimumSize(1100, 650)
        version = version or get_version()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.background = StartupBackground()

        raster_path = next((p for name in _RASTER_ARTWORK_NAMES if (p := _IMAGES / name).is_file()), None)
        artwork_layer = QWidget()
        artwork_layout = QHBoxLayout(artwork_layer)
        artwork_layout.setContentsMargins(0, 0, 0, 0)
        if raster_path is not None:
            self.artwork = ArtworkWidget(str(raster_path))
            artwork_layout.addWidget(self.artwork)
        else:
            self.artwork = QSvgWidget(str(_IMAGES / "startup-headphones.svg"))
            self.artwork.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
            self.artwork.setAccessibleName("Minh họa tai nghe màu hồng MelodyAI")
            artwork_layout.addStretch(1)
            artwork_layout.addWidget(self.artwork, 1)

        foreground = QWidget()
        foreground_row = QHBoxLayout(foreground)
        foreground_row.setContentsMargins(64, 40, 48, 32)
        self.hero = LeftHero(version)
        foreground_row.addWidget(self.hero, 56)
        foreground_row.addStretch(44)

        content = _OverlayStack([self.background, artwork_layer, foreground])
        root.addWidget(content, 1)

        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(48, 0, 48, 20)
        self.footer = QLabel(f"v{version}   ·   AI Music & Creative Studio")
        self.footer.setObjectName("startupFooter")
        footer_row.addWidget(self.footer)
        footer_row.addStretch(1)
        self.footer_tagline = QLabel("Sáng tạo hôm nay, cảm xúc ngày mai ♥")
        self.footer_tagline.setObjectName("startupFooterTagline")
        footer_row.addWidget(self.footer_tagline)
        root.addLayout(footer_row)

        self.login_card = self.hero.login_card
        self.activation_card = self.hero.activation_card
        self.login_card.clicked.connect(self.request_login.emit)
        self.activation_card.clicked.connect(self.request_activation.emit)

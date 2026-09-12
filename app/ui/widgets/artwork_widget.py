"""Hero illustration that bleeds into the page background.

Unlike a plain QLabel/QSvgWidget, this widget owns its own scaling and
compositing: the source image is cropped to cover its right-hand region
(KeepAspectRatioByExpanding) and its left/bottom edges are alpha-faded to
transparent, so no rectangular artwork boundary is ever visible — the page
background painted behind it shows through the fade instead.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QWidget

#: Fraction of the widget's own width the illustration occupies, right-anchored.
_ART_WIDTH_RATIO = 0.62
#: Fraction of the illustration's width given to the left fade-to-transparent.
_LEFT_FADE_RATIO = 0.55
#: Fraction of the widget's height given to the bottom fade-to-transparent.
_BOTTOM_FADE_RATIO = 0.24


class ArtworkWidget(QWidget):
    def __init__(self, path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._source = QPixmap(path)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setMinimumSize(240, 240)

    def isValid(self) -> bool:
        return not self._source.isNull()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002 - Qt signature
        if self._source.isNull():
            return
        width, height = self.width(), self.height()
        if width <= 0 or height <= 0:
            return

        art_width = max(1, int(width * _ART_WIDTH_RATIO))
        scaled = self._source.scaled(
            QSize(art_width, height),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        crop_x = max(0, (scaled.width() - art_width) // 2)
        crop_y = max(0, (scaled.height() - height) // 2)
        cropped = scaled.copy(crop_x, crop_y, art_width, height)

        buffer = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        buffer.fill(Qt.GlobalColor.transparent)
        art_x = width - art_width
        painter = QPainter(buffer)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(art_x, 0, cropped)

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        fade_width = max(1, int(art_width * _LEFT_FADE_RATIO))
        left_fade = QLinearGradient(art_x, 0, art_x + fade_width, 0)
        left_fade.setColorAt(0.0, QColor(0, 0, 0, 0))
        left_fade.setColorAt(1.0, QColor(0, 0, 0, 255))
        painter.fillRect(art_x, 0, fade_width, height, left_fade)

        bottom_fade_height = max(1, int(height * _BOTTOM_FADE_RATIO))
        bottom_fade = QLinearGradient(0, height - bottom_fade_height, 0, height)
        bottom_fade.setColorAt(0.0, QColor(0, 0, 0, 255))
        bottom_fade.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(art_x, height - bottom_fade_height, art_width, bottom_fade_height, bottom_fade)
        painter.end()

        page_painter = QPainter(self)
        page_painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        page_painter.drawImage(0, 0, buffer)

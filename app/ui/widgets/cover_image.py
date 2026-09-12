"""A widget that renders an image to fill its rect, never distorted.

Two modes:

- ``"cover"`` (default) — KeepAspectRatioByExpanding + center-crop, so the
  image always fills the panel edge to edge. Right for a full-bleed photo.
- ``"contain"`` — KeepAspectRatio, centered over a soft gradient backdrop.
  Right for a sticker-style cutout (transparent background, own decorative
  text baked in) that would lose content — its top/bottom text — if cropped.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QWidget


class CoverImage(QWidget):
    def __init__(self, path: str, mode: str = "cover", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._source = QPixmap(path)
        self._mode = mode

    def isValid(self) -> bool:
        return not self._source.isNull()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002 - Qt signature
        if self._source.isNull():
            return
        width, height = self.width(), self.height()
        if width <= 0 or height <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self._mode == "contain":
            gradient = QLinearGradient(0, 0, 0, height)
            gradient.setColorAt(0.0, QColor("#FDEFF4"))
            gradient.setColorAt(1.0, QColor("#F3B8CF"))
            painter.fillRect(self.rect(), gradient)
            scaled = self._source.scaled(
                QSize(width, height), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap((width - scaled.width()) // 2, (height - scaled.height()) // 2, scaled)
            return
        scaled = self._source.scaled(
            QSize(width, height),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        crop_x = (scaled.width() - width) // 2
        crop_y = (scaled.height() - height) // 2
        painter.drawPixmap(0, 0, scaled, crop_x, crop_y, width, height)

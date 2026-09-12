"""Result gallery for the image tool: one hero + a grid of smaller thumbs.

Kept separate from :class:`app.ui.widgets.image_gallery.ImageGallery` (a
plain QListWidget gallery still used by the component showcase and its
tests) — this widget owns a different, denser mosaic layout with a
hover-revealed action row per card, matching the reference design.
"""

from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QImageReader, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.empty_state import EmptyState

_ICONS = Path(__file__).resolve().parents[2] / "assets/icons"


def _read_preview(path: Path, size: QSize) -> QPixmap:
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    original = reader.size()
    if original.isValid():
        reader.setScaledSize(original.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding))
    return QPixmap.fromImage(reader.read())


class ImageCard(QFrame):
    """One result thumbnail; hover reveals Preview/Download/Save actions."""

    preview_requested = Signal(str)
    download_requested = Signal(str)
    save_requested = Signal(str)

    def __init__(self, path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.path = str(path)
        self.setObjectName("imageCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(90)
        self.setMaximumHeight(320)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.thumb = QLabel()
        self.thumb.setObjectName("imageCardThumb")
        self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb.setScaledContents(False)
        layout.addWidget(self.thumb)
        self._source = QPixmap(self.path)

        self.overlay = QWidget(self)
        self.overlay.setObjectName("imageCardOverlay")
        overlay_row = QHBoxLayout(self.overlay)
        overlay_row.setContentsMargins(0, 0, 0, 0)
        overlay_row.setSpacing(6)
        for icon_file, tooltip, signal in (
            ("eye-white.svg", "Xem trước", self.preview_requested),
            ("download-white.svg", "Tải xuống", self.download_requested),
            ("bookmark-white.svg", "Lưu vào lịch sử", self.save_requested),
        ):
            button = QPushButton()
            button.setObjectName("imageCardAction")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setIcon(QIcon(str(_ICONS / icon_file)))
            button.setIconSize(QSize(15, 15))
            button.setToolTip(tooltip)
            button.clicked.connect(lambda _checked=False, sig=signal: sig.emit(self.path))
            overlay_row.addWidget(button)
        self.overlay.hide()
        self.installEventFilter(self)

    def resizeEvent(self, event) -> None:  # noqa: ANN001 - Qt signature
        super().resizeEvent(event)
        self._rescale()
        self.overlay.setGeometry(0, self.height() - 34, self.width(), 34)

    def _rescale(self) -> None:
        if self._source.isNull() or self.width() <= 0 or self.height() <= 0:
            return
        scaled = self._source.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
        )
        x = (scaled.width() - self.width()) // 2
        y = (scaled.height() - self.height()) // 2
        self.thumb.setPixmap(scaled.copy(x, y, self.width(), self.height()))

    def eventFilter(self, watched: QWidget, event: QEvent) -> bool:
        if watched is self:
            if event.type() == QEvent.Type.Enter:
                self.overlay.show()
                self.overlay.raise_()
            elif event.type() == QEvent.Type.Leave:
                self.overlay.hide()
        return super().eventFilter(watched, event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: ANN001 - Qt signature
        if event.button() == Qt.MouseButton.LeftButton and not self.overlay.geometry().contains(event.pos()):
            self.preview_requested.emit(self.path)
        super().mouseReleaseEvent(event)


class ImageResultGallery(QWidget):
    image_opened = Signal(str)
    download_requested = Signal(str)
    download_all_requested = Signal()
    save_requested = Signal(str)
    error = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Kết quả")
        title.setObjectName("galleryTitle")
        header.addWidget(title)
        header.addStretch(1)
        self.download_all_button = QPushButton("Tải tất cả")
        self.download_all_button.setObjectName("galleryDownloadAll")
        self.download_all_button.setIcon(QIcon(str(_ICONS / "download.svg")))
        self.download_all_button.setIconSize(QSize(13, 13))
        self.download_all_button.clicked.connect(self.download_all_requested.emit)
        header.addWidget(self.download_all_button)
        self.header = QWidget()
        self.header.setLayout(header)
        # Without a cap, a plain QWidget with no other stretch to compete
        # against ends up sharing the layout's leftover height 50/50 with
        # whatever comes after it — pinning it to its content height keeps
        # "Kết quả" flush at the top instead of floating a third of the way
        # down the column.
        self.header.setMaximumHeight(32)
        layout.addWidget(self.header)

        self.empty = EmptyState("Chưa có ảnh", "Ảnh được tạo sẽ xuất hiện tại đây.")
        layout.addWidget(self.empty, 1)

        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setSpacing(8)
        # A scroll area — not a bare stretch-filled widget — so cards render
        # at a capped, thumbnail-like size (see ImageCard.setMaximumHeight)
        # and any overflow (more rows than fit, or a short window) scrolls
        # instead of being force-stretched to fill the leftover space.
        self.scroll = QScrollArea()
        self.scroll.setObjectName("galleryScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setWidget(self.grid_container)
        layout.addWidget(self.scroll, 1)
        self.scroll.hide()

        self._preview: QDialog | None = None
        self._cards: list[ImageCard] = []
        self._loading = False
        self._showing_skeleton = False
        self._sync_header()

    def _clear_grid(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                # setParent(None) drops it from the layout's geometry
                # accounting immediately; deleteLater() alone leaves a
                # stale row/column stretch (a visible sliver) until the
                # next event loop turn frees it.
                widget.setParent(None)
                widget.deleteLater()
        for row in range(self.grid.rowCount()):
            self.grid.setRowStretch(row, 0)
        self._cards.clear()

    def set_images(self, paths: Iterable[str | Path]) -> None:
        self._showing_skeleton = False
        self._clear_grid()
        resolved = []
        for path in paths:
            source = Path(path).expanduser().resolve()
            if not source.is_file():
                self.error.emit(f"Không thể đọc ảnh: {source.name}")
                continue
            resolved.append(source)
        for source in resolved:
            card = ImageCard(str(source))
            card.setMinimumHeight(140)
            card.preview_requested.connect(self._open_preview)
            card.download_requested.connect(self.download_requested.emit)
            card.save_requested.connect(self.save_requested.emit)
            self._cards.append(card)
        self._layout_cards()
        has_images = bool(resolved)
        self.empty.setVisible(not has_images)
        self.scroll.setVisible(has_images)
        self._sync_header()

    def _layout_cards(self) -> None:
        self._place_widgets(self._cards)

    def _place_widgets(self, widgets: list[QWidget]) -> None:
        """1 or 2 results get a hero treatment; AIService only ever hands us
        1/2/4 images (see its ratio/count validation), and a hero + 3
        thumbnails for 4 leaves one grid cell blank — a lopsided-looking
        gap. 3+ results fall back to an even N-column grid instead, so
        every cell is filled and nothing looks misaligned."""
        count = len(widgets)
        if count == 0:
            return
        if count <= 2:
            for column in range(3):
                self.grid.setColumnStretch(column, 2 if column == 0 else 1)
            hero = widgets[0]
            hero.setMinimumHeight(220)
            if count == 1:
                self.grid.addWidget(hero, 0, 0, 1, 3)
            else:
                self.grid.addWidget(hero, 0, 0, 2, 1)
                self.grid.addWidget(widgets[1], 0, 1, 2, 2)
            return
        for column in range(3):
            self.grid.setColumnStretch(column, 0)
        columns = 2
        for column in range(columns):
            self.grid.setColumnStretch(column, 1)
        for index, widget in enumerate(widgets):
            row, column = divmod(index, columns)
            self.grid.addWidget(widget, row, column)

    def _sync_header(self) -> None:
        self.header.setVisible(bool(self._cards))

    def show_skeleton(self, count: int = 4) -> None:
        """Loading placeholder cards, shown while a generation is running."""
        self._showing_skeleton = True
        self._clear_grid()
        placeholders = []
        for _ in range(count):
            frame = QFrame()
            frame.setObjectName("imageCardSkeleton")
            frame.setMinimumHeight(140)
            frame.setMaximumHeight(320)
            placeholders.append(frame)
        self._place_widgets(placeholders)
        self.empty.hide()
        self.scroll.show()
        self.header.hide()

    def set_loading(self, loading: bool) -> None:
        # The page reuses this for save/export loading too (same shared
        # controller), not only generation — only wipe to a skeleton when
        # there is nothing worth preserving on screen yet.
        self._loading = loading
        if loading:
            if not self._cards:
                self.show_skeleton()
        elif self._showing_skeleton:
            # Generation ended without a show_result() call (e.g. it
            # failed) — fall back to the empty state instead of leaving
            # skeleton placeholders on screen forever.
            self._showing_skeleton = False
            self._clear_grid()
            self.empty.show()
            self.scroll.hide()
            self._sync_header()
        self.scroll.setEnabled(not loading)

    def _open_preview(self, path: str) -> None:
        pixmap = _read_preview(Path(path), QSize(900, 650))
        if pixmap.isNull():
            self.error.emit("Ảnh không còn khả dụng.")
            return
        if self._preview is not None:
            self._preview.close()
            self._preview.deleteLater()
        self._preview = QDialog(self)
        self._preview.setWindowTitle(Path(path).name)
        preview_layout = QVBoxLayout(self._preview)
        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(label)
        self._preview.show()
        self.image_opened.emit(path)

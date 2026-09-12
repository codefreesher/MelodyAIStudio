"""Responsive thumbnail gallery. Callers supply local images, never URLs."""

from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QImageReader, QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from app.ui.widgets.empty_state import EmptyState


def read_preview(path: Path, size: QSize) -> QPixmap:
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    original = reader.size()
    if original.isValid():
        reader.setScaledSize(original.scaled(size, Qt.AspectRatioMode.KeepAspectRatio))
    return QPixmap.fromImage(reader.read())


class ImageGallery(QWidget):
    image_opened = Signal(str)
    error = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.empty = EmptyState("Chưa có ảnh", "Ảnh kết quả sẽ xuất hiện tại đây.")
        layout.addWidget(self.empty)
        self.list = QListWidget()
        self.list.setViewMode(QListWidget.ViewMode.IconMode)
        self.list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list.setMovement(QListWidget.Movement.Static)
        self.list.setIconSize(QSize(160, 120))
        self.list.setGridSize(QSize(190, 160))
        self.list.setWordWrap(True)
        self.list.setMinimumHeight(180)
        self.list.setAccessibleName("Thư viện ảnh")
        layout.addWidget(self.list)
        self.list.hide()
        self.list.itemClicked.connect(self._open_item)
        self.list.itemActivated.connect(self._open_item)
        self._preview: QDialog | None = None
        self._was_enabled = True
        self._loading = False

    def set_images(self, paths: Iterable[str | Path]) -> None:
        self.list.clear()
        for path in paths:
            source = Path(path).expanduser().resolve()
            pixmap = read_preview(source, QSize(320, 240))
            if pixmap.isNull():
                self.error.emit(f"Không thể đọc ảnh: {source.name}")
                continue
            item = QListWidgetItem(QIcon(pixmap), source.name)
            item.setData(Qt.ItemDataRole.UserRole, str(source))
            item.setToolTip(source.name)
            self.list.addItem(item)
        has_images = self.list.count() > 0
        self.empty.setVisible(not has_images)
        self.list.setVisible(has_images)

    def set_loading(self, loading: bool) -> None:
        if loading == self._loading:
            return
        self._loading = loading
        if loading:
            self._was_enabled = self.list.isEnabled()
            self.list.setEnabled(False)
        else:
            self.list.setEnabled(self._was_enabled)
        self.setToolTip("Đang tải ảnh…" if loading else "")

    def _open_item(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        pixmap = read_preview(Path(path), QSize(900, 650))
        if pixmap.isNull():
            self.error.emit("Ảnh không còn khả dụng.")
            return
        if self._preview is not None:
            self._preview.close()
            self._preview.deleteLater()
        self._preview = QDialog(self)
        self._preview.setWindowTitle(Path(path).name)
        layout = QVBoxLayout(self._preview)
        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self._preview.show()
        self.image_opened.emit(path)

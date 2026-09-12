"""Storage tab: one card, one row per folder — friendly names, real paths,
compact Mở/Đổi actions. Internal folder keys (projects/downloads/models/
cache) are unchanged from SettingsService; only the display differs."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from app.ui.widgets.path_selector import PathSelector
from app.ui.widgets.setting_card import SettingCard

# (internal key, icon, title, description) — order matches the reference.
_FOLDERS = (
    ("projects", "folder.svg", "Dự án", "Nơi lưu nhạc, lyric, audio và ảnh đã tạo"),
    ("downloads", "download.svg", "Tệp tải xuống", "Nơi lưu file được tải về"),
    ("models", "hard-drive.svg", "AI Models", "Nơi lưu các model AI local"),
    ("cache", "database.svg", "Bộ nhớ đệm", "Dữ liệu tạm của MelodyAI"),
)


class StorageSettings(QWidget):
    folder_action = Signal(str, str)  # (internal key, "open" | "change")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(16)

        card = SettingCard("Vị trí lưu trữ")
        self.selectors: dict[str, PathSelector] = {}
        for index, (key, icon_file, title, description) in enumerate(_FOLDERS):
            selector = PathSelector(icon_file, title, description)
            selector.open_requested.connect(lambda k=key: self.folder_action.emit(k, "open"))
            selector.change_requested.connect(lambda k=key: self.folder_action.emit(k, "change"))
            card.add_row(selector)
            self.selectors[key] = selector
            if index < len(_FOLDERS) - 1:
                card.add_divider()
        column.addWidget(card)
        column.addStretch(1)

    def set_path(self, key: str, path: str) -> None:
        selector = self.selectors.get(key)
        if selector:
            selector.set_path(path)

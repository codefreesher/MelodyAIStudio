"""Compact history list: filter tabs + search over a scrollable card list.

Replaces the previous QTableWidget layout; the controller's contract is
unchanged except ``action_requested`` now carries the row index directly
(the old table-selection lookup — ``page.table.currentRow()`` — has no
equivalent once each row owns its own inline Play/Download/Delete buttons).
"""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.dropdown import ComboBox
from app.ui.widgets.empty_state import EmptyState
from app.ui.widgets.inputs import SearchInput
from app.ui.widgets.toast import Toast

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"
_PAGE_SIZE = 20
_TYPE_META = {
    "music": ("dashboard-music.svg", "Nhạc"),
    "lyric": ("dashboard-lyric.svg", "Lyric"),
    "audio": ("dashboard-audio.svg", "Audio"),
    "image": ("dashboard-image.svg", "Ảnh"),
}


def _format_datetime(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return value


class HistoryItemRow(QFrame):
    """One history entry: type avatar, title/subtitle, inline actions."""

    play_requested = Signal()
    download_requested = Signal()
    delete_requested = Signal()

    def __init__(self, row: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("historyItem")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        icon_file, type_label = _TYPE_META.get(row["type"], ("dashboard-music.svg", row["type"]))
        avatar = QLabel()
        avatar.setObjectName("historyItemAvatar")
        avatar.setFixedSize(44, 44)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setPixmap(QIcon(str(_ICONS / icon_file)).pixmap(QSize(22, 22)))
        layout.addWidget(avatar)

        text_column = QVBoxLayout()
        text_column.setSpacing(2)
        title = QLabel(row["title"])
        title.setObjectName("historyItemTitle")
        title.setWordWrap(False)
        subtitle = QLabel(f"{type_label} · {_format_datetime(row['created_at'])}")
        subtitle.setObjectName("historyItemSubtitle")
        text_column.addWidget(title)
        text_column.addWidget(subtitle)
        layout.addLayout(text_column, 1)

        for icon_file, tooltip, signal in (
            ("play.svg", "Phát", self.play_requested),
            ("download.svg", "Tải xuống", self.download_requested),
            ("trash.svg", "Xóa", self.delete_requested),
        ):
            button = QPushButton()
            button.setObjectName("historyItemAction")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setIcon(QIcon(str(_ICONS / icon_file)))
            button.setIconSize(QSize(15, 15))
            button.setToolTip(tooltip)
            button.clicked.connect(signal.emit)
            layout.addWidget(button)


class HistoryPage(QWidget):
    refresh_requested = Signal()
    action_requested = Signal(str, int)
    page_requested = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("historyPage")
        self._page = 0
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)

        title = QLabel("Lịch sử sáng tạo")
        title.setObjectName("historyHeading")
        root.addWidget(title)
        self.toast = Toast(plain=True)
        root.addWidget(self.toast)

        self.tabs = QTabBar()
        self.tabs.setObjectName("historyTabs")
        self.tabs.setExpanding(False)
        self.tabs.setDrawBase(False)
        for text in ("Tất cả", "Nhạc", "Lyric", "Audio", "Ảnh"):
            self.tabs.addTab(text)
        root.addWidget(self.tabs)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)
        self.search = SearchInput()
        self.search.setObjectName("historySearch")
        self.search.addAction(QIcon(str(_ICONS / "search.svg")), QLineEdit.ActionPosition.LeadingPosition)
        filter_row.addWidget(self.search, 1)
        self.sort = ComboBox(["Mới nhất", "Cũ nhất"])
        self.sort.setObjectName("historySort")
        self.sort.setFixedWidth(150)
        filter_row.addWidget(self.sort)
        root.addLayout(filter_row)

        self.list_container = QWidget()
        self.list_container.setObjectName("historyListContainer")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.empty = EmptyState("Chưa có lịch sử", "Kết quả sáng tạo của bạn sẽ xuất hiện tại đây.")
        self.list_layout.addWidget(self.empty)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("historyScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setWidget(self.list_container)
        root.addWidget(self.scroll, 1)

        pager = QHBoxLayout()
        pager.addStretch(1)
        self.previous = QPushButton()
        self.previous.setObjectName("historyPagerArrow")
        self.previous.setIcon(QIcon(str(_ICONS / "chevron-left.svg")))
        self.previous.setCursor(Qt.CursorShape.PointingHandCursor)
        pager.addWidget(self.previous)
        self.page_numbers = QHBoxLayout()
        self.page_numbers.setSpacing(4)
        pager.addLayout(self.page_numbers)
        self.next = QPushButton()
        self.next.setObjectName("historyPagerArrow")
        self.next.setIcon(QIcon(str(_ICONS / "chevron-right.svg")))
        self.next.setCursor(Qt.CursorShape.PointingHandCursor)
        pager.addWidget(self.next)
        pager.addStretch(1)
        root.addLayout(pager)

        self.previous.clicked.connect(lambda: self.page_requested.emit(-1))
        self.next.clicked.connect(lambda: self.page_requested.emit(1))
        self.tabs.currentChanged.connect(lambda _: self.refresh_requested.emit())
        self.sort.currentIndexChanged.connect(lambda _: self.refresh_requested.emit())
        self.search.search_requested.connect(lambda _: self.refresh_requested.emit())

    def show_rows(self, rows: list[dict], total: int, page: int) -> None:
        self._page = page
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            # self.empty is a long-lived widget re-added on every empty
            # result, not a per-call card — deleting it here leaves a
            # dangling reference that crashes the next empty-result call.
            if widget and widget is not self.empty:
                widget.setParent(None)
                widget.deleteLater()
        if not rows:
            self.list_layout.addWidget(self.empty)
            self.empty.show()
        else:
            # takeAt() above only unmanages self.empty from the layout — it
            # stays visible, floating at its last geometry, until told
            # otherwise, which is what left it hovering under real rows.
            self.empty.hide()
            for index, row in enumerate(rows):
                card = HistoryItemRow(row)
                card.play_requested.connect(lambda _=False, i=index: self.action_requested.emit("play", i))
                card.download_requested.connect(lambda _=False, i=index: self.action_requested.emit("export", i))
                card.delete_requested.connect(lambda _=False, i=index: self.action_requested.emit("delete", i))
                self.list_layout.addWidget(card)
            self.list_layout.addStretch(1)
        self._update_pager(total, page)

    def _update_pager(self, total: int, page: int) -> None:
        total_pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)
        while self.page_numbers.count():
            item = self.page_numbers.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        window = 5
        start = max(0, min(page - window // 2, total_pages - window))
        end = min(total_pages, start + window)
        for number in range(start, end):
            button = QPushButton(str(number + 1))
            button.setObjectName("historyPageNumber")
            button.setCheckable(True)
            button.setChecked(number == page)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _=False, target=number: self.page_requested.emit(target - self._page))
            self.page_numbers.addWidget(button)
        self.previous.setEnabled(page > 0)
        self.next.setEnabled(page + 1 < total_pages)

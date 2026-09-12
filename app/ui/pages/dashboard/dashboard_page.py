"""MelodyAI dashboard with quick tools, banner and recent projects."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from app.ui.widgets.empty_state import EmptyState
from app.ui.widgets.inputs import SearchInput

_IMAGES = Path(__file__).resolve().parents[3] / "assets/images"
_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"


class DashboardBanner(QWidget):
    """Responsive pastel banner that preserves the supplied artwork ratio."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dashboardBanner")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setMinimumHeight(130)
        self.setMaximumHeight(190)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._artwork = QPixmap(str(_IMAGES / "banner.png"))

    def sizeHint(self) -> QSize:
        return QSize(1000, 165)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002 - Qt signature
        if self._artwork.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        scaled = self._artwork.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        painter.drawPixmap(
            (self.width() - scaled.width()) // 2, (self.height() - scaled.height()) // 2, scaled
        )


class DashboardActionCard(QPushButton):
    def __init__(self, icon_file: str, title: str, description: str, variant: str) -> None:
        super().__init__()
        self.setObjectName("dashboardActionCard")
        self.setProperty("variant", variant)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(f"{title}. {description}")
        self.setMinimumHeight(148)
        column = QVBoxLayout(self)
        column.setContentsMargins(18, 16, 18, 16)
        column.setSpacing(5)
        icon = QLabel()
        icon.setObjectName("dashboardActionIcon")
        icon.setProperty("variant", variant)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        icon.setFixedSize(52, 52)
        icon.setPixmap(QIcon(str(_ICONS / icon_file)).pixmap(QSize(34, 34)))
        title_label = QLabel(title)
        title_label.setObjectName("dashboardActionTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        description_label = QLabel(description)
        description_label.setObjectName("dashboardActionDescription")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setWordWrap(True)
        description_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        column.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)
        column.addWidget(title_label)
        column.addWidget(description_label)


class RecentProjectCard(QPushButton):
    def __init__(self, row: dict) -> None:
        super().__init__()
        self.setObjectName("dashboardProjectCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(row["title"])
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 8)
        column.setSpacing(5)
        thumbnail = QLabel()
        thumbnail.setObjectName("dashboardProjectThumbnail")
        thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        thumbnail.setMinimumHeight(105)
        thumbnail.setMaximumHeight(125)
        path = row.get("thumbnail_path", "")
        if not path and str(row.get("type", "")).casefold() in ("music", "nhạc"):
            path = str(_IMAGES / "default_music_cover.png")
        pixmap = QPixmap(path) if path else QPixmap()
        if pixmap.isNull():
            thumbnail.setText("♪")
        else:
            thumbnail.setPixmap(
                pixmap.scaled(
                    360,
                    210,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        title = QLabel(row["title"])
        title.setObjectName("dashboardProjectTitle")
        meta = QLabel(f"{row['type']} · {row['created_at'][:10]}")
        meta.setObjectName("dashboardProjectMeta")
        for label in (title, meta):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            label.setContentsMargins(10, 0, 10, 0)
        column.addWidget(thumbnail)
        column.addWidget(title)
        column.addWidget(meta)


class DashboardPage(QWidget):
    navigate = Signal(str)
    search_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dashboardPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        greeting_column = QVBoxLayout()
        greeting_column.setSpacing(2)
        self.greeting = QLabel("Xin chào!")
        self.greeting.setObjectName("dashboardGreeting")
        greeting_column.addWidget(self.greeting)
        greeting_column.addWidget(QLabel("Hôm nay bạn muốn sáng tạo điều gì?"))
        header.addLayout(greeting_column, 1)
        self.search = SearchInput("Tìm kiếm chức năng…")
        self.search.setObjectName("dashboardSearch")
        self.search.setMinimumWidth(280)
        self.search.setMaximumWidth(340)
        self.search.search_requested.connect(self.search_requested.emit)
        header.addWidget(self.search)
        layout.addLayout(header)

        layout.addWidget(DashboardBanner())

        cards = QHBoxLayout()
        cards.setSpacing(12)
        tools = [
            ("music", "dashboard-music.svg", "Tạo nhạc", "Biến ý tưởng thành bản nhạc hoàn chỉnh"),
            ("lyric", "dashboard-lyric.svg", "Tạo lyric", "Viết lời bài hát theo chủ đề, cảm xúc"),
            ("audio", "dashboard-audio.svg", "Tạo audio", "Chuyển văn bản thành giọng nói"),
            ("image", "dashboard-image.svg", "Tạo ảnh", "Tạo hình ảnh từ mô tả bằng AI"),
        ]
        self.action_cards: dict[str, DashboardActionCard] = {}
        for route, icon_file, title, description in tools:
            card = DashboardActionCard(icon_file, title, description, route)
            card.clicked.connect(lambda checked=False, key=route: self.navigate.emit(key))
            cards.addWidget(card, 1)
            self.action_cards[route] = card
        layout.addLayout(cards)

        recent_header = QHBoxLayout()
        recent_title = QLabel("Dự án gần đây")
        recent_title.setObjectName("dashboardSectionTitle")
        recent_header.addWidget(recent_title)
        recent_header.addStretch(1)
        view_all = QPushButton("Xem tất cả  →")
        view_all.setObjectName("dashboardViewAll")
        view_all.clicked.connect(lambda: self.navigate.emit("history"))
        recent_header.addWidget(view_all)
        layout.addLayout(recent_header)

        self.recent_host = QWidget()
        self.recent = QGridLayout(self.recent_host)
        self.recent.setContentsMargins(0, 0, 0, 0)
        self.recent.setHorizontalSpacing(12)
        for column in range(4):
            self.recent.setColumnStretch(column, 1)
        layout.addWidget(self.recent_host)
        layout.addStretch(1)

    def set_projects(self, rows: list[dict]) -> None:
        while self.recent.count():
            item = self.recent.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        if not rows:
            self.recent.addWidget(
                EmptyState("Chưa có dự án", "Tạo và lưu kết quả đầu tiên của bạn."), 0, 0, 1, 4
            )
            return
        for index, row in enumerate(rows[:4]):
            card = RecentProjectCard(row)
            card.clicked.connect(lambda checked=False: self.navigate.emit("history"))
            self.recent.addWidget(card, 0, index)

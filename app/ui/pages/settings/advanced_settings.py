"""Advanced tab: cache/logs as normal cards, credentials/logout set apart
in a visually distinct danger zone — never four identical full-width
buttons in a row."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.widgets.buttons import DangerButton, OutlineButton
from app.ui.widgets.setting_card import SettingCard


class AdvancedSettings(QWidget):
    action_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(16)

        cache_card = SettingCard("Bộ nhớ đệm")
        cache_text = QLabel("Xóa dữ liệu tạm của MelodyAI. Không ảnh hưởng dự án đã tạo.")
        cache_text.setObjectName("settingRowDescription")
        cache_text.setWordWrap(True)
        cache_card.add_row(cache_text)
        cache_row = QHBoxLayout()
        cache_row.addStretch(1)
        cache_button = OutlineButton("Xóa cache")
        cache_button.clicked.connect(lambda: self.action_requested.emit("clear_cache"))
        cache_row.addWidget(cache_button)
        cache_card.add_row_layout(cache_row)
        column.addWidget(cache_card)

        logs_card = SettingCard("Nhật ký ứng dụng")
        logs_text = QLabel("Nhật ký giúp kiểm tra lỗi của MelodyAI.")
        logs_text.setObjectName("settingRowDescription")
        logs_text.setWordWrap(True)
        logs_card.add_row(logs_text)
        logs_row = QHBoxLayout()
        logs_row.addStretch(1)
        logs_button = OutlineButton("Xem logs")
        logs_button.clicked.connect(lambda: self.action_requested.emit("logs"))
        logs_row.addWidget(logs_button)
        logs_card.add_row_layout(logs_row)
        column.addWidget(logs_card)

        danger_label = QLabel("Vùng nguy hiểm")
        danger_label.setObjectName("dangerZoneLabel")
        column.addWidget(danger_label)

        danger_card = SettingCard()
        danger_card.setObjectName("dangerZoneCard")

        credentials_row = QVBoxLayout()
        credentials_row.setSpacing(4)
        credentials_title = QLabel("Tài khoản & dữ liệu đăng nhập")
        credentials_title.setObjectName("dangerRowTitle")
        credentials_row.addWidget(credentials_title)
        credentials_desc = QLabel("Xóa thông tin đăng nhập đã lưu — API key/token lưu trong Credential Vault.")
        credentials_desc.setObjectName("dangerRowDescription")
        credentials_desc.setWordWrap(True)
        credentials_row.addWidget(credentials_desc)
        credentials_line = QHBoxLayout()
        credentials_line.addLayout(credentials_row, 1)
        credentials_button = DangerButton("Xóa credentials")
        credentials_button.setObjectName("dangerActionButton")
        credentials_button.clicked.connect(lambda: self.action_requested.emit("clear_credentials"))
        credentials_line.addWidget(credentials_button, 0, Qt.AlignmentFlag.AlignVCenter)
        danger_card.add_row_layout(credentials_line)
        danger_card.add_divider()

        logout_row = QVBoxLayout()
        logout_row.setSpacing(4)
        logout_title = QLabel("Đăng xuất khỏi MelodyAI")
        logout_title.setObjectName("dangerRowTitle")
        logout_row.addWidget(logout_title)
        logout_desc = QLabel("Phiên đăng nhập hiện tại sẽ bị kết thúc.")
        logout_desc.setObjectName("dangerRowDescription")
        logout_row.addWidget(logout_desc)
        logout_line = QHBoxLayout()
        logout_line.addLayout(logout_row, 1)
        logout_button = DangerButton("Đăng xuất")
        logout_button.setObjectName("dangerActionButton")
        logout_button.clicked.connect(lambda: self.action_requested.emit("clear_session"))
        logout_line.addWidget(logout_button, 0, Qt.AlignmentFlag.AlignVCenter)
        danger_card.add_row_layout(logout_line)

        column.addWidget(danger_card)
        column.addStretch(1)

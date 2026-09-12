"""Activation form emits intent and never reads hardware or license files."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.widgets.buttons import OutlineButton, PrimaryButton
from app.ui.widgets.cards import BaseCard
from app.ui.widgets.inputs import TextInput
from app.ui.widgets.toast import Toast


class ActivationPage(QWidget):
    activation_requested = Signal(str)
    copy_requested = Signal()
    back_requested = Signal()
    support_requested = Signal()
    telegram_requested = Signal()
    zalo_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(48, 24, 48, 24)
        self.back_button = OutlineButton("←  Quay lại")
        root.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)
        title = QLabel("Kích hoạt phần mềm")
        title.setProperty("role", "title")
        root.addWidget(title)
        self.toast = Toast(plain=True)
        root.addWidget(self.toast)
        row = QHBoxLayout()
        row.setSpacing(28)
        form = BaseCard("Bản quyền MelodyAI", "Kích hoạt trải nghiệm sáng tạo của bạn.")
        form.content.addWidget(QLabel("Machine ID"))
        machine_row = QHBoxLayout()
        self.machine = TextInput("Đang đọc Machine ID…")
        self.machine.setReadOnly(True)
        self.machine.setClearButtonEnabled(False)
        self.copy_button = OutlineButton("Sao chép")
        machine_row.addWidget(self.machine, 1)
        machine_row.addWidget(self.copy_button)
        form.content.addLayout(machine_row)
        form.content.addWidget(QLabel("License Key"))
        self.license_input = TextInput("Dán license key do Admin cung cấp")
        self.license_input.setClearButtonEnabled(False)
        self.license_input.setAccessibleName("License Key")
        form.content.addWidget(self.license_input)
        self.activate_button = PrimaryButton("Kích hoạt ngay")
        form.content.addWidget(self.activate_button)
        # Keep this compact one-line form grouped at the top of the card.
        # Without a trailing stretch, wrapped QLabel rows absorb the card's
        # spare height and create large gaps between every control.
        form.content.addStretch(1)
        row.addWidget(form, 3)
        guide = BaseCard(
            "Hướng dẫn kích hoạt",
            "1. Sao chép Machine ID\n\n2. Gửi Machine ID cho Admin\n\n3. Nhận license key\n\n4. Dán key vào ô License Key\n\n5. Nhấn Kích hoạt ngay",
        )
        guide.content.addStretch()
        social_row = QHBoxLayout()
        social_row.setSpacing(10)
        self.telegram_button = OutlineButton("Telegram")
        self.telegram_button.setEnabled(False)
        self.zalo_button = OutlineButton("Zalo")
        self.zalo_button.setEnabled(False)
        social_row.addWidget(self.telegram_button)
        social_row.addWidget(self.zalo_button)
        guide.content.addLayout(social_row)
        self.support_button = OutlineButton("Liên hệ hỗ trợ")
        guide.content.addWidget(self.support_button)
        row.addWidget(guide, 2)
        root.addLayout(row, 1)
        self.back_button.clicked.connect(self.back_requested.emit)
        self.copy_button.clicked.connect(self.copy_requested.emit)
        self.support_button.clicked.connect(self.support_requested.emit)
        self.telegram_button.clicked.connect(self.telegram_requested.emit)
        self.zalo_button.clicked.connect(self.zalo_requested.emit)
        self.activate_button.clicked.connect(
            lambda: self.activation_requested.emit(self.license_input.text())
        )
        self.license_input.returnPressed.connect(self.activate_button.click)

    def set_loading(self, loading: bool) -> None:
        self.activate_button.set_loading(loading, "Đang xác minh…")
        self.license_input.setEnabled(not loading)
        self.back_button.setEnabled(not loading)

    def set_support_links(self, telegram_available: bool, zalo_available: bool) -> None:
        self.telegram_button.setEnabled(telegram_available)
        self.zalo_button.setEnabled(zalo_available)

"""The update card: version, status, release notes, progress, actions — all
in one compact card whose contents change with the state machine (see
UpdateController) instead of showing every control at once.

States: IDLE, CHECKING, UP_TO_DATE, UPDATE_AVAILABLE, DOWNLOADING,
VERIFYING, READY_TO_INSTALL, INSTALLING, ERROR.
"""

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.core.constants import APP_NAME, APP_SUBTITLE
from app.ui.pages.updates.release_notes import ReleaseNotes
from app.ui.pages.updates.update_progress import UpdateProgress, format_bytes
from app.ui.widgets.buttons import PrimaryButton
from app.ui.widgets.text_link import TextLink

_ICONS = Path(__file__).resolve().parents[3] / "assets/icons"
_IMAGES = Path(__file__).resolve().parents[3] / "assets/images"

# state -> (status icon file or None, status text template, checked_at visible)
_STATUS = {
    "IDLE": (None, "", "text"),
    "CHECKING": (None, "Đang kiểm tra phiên bản mới...", "muted"),
    "UP_TO_DATE": ("check-circle-green.svg", "Bạn đang sử dụng phiên bản mới nhất", "success"),
    "UPDATE_AVAILABLE": ("rocket-pink.svg", "Có bản cập nhật mới", "primary"),
    "DOWNLOADING": (None, "Đang tải bản cập nhật...", "muted"),
    "VERIFYING": (None, "Đang xác minh...", "muted"),
    "READY_TO_INSTALL": ("check-circle-green.svg", "Tải xuống hoàn tất · Đã xác minh file cập nhật", "success"),
    "INSTALLING": (None, "Đang chuẩn bị cập nhật...", "muted"),
    "ERROR": (None, "", "text"),
}


class UpdateCard(QFrame):
    check_requested = Signal()
    download_requested = Signal()
    cancel_requested = Signal()
    install_requested = Signal()
    dismiss_requested = Signal()
    view_release_requested = Signal()

    def __init__(self, version: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("updateCard")
        self.current_version = version
        self._primary_action = "check"
        self._secondary_action: str | None = None
        column = QVBoxLayout(self)
        column.setContentsMargins(28, 26, 28, 26)
        column.setSpacing(0)

        header = QHBoxLayout()
        header.setSpacing(12)
        logo_path = _IMAGES / "logo-mark.svg"
        if logo_path.is_file():
            logo = QSvgWidget(str(logo_path))
            logo.setFixedSize(40, 40)
            header.addWidget(logo)
        name_column = QVBoxLayout()
        name_column.setSpacing(0)
        name_label = QLabel(APP_NAME)
        name_label.setObjectName("updateAppName")
        name_column.addWidget(name_label)
        subtitle_label = QLabel(APP_SUBTITLE)
        subtitle_label.setObjectName("updateAppSubtitle")
        name_column.addWidget(subtitle_label)
        header.addLayout(name_column)
        header.addStretch(1)
        self.badge = QLabel("Có bản mới")
        self.badge.setObjectName("updateBadge")
        self.badge.hide()
        header.addWidget(self.badge, 0, Qt.AlignmentFlag.AlignTop)
        column.addLayout(header)
        column.addSpacing(18)

        version_row = QHBoxLayout()
        version_row.setSpacing(20)
        current_column = QVBoxLayout()
        current_column.setSpacing(2)
        current_caption = QLabel("Phiên bản hiện tại")
        current_caption.setObjectName("updateVersionCaption")
        current_column.addWidget(current_caption)
        self.current_version_label = QLabel(f"v{version}")
        self.current_version_label.setObjectName("updateVersionValue")
        current_column.addWidget(self.current_version_label)
        version_row.addLayout(current_column)

        self.arrow_label = QLabel("→")
        self.arrow_label.setObjectName("updateVersionArrow")
        self.arrow_label.hide()
        version_row.addWidget(self.arrow_label)

        self.latest_column = QWidget()
        latest_layout = QVBoxLayout(self.latest_column)
        latest_layout.setContentsMargins(0, 0, 0, 0)
        latest_layout.setSpacing(2)
        latest_caption = QLabel("Phiên bản mới")
        latest_caption.setObjectName("updateVersionCaption")
        latest_layout.addWidget(latest_caption)
        self.latest_version_label = QLabel("")
        self.latest_version_label.setObjectName("updateVersionValueLatest")
        latest_layout.addWidget(self.latest_version_label)
        version_row.addWidget(self.latest_column)
        self.latest_column.hide()
        version_row.addStretch(1)
        column.addLayout(version_row)
        column.addSpacing(14)

        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(16, 16)
        self.status_icon.hide()
        status_row.addWidget(self.status_icon)
        self.status_label = QLabel("")
        self.status_label.setObjectName("updateStatusText")
        self.status_label.setWordWrap(True)
        status_row.addWidget(self.status_label, 1)
        column.addLayout(status_row)
        self.checked_at_label = QLabel("")
        self.checked_at_label.setObjectName("updateCheckedAt")
        column.addWidget(self.checked_at_label)
        column.addSpacing(4)

        self.notes_label = QLabel("Có gì mới")
        self.notes_label.setObjectName("updateNotesLabel")
        column.addWidget(self.notes_label)
        self.notes = ReleaseNotes()
        column.addWidget(self.notes)
        self.size_label = QLabel("")
        self.size_label.setObjectName("updateSizeLabel")
        column.addWidget(self.size_label)
        column.addSpacing(14)

        self.progress = UpdateProgress()
        self.progress.cancel_requested.connect(self.cancel_requested.emit)
        column.addWidget(self.progress)
        column.addSpacing(10)

        self.error_box = QWidget()
        error_layout = QVBoxLayout(self.error_box)
        error_layout.setContentsMargins(0, 0, 0, 0)
        error_layout.setSpacing(6)
        error_title_row = QHBoxLayout()
        error_title_row.setSpacing(6)
        error_icon = QLabel()
        error_icon.setPixmap(QIcon(str(_ICONS / "alert-circle.svg")).pixmap(QSize(16, 16)))
        error_title_row.addWidget(error_icon)
        error_title = QLabel("Không thể cập nhật")
        error_title.setObjectName("updateErrorTitle")
        error_title_row.addWidget(error_title)
        error_title_row.addStretch(1)
        error_layout.addLayout(error_title_row)
        self.error_message_label = QLabel("")
        self.error_message_label.setObjectName("updateErrorMessage")
        self.error_message_label.setWordWrap(True)
        error_layout.addWidget(self.error_message_label)
        self.error_toggle = QPushButton("▸ Chi tiết lỗi")
        self.error_toggle.setObjectName("updateErrorToggle")
        self.error_toggle.setCheckable(True)
        self.error_toggle.setFlat(True)
        self.error_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.error_toggle.toggled.connect(self._on_error_toggle)
        error_layout.addWidget(self.error_toggle)
        self.error_detail_label = QLabel("")
        self.error_detail_label.setObjectName("updateErrorDetail")
        self.error_detail_label.setWordWrap(True)
        self.error_detail_label.hide()
        error_layout.addWidget(self.error_detail_label)
        column.addWidget(self.error_box)
        self.error_box.hide()
        column.addSpacing(6)

        actions = QHBoxLayout()
        actions.setSpacing(12)
        self.secondary_link = TextLink("")
        self.secondary_link.setObjectName("updateSecondaryLink")
        self.secondary_link.hide()
        self.secondary_link.clicked.connect(self._on_secondary_clicked)
        actions.addWidget(self.secondary_link)
        actions.addStretch(1)
        self.primary_button = PrimaryButton("Kiểm tra cập nhật")
        self.primary_button.setObjectName("updatePrimaryButton")
        self.primary_button.setIcon(QIcon(str(_ICONS / "refresh-cw.svg")))
        self.primary_button.setIconSize(QSize(15, 15))
        self.primary_button.clicked.connect(self._on_primary_clicked)
        actions.addWidget(self.primary_button)
        column.addLayout(actions)

        self.set_state("IDLE")

    def _on_error_toggle(self, checked: bool) -> None:
        self.error_detail_label.setVisible(checked)
        self.error_toggle.setText(("▾" if checked else "▸") + " Chi tiết lỗi")

    def _on_primary_clicked(self) -> None:
        signal = {
            "check": self.check_requested,
            "download": self.download_requested,
            "install": self.install_requested,
            "retry": self.check_requested,
        }.get(self._primary_action)
        if signal:
            signal.emit()

    def _on_secondary_clicked(self) -> None:
        if self._secondary_action == "view":
            self.view_release_requested.emit()
        elif self._secondary_action == "dismiss":
            self.dismiss_requested.emit()

    def _set_primary(self, text: str, action: str, icon_file: str | None, enabled: bool = True) -> None:
        self._primary_action = action
        self.primary_button.setText(text)
        self.primary_button.setEnabled(enabled)
        self.primary_button.setVisible(bool(text))
        if icon_file:
            self.primary_button.setIcon(QIcon(str(_ICONS / icon_file)))
        else:
            self.primary_button.setIcon(QIcon())

    def _set_secondary(self, text: str, action: str | None) -> None:
        self._secondary_action = action
        self.secondary_link.setText(text)
        self.secondary_link.setVisible(bool(text))

    def set_state(self, state: str, **context) -> None:
        icon_file, template, tone = _STATUS.get(state, (None, "", "text"))
        self.status_icon.setVisible(bool(icon_file))
        if icon_file:
            self.status_icon.setPixmap(QIcon(str(_ICONS / icon_file)).pixmap(QSize(16, 16)))
        self.status_label.setText(context.get("status_text", template))
        self.status_label.setProperty("tone", tone)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

        self.badge.setVisible(state == "UPDATE_AVAILABLE")
        show_latest = state in ("UPDATE_AVAILABLE", "DOWNLOADING", "VERIFYING", "READY_TO_INSTALL", "INSTALLING")
        self.arrow_label.setVisible(show_latest)
        self.latest_column.setVisible(show_latest)
        if "latest_version" in context:
            self.latest_version_label.setText(f"v{context['latest_version']}")

        self.checked_at_label.setText(context.get("checked_at", "") if state == "UP_TO_DATE" else "")
        self.checked_at_label.setVisible(bool(self.checked_at_label.text()))

        show_notes = state in ("UPDATE_AVAILABLE", "DOWNLOADING", "VERIFYING", "READY_TO_INSTALL", "INSTALLING")
        self.notes_label.setVisible(show_notes)
        self.notes.setVisible(show_notes)
        if "notes" in context:
            self.notes.set_notes(context["notes"])
        size = context.get("size", 0)
        self.size_label.setVisible(show_notes and bool(size))
        if size:
            self.size_label.setText(f"Dung lượng: {format_bytes(size)}")

        self.progress.setVisible(state in ("DOWNLOADING", "VERIFYING"))
        self.error_box.setVisible(state == "ERROR")
        if state == "ERROR":
            self.error_message_label.setText(context.get("error_summary", "Không thể cập nhật."))
            self.error_detail_label.setText(context.get("error_detail", ""))
            self.error_toggle.setChecked(False)

        if state == "IDLE":
            self._set_primary("Kiểm tra cập nhật", "check", "refresh-cw.svg")
            self._set_secondary("", None)
        elif state == "CHECKING":
            self._set_primary("Đang kiểm tra...", "check", "refresh-cw.svg", enabled=False)
            self._set_secondary("", None)
        elif state == "UP_TO_DATE":
            self._set_primary("Kiểm tra lại", "check", "refresh-cw.svg")
            self._set_secondary("", None)
        elif state == "UPDATE_AVAILABLE":
            self._set_primary("Tải bản cập nhật", "download", "download-white.svg")
            self._set_secondary("Xem chi tiết", "view" if context.get("html_url") else None)
        elif state == "DOWNLOADING":
            self._set_primary("", "download", None)
            self._set_secondary("", None)
        elif state == "VERIFYING":
            self._set_primary("", "download", None, enabled=False)
            self._set_secondary("", None)
        elif state == "READY_TO_INSTALL":
            self._set_primary("Cài đặt và khởi động lại", "install", "rocket-pink.svg")
            self._set_secondary("Để sau", "dismiss")
        elif state == "INSTALLING":
            self._set_primary("Đang chuẩn bị cập nhật...", "install", None, enabled=False)
            self._set_secondary("", None)
        elif state == "ERROR":
            self._set_primary("Thử lại", "retry", "refresh-cw.svg")
            self._set_secondary("", None)

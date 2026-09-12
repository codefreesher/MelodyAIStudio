"""Standalone admin GUI. Run python -m admin_tools.active from project root."""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QDate, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from admin_tools.key_generator import generate_keypair, generate_license
from app.models.license import FEATURES, PLANS
from app.ui.themes.theme_manager import ThemeManager
from app.ui.widgets.buttons import OutlineButton, PrimaryButton
from app.ui.widgets.dropdown import ComboBox
from app.ui.widgets.inputs import TextInput
from app.ui.widgets.toast import Toast


class AdminWindow(QWidget):
    def __init__(self, directory: Path | None = None) -> None:
        super().__init__()
        directory = directory or Path(__file__).resolve().parent
        self.private_path = directory / "private/license_private.pem"
        self.public_path = directory / "public/license_public.pem"
        self.setWindowTitle("MelodyAI — Admin License Tool")
        self.resize(660, 650)
        layout = QVBoxLayout(self)
        self.toast = Toast()
        layout.addWidget(self.toast)
        form = QFormLayout()
        self.machine = TextInput("Machine ID của khách hàng")
        self.plan = ComboBox(PLANS)
        self.expiry = QDateEdit(QDate.currentDate().addDays(30))
        self.expiry.setCalendarPopup(True)
        self.expiry.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Machine ID", self.machine)
        form.addRow("Plan", self.plan)
        form.addRow("Expiry (cuối ngày UTC)", self.expiry)
        layout.addLayout(form)
        self.features: dict[str, QCheckBox] = {}
        row = QHBoxLayout()
        for feature in FEATURES:
            checkbox = QCheckBox(feature)
            checkbox.setChecked(True)
            self.features[feature] = checkbox
            row.addWidget(checkbox)
        layout.addLayout(row)
        self.keypair_button = OutlineButton("Generate Key Pair")
        self.keypair_button.clicked.connect(self._keypair)
        layout.addWidget(self.keypair_button)
        self.generate_button = PrimaryButton("Generate License")
        self.generate_button.clicked.connect(self._generate)
        layout.addWidget(self.generate_button)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)
        self.copy_button = OutlineButton("Copy License")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(lambda: QApplication.clipboard().setText(self.output.toPlainText()))
        layout.addWidget(self.copy_button)
        self.plan.currentTextChanged.connect(lambda plan: self.expiry.setEnabled(plan != "LIFETIME"))

    def _keypair(self) -> None:
        try:
            generate_keypair(self.private_path, self.public_path)
            self.toast.show_message(
                "Đã tạo keypair. Copy public PEM vào app/assets/keys/license_public.pem để desktop verify.",
                "success",
                0,
            )
        except (OSError, ValueError):
            self.toast.show_message(
                "Không tạo được keypair. Kiểm tra quyền ghi và key đã tồn tại; không ghi đè key cũ.", "error"
            )

    def _generate(self) -> None:
        self.output.clear()
        self.copy_button.setEnabled(False)
        try:
            date = self.expiry.date()
            expiry = (
                None
                if self.plan.currentText() == "LIFETIME"
                else datetime(date.year(), date.month(), date.day(), 23, 59, 59, tzinfo=timezone.utc)
            )
            if expiry is not None and expiry <= datetime.now(timezone.utc):
                raise ValueError("Ngày hết hạn phải ở tương lai.")
            token = generate_license(
                self.private_path,
                self.machine.text(),
                self.plan.currentText(),
                expiry,
                [key for key, checkbox in self.features.items() if checkbox.isChecked()],
            )
            self.output.setPlainText(token)
            self.copy_button.setEnabled(True)
        except (OSError, ValueError, TypeError):
            self.toast.show_message(
                "Không tạo được license. Kiểm tra Machine ID, ngày hết hạn và private key.", "error"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    app = QApplication([sys.argv[0]])
    theme = ThemeManager(app)
    theme.apply()
    window = AdminWindow()
    window.show()
    if args.smoke_test:
        QTimer.singleShot(250, window.close)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

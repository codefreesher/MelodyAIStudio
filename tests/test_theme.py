"""Run with QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME=generic python -m unittest discover -s tests."""

import unittest

from PySide6.QtCore import Qt, qInstallMessageHandler
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QWidget,
)

from app.ui.main_window import MainWindow
from app.ui.themes.theme_manager import ThemeManager


class ThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        cls.manager = ThemeManager(cls.app)
        cls.manager.apply()

    def test_palette_and_reapplication(self) -> None:
        self.manager.apply()
        self.assertEqual(self.app.palette().color(QPalette.ColorRole.Window), QColor("#FFF8FB"))
        self.assertNotIn("{{", self.app.styleSheet())
        with self.assertRaises(ValueError):
            self.manager.apply("unknown")
        self.assertEqual(self.manager.current_theme, "pink_light")

    def test_widgets_render_without_stylesheet_errors(self) -> None:
        messages: list[str] = []
        previous = qInstallMessageHandler(lambda kind, context, text: messages.append(text))
        dialog = QDialog()
        try:
            layout = QGridLayout(dialog)
            widgets = []
            for role in ("primary", "secondary", "outline", "danger", "icon"):
                button = QPushButton(role)
                self.manager.set_role(button, role)
                widgets.append(button)
            disabled = QPushButton("Disabled")
            self.manager.set_role(disabled, "primary")
            disabled.setEnabled(False)
            widgets.append(disabled)
            text = QLineEdit()
            text.setPlaceholderText("Nhập nội dung…")
            widgets.extend([text, QTextEdit("MelodyAI")])
            combo = QComboBox()
            combo.addItems(["Pink Light", "Tiếng Việt", "English"])
            widgets.append(combo)
            for control in (QCheckBox("Ghi nhớ"), QRadioButton("Đã chọn")):
                control.setChecked(True)
                widgets.append(control)
            tabs = QTabWidget()
            tabs.addTab(QLabel("Nội dung"), "Tổng quan")
            tabs.addTab(QWidget(), "Chi tiết")
            widgets.append(tabs)
            items = QListWidget()
            items.addItems(["Nhạc", "Lyric", "Audio"])
            items.setCurrentRow(1)
            widgets.append(items)
            table = QTableWidget(2, 2)
            table.setHorizontalHeaderLabels(["Tên", "Trạng thái"])
            table.setItem(0, 0, QTableWidgetItem("Demo"))
            widgets.append(table)
            bar = QProgressBar()
            bar.setValue(65)
            widgets.append(bar)
            widgets.append(QScrollBar(Qt.Orientation.Horizontal))
            card = QFrame()
            self.manager.set_role(card, "card")
            self.manager.add_card_shadow(card)
            card.setMinimumHeight(40)
            widgets.append(card)
            for index, widget in enumerate(widgets):
                layout.addWidget(widget, index // 3, index % 3)
            dialog.resize(1000, 720)
            dialog.show()
            self.app.processEvents()
            self.assertFalse(dialog.grab().isNull())
            combo.showPopup()
            self.app.processEvents()
            combo.hidePopup()
            errors = [
                message
                for message in messages
                if any(term in message.lower() for term in ("parse", "unknown property", "stylesheet"))
            ]
            self.assertEqual(errors, [])
        finally:
            dialog.close()
            qInstallMessageHandler(previous)

    def test_main_window_background(self) -> None:
        window = MainWindow("test")
        window.show()
        self.app.processEvents()
        image = window.grab().toImage()
        # Sample the bottom-left resize-grip strip: the title bar is now a
        # translucent overlay and the startup page paints its own layered
        # background, so this margin is the one spot still showing the flat
        # window-chrome background token exactly.
        self.assertEqual(image.pixelColor(6, window.height() - 6), QColor("#FFF8FB"))
        window.close()


if __name__ == "__main__":
    unittest.main()

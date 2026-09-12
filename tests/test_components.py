"""Behavior checks for reusable UI components."""

import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget

from app.ui.pages.resources.resource_item import ResourceItem
from app.ui.themes.theme_manager import ThemeManager
from app.ui.widgets.buttons import PrimaryButton
from app.ui.widgets.cards import ResourceCard
from app.ui.widgets.dialog import ConfirmDialog
from app.ui.widgets.dropdown import ComboBox
from app.ui.widgets.image_gallery import ImageGallery
from app.ui.widgets.inputs import PasswordInput, SearchInput
from app.ui.widgets.progress import LoadingOverlay, ProgressDialog
from app.ui.widgets.sidebar import Sidebar
from app.ui.widgets.toast import Toast


class ComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        ThemeManager(cls.app).apply()

    def test_loading_preserves_state(self) -> None:
        button = PrimaryButton("Generate")
        clicks = []
        button.clicked.connect(lambda: clicks.append(True))
        button.set_loading(True)
        button.click()
        self.assertEqual(clicks, [])
        button.set_loading(False)
        self.assertEqual(button.text(), "Generate")
        button.click()
        self.assertEqual(clicks, [True])
        button.setEnabled(False)
        button.set_loading(True)
        button.set_loading(False)
        self.assertFalse(button.isEnabled())
        combo = ComboBox(["A", "B"])
        combo.setCurrentIndex(1)
        combo.set_loading(True)
        combo.set_loading(False)
        self.assertEqual(combo.currentText(), "B")

    def test_input_and_navigation(self) -> None:
        password = PasswordInput()
        self.assertEqual(password.echoMode(), QLineEdit.EchoMode.Password)
        password.visibility_action.trigger()
        self.assertEqual(password.echoMode(), QLineEdit.EchoMode.Normal)
        search = SearchInput()
        values = []
        search.search_requested.connect(values.append)
        search.setText("  melody  ")
        QTest.keyClick(search, Qt.Key.Key_Return)
        self.assertEqual(values, ["melody"])
        sidebar = Sidebar()
        logouts = []
        sidebar.logout_requested.connect(lambda: logouts.append(True))
        self.assertEqual(sidebar.profile_button.toolTip(), "Đăng xuất")
        sidebar.profile_button.click()
        self.assertEqual(logouts, [True])
        first = sidebar.add_item("a", "A")
        second = sidebar.add_item("b", "B")
        sidebar.set_current("a")
        second.click()
        self.assertFalse(first.isChecked())
        self.assertTrue(second.isChecked())

    def test_resource_actions_and_dialogs(self) -> None:
        card = ResourceCard("Test")
        actions = []
        card.action_requested.connect(actions.append)
        card.actions["repair"].click()
        self.assertEqual(actions, ["repair"])
        dialog = ConfirmDialog("Test", "Continue?")
        dialog.confirm_button.click()
        self.assertEqual(dialog.result(), dialog.DialogCode.Accepted)
        progress = ProgressDialog()
        cancels = []
        progress.cancel_requested.connect(lambda: cancels.append(True))
        progress.set_progress(500, 100)
        self.assertEqual(progress.bar.value(), 100)
        progress.reject()
        progress.reject()
        self.assertEqual(cancels, [True])

    def test_unconfigured_resource_still_has_download_action(self) -> None:
        item = ResourceItem({
            "id": "ollama", "name": "Ollama", "installed": False,
            "official_url": "https://ollama.com/download/windows",
        })
        requested = []
        item.download_requested.connect(lambda: requested.append(True))
        button = item.findChild(QWidget, "resourceDownloadButton")
        self.assertIsNotNone(button)
        self.assertEqual(button.text(), "Tải chính thức")
        button.click()
        self.assertEqual(requested, [True])

    def test_toast_overlay_and_gallery(self) -> None:
        host = QWidget()
        host.resize(640, 480)
        host.show()
        overlay = LoadingOverlay(host)
        overlay.set_loading(True)
        host.resize(800, 600)
        self.app.processEvents()
        self.assertEqual(overlay.size(), host.size())
        overlay.set_loading(False)
        toast = Toast(host)
        toast.show_message("Test", duration_ms=10)
        QTest.qWait(30)
        self.assertTrue(toast.isHidden())
        gallery = ImageGallery()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.png"
            pixmap = QPixmap(80, 40)
            pixmap.fill(Qt.GlobalColor.red)
            pixmap.save(str(path))
            gallery.set_images([path])
            self.assertEqual(gallery.list.count(), 1)
            gallery._open_item(gallery.list.item(0))
            self.assertTrue(gallery._preview.isVisible())
            gallery._preview.close()
            gallery.set_images([])
            self.assertTrue(gallery.list.isHidden())
        host.close()


if __name__ == "__main__":
    unittest.main()

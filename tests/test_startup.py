"""Startup routing, keyboard interaction and responsive layout checks."""

import unittest

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.controllers.startup_controller import StartupController
from app.ui.pages.startup.startup_page import StartupPage
from app.ui.themes.theme_manager import ThemeManager


class StartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        ThemeManager(cls.app).apply()

    def test_navigation_intent_and_disabled(self) -> None:
        page = StartupPage("0.1.0")
        controller = StartupController(page)
        routes = []
        controller.navigation_requested.connect(routes.append)
        page.show()
        page.login_card.setFocus()
        QTest.keyClick(page.login_card, Qt.Key.Key_Space)
        page.activation_card.click()
        self.assertEqual(routes, ["login", "activation"])
        page.login_card.setEnabled(False)
        page.login_card.click()
        self.assertEqual(len(routes), 2)
        self.assertIn("v0.1.0", page.footer.text())
        page.close()

    def test_responsive_artwork_and_cards(self) -> None:
        page = StartupPage()
        page.show()
        # Artwork is a QSvgWidget by default, or an ArtworkWidget when a
        # raster illustration is dropped into assets/images (see StartupPage).
        artwork = page.artwork
        self.assertTrue(artwork.renderer().isValid() if hasattr(artwork, "renderer") else artwork.isValid())
        for width, height in ((1100, 650), (1280, 720), (1366, 768), (1920, 1080), (2560, 1440)):
            page.resize(width, height)
            self.app.processEvents()
            self.assertEqual(page.width(), width)
            self.assertEqual(page.height(), height)
            self.assertGreaterEqual(page.login_card.height(), 132)
            self.assertGreaterEqual(page.activation_card.height(), 132)
            self.assertFalse(page.login_card.geometry().intersects(page.activation_card.geometry()))
            for widget in (page.login_card, page.activation_card, page.artwork, page.footer):
                self.assertTrue(page.rect().contains(widget.geometry()))
            self.assertFalse(page.grab().isNull())
        page.resize(1100, 650)
        self.app.processEvents()
        page.grab().save("/tmp/melody-startup-1100.png")
        page.resize(1280, 720)
        self.app.processEvents()
        page.grab().save("/tmp/melody-startup-1280.png")
        page.close()

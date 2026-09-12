"""Login behavior, session persistence and shell navigation."""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit

from app.controllers.login_controller import LoginController
from app.models.user import User
from app.providers.mock.auth_provider import MockAuthProvider
from app.security.session_manager import JsonSessionStore, SessionManager
from app.services.auth_service import AuthService
from app.ui.main_window import MainWindow
from app.ui.pages.login.login_page import LoginPage
from app.ui.themes.theme_manager import ThemeManager


class LoginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        ThemeManager(cls.app).apply()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = JsonSessionStore(Path(self.temp.name) / "session.json")
        self.service = AuthService(MockAuthProvider(), SessionManager(self.store))
        self.page = LoginPage()
        self.controller = LoginController(self.page, self.service)
        self.page.resize(1100, 650)
        self.page.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        QThreadPool.globalInstance().waitForDone(3000)
        self.app.processEvents()
        self.page.close()
        self.temp.cleanup()

    def wait_login(self) -> None:
        for _ in range(100):
            QTest.qWait(10)
            if self.controller.worker is None:
                return
        self.fail("Login worker did not finish")

    def test_empty(self) -> None:
        self.page.submit.click()
        self.assertIn("Vui lòng nhập", self.page.toast.message.text())
        self.assertIsNone(self.controller.worker)

    def test_wrong_password(self) -> None:
        self.page.identifier.setText("demo@melodyai.local")
        self.page.password.setText("wrong")
        self.page.submit.click()
        self.wait_login()
        self.assertIn("không đúng", self.page.toast.message.text())
        self.assertIsNone(self.service.sessions.current_user)
        self.assertFalse(self.store.path.exists())
        self.assertTrue(self.page.submit.isEnabled())

    def test_success_remember_and_clear(self) -> None:
        successes = []
        self.controller.authentication_successful.connect(successes.append)
        self.page.identifier.setText("demo@melodyai.local")
        self.page.password.setText("123456")
        self.page.remember.setChecked(True)
        self.page.submit.click()
        self.wait_login()
        self.assertEqual(len(successes), 1)
        self.assertEqual(successes[0].username, "demo")
        self.assertEqual(self.page.password.text(), "")
        self.assertNotIn("123456", self.store.path.read_text())
        self.assertEqual(JsonSessionStore(self.store.path).load(), "demo@melodyai.local")
        restored_page = LoginPage()
        restored = LoginController(restored_page, self.service)
        self.assertIs(restored.page, restored_page)
        self.assertTrue(restored_page.remember.isChecked())
        self.assertEqual(restored_page.identifier.text(), "demo@melodyai.local")
        self.service.login("demo", "123456", False)
        self.assertFalse(self.store.path.exists())
        restored_page.close()

    def test_show_password_and_back(self) -> None:
        self.page.password.setText("test")
        self.page.password.visibility_action.trigger()
        self.assertEqual(self.page.password.echoMode(), QLineEdit.EchoMode.Normal)
        self.page.password.visibility_action.trigger()
        self.assertEqual(self.page.password.echoMode(), QLineEdit.EchoMode.Password)
        window = MainWindow("0.1.0")
        self.window = window
        window.attach_login(self.page, self.controller)
        window.startup_page.login_card.click()
        self.assertIs(window.stack.currentWidget(), self.page)
        self.page.back_button.click()
        self.assertIs(window.stack.currentWidget(), window.startup_page)
        self.assertEqual(self.page.password.text(), "")
        window.close()

    def test_remembered_session_restores_without_password(self) -> None:
        self.service.login("demo", "123456", True)
        restored = AuthService(MockAuthProvider(), SessionManager(JsonSessionStore(self.store.path)))
        user = restored.restore_session()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "demo@melodyai.local")
        self.assertEqual(restored.sessions.current_user, user)

    def test_expired_account_clears_remembered_session(self) -> None:
        class ExpiredProvider(MockAuthProvider):
            def restore_session(self, identifier: str) -> User:
                return User(
                    "expired",
                    "expired",
                    identifier,
                    "PRO",
                    (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
                )

        self.store.save("expired@example.com")
        restored = AuthService(ExpiredProvider(), SessionManager(self.store))
        with self.assertRaisesRegex(Exception, "hết hạn"):
            restored.restore_session()
        self.assertFalse(self.store.path.exists())

    def test_render(self) -> None:
        # Artwork is a CoverImage (see LoginPage); kept generic in case a
        # future variant renders differently.
        artwork = self.page.artwork
        self.assertTrue(artwork.renderer().isValid() if hasattr(artwork, "renderer") else artwork.isValid())
        self.page.grab().save("/tmp/melody-login-1100.png")

"""Admin issuance through activation UI using disposable keys."""

import tempfile
import unittest
from pathlib import Path

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from admin_tools.active import AdminWindow
from app.controllers.activation_controller import ActivationController
from app.security.license_manager import LicenseManager
from app.security.license_verifier import LicenseVerifier
from app.security.machine_id import get_machine_id
from app.services.activation_service import ActivationService
from app.ui.pages.activation.activation_page import ActivationPage
from app.ui.themes.theme_manager import ThemeManager


class ActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        ThemeManager(cls.app).apply()

    def test_admin_to_desktop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            admin = AdminWindow(root)
            admin.keypair_button.click()
            machine = get_machine_id()
            self.assertEqual(machine, get_machine_id())
            admin.machine.setText(machine)
            admin.plan.setCurrentText("LIFETIME")
            self.assertFalse(admin.expiry.isEnabled())
            admin.generate_button.click()
            token = admin.output.toPlainText()
            self.assertTrue(token.startswith("MLAI1."))
            manager = LicenseManager(LicenseVerifier(admin.public_path), machine, root / "saved.token")
            page = ActivationPage()
            controller = ActivationController(page, ActivationService(manager, machine))
            results = []
            controller.activation_successful.connect(results.append)
            page.resize(1100, 650)
            page.show()
            page.copy_button.click()
            self.assertEqual(QApplication.clipboard().text(), machine)
            page.activate_button.click()
            self.assertIn("Vui lòng nhập", page.toast.message.text())
            page.license_input.setText(token)
            page.activate_button.click()
            for _ in range(100):
                QTest.qWait(10)
                if controller.worker is None:
                    break
            self.assertIsNone(controller.worker)
            self.assertEqual(len(results), 1)
            self.assertEqual(manager.load().plan, "LIFETIME")
            page.grab().save("/tmp/melody-activation.png")
            page.close()
            admin.close()

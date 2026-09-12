"""End-to-end Qt workspace checks using disposable user data and mock outputs."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtTest import QTest

from app.application import Application
from app.core.config import AppConfig
from app.core.paths import AppPaths


def wait_until(predicate, milliseconds: int = 15000) -> None:
    for _ in range(milliseconds // 20):
        QTest.qWait(20)
        if predicate():
            return
    raise AssertionError("Timed out waiting for UI operation")


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        paths = AppPaths(Path(directory))
        paths.ensure_directories()
        app = Application(
            [], AppConfig(check_updates_automatically=False), paths,
            (Path(__file__).resolve().parents[1] / "VERSION").read_text().strip(),
        )
        app.window.show()
        app.qt.processEvents()
        app.window.startup_page.login_card.click()
        assert app.window.stack.currentWidget() is app.window.login_page
        app.window.login_page.back_button.click()
        app.window.startup_page.activation_card.click()
        assert app.window.stack.currentWidget() is app.window.activation_page
        app.activation_controller.back_requested.emit()
        for width, height in [(1100, 650), (1366, 768), (1920, 1080)]:
            app.window.resize(width, height)
            QTest.qWait(20)
            assert app.window.width() == width
            assert app.window.height() == height
        assert app.window.stack.currentWidget() is app.window.startup_page
        app.window.close()
        app.qt.processEvents()
    print("Workspace QA passed: startup routes, resize and shutdown.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

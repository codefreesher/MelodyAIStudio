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
            [], AppConfig(), paths, (Path(__file__).resolve().parents[1] / "VERSION").read_text().strip()
        )
        app.window.show()
        app.window.startup_page.login_card.click()
        login = app.window.login_page
        login.identifier.setText("demo@melodyai.local")
        login.password.setText("123456")
        login.submit.click()
        wait_until(lambda: app.studio is not None and app.login_controller.worker is None)
        studio = app.studio
        for controller in studio.generators:
            kind = controller.page.kind
            studio.view.navigate(kind)
            page = controller.page
            page.prompts[0].setPlainText("Bình minh trên biển")
            if kind == "lyric":
                page.extra.setChecked(True)
                page.options["count"].setCurrentText("3")
            if kind == "image":
                page.options["count"].setCurrentText("4")
            if kind == "audio":
                page.options["format"].setCurrentText("WAV")
            page.generate_button.click()
            wait_until(lambda: controller.worker is None)
            assert controller.result is not None, page.toast.message.text()
            if kind == "lyric":
                assert page.editors.count() == 3
                page.editors.widget(0).setPlainText("Edited lyric")
            page.save_button.click()
            wait_until(lambda: controller.worker is None)
        studio.view.navigate("history")
        assert studio.history_page.table.rowCount() == 4
        studio.history_page.tabs.setCurrentIndex(2)
        assert studio.history_page.table.rowCount() == 1
        studio.history_page.sort.setCurrentIndex(1)
        assert studio.history_page.table.rowCount() == 1
        for route in studio.view.pages:
            studio.view.navigate(route)
            QTest.qWait(50)
            wait_until(lambda: not studio.busy())
        studio.settings_controller.page.language.setCurrentText("en")
        studio.settings_controller.save(studio.settings_controller.page.values())
        assert studio.view.sidebar.items["dashboard"].text() == "Home"
        studio.settings_controller.page.language.setCurrentText("vi")
        studio.settings_controller.save(studio.settings_controller.page.values())
        assert studio.view.sidebar.items["dashboard"].text() == "Trang chủ"
        studio.settings_controller.page.theme.setCurrentText("pink_dark")
        studio.settings_controller.save(studio.settings_controller.page.values())
        assert app.theme_manager.current_theme == "pink_dark"
        studio.settings_controller.page.theme.setCurrentText("pink_light")
        studio.settings_controller.save(studio.settings_controller.page.values())
        for width, height in [(1100, 650), (1366, 768), (1920, 1080)]:
            app.window.resize(width, height)
            QTest.qWait(20)
            assert app.window.width() == width
            assert app.window.height() == height
        studio.logout()
        assert app.window.stack.currentWidget() is app.window.startup_page
        app.window.close()
    print("Workspace QA passed: login, 4 generators, edits/save, history, routes, themes, resize, logout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

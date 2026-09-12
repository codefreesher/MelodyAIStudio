"""Shared asynchronous controller for all creative tools."""

from pathlib import Path

from PySide6.QtCore import QObject, QThreadPool, Signal, Slot
from PySide6.QtWidgets import QApplication, QFileDialog

from app.services.ai_service import AIService
from app.ui.pages.generation_page import GenerationPage
from app.utils.async_utils import Worker


class GenerationController(QObject):
    saved = Signal()

    def __init__(self, page: GenerationPage, service: AIService) -> None:
        super().__init__(page)
        self.page, self.service = page, service
        self.result = None
        self.worker = None
        page.generate_requested.connect(self.generate)
        page.cancel_requested.connect(service.cancel)
        page.save_requested.connect(self.save)
        page.export_requested.connect(self.export)
        page.copy_requested.connect(self.copy)
        page.import_requested.connect(self.import_file)
        if page.player:
            page.player.error.connect(lambda message: page.toast.show_message(message, "error"))

    @Slot(str, dict)
    def generate(self, prompt: str, options: dict) -> None:
        if self.worker:
            return
        self.operation = "generate"
        self.service.prepare()
        self.page.set_loading(True)
        self.page.set_result_enabled(False)
        self.worker = Worker(lambda: self.service.generate(prompt, options))
        self.worker.signals.result.connect(self._result)
        self.worker.signals.error.connect(self._error)
        self.worker.signals.finished.connect(self._finished)
        QThreadPool.globalInstance().start(self.worker)

    @Slot(object)
    def _result(self, result: object) -> None:
        if self.operation != "generate":
            if self.operation == "save":
                self.saved.emit()
            self.page.toast.show_message(
                "Đã lưu lịch sử." if self.operation == "save" else "Đã xuất kết quả.", "success"
            )
            return
        self.result = result
        texts = [path.read_text(encoding="utf-8") for path in result.paths] if result.type == "lyric" else []
        self.page.show_result(result, texts)
        self.page.toast.show_message("Đã tạo kết quả. Nhấn Lưu lịch sử để lưu dự án.", "success")

    @Slot(object)
    def _error(self, error: Exception) -> None:
        self.page.toast.show_message(
            str(error) if isinstance(error, ValueError) else "Không thể xử lý tác vụ.", "error"
        )

    @Slot()
    def _finished(self) -> None:
        self.worker = None
        self.page.set_loading(False)
        self.page.set_result_enabled(self.result is not None)

    def run_file_action(self, operation: str, function) -> None:
        if self.worker:
            return
        self.operation = operation
        self.page.set_loading(True)
        self.page.cancel_button.setEnabled(False)
        self.page.set_result_enabled(False)
        self.worker = Worker(function)
        self.worker.signals.result.connect(self._result)
        self.worker.signals.error.connect(self._error)
        self.worker.signals.finished.connect(self._finished)
        QThreadPool.globalInstance().start(self.worker)

    def save(self) -> None:
        if self.result:
            texts = [self.page.editors.widget(i).toPlainText() for i in range(self.page.editors.count())]
            result = self.result
            self.run_file_action(
                "save", lambda: self.service.save(result, texts if result.type == "lyric" else None)
            )

    def export(self) -> None:
        if self.result:
            folder = QFileDialog.getExistingDirectory(self.page, "Chọn thư mục xuất")
            if folder:
                result = self.result
                texts = [self.page.editors.widget(i).toPlainText() for i in range(self.page.editors.count())]

                def export_files():
                    if result.type == "lyric":
                        for path, text in zip(result.paths, texts):
                            path.write_text(text, encoding="utf-8")
                    self.service.download(result, Path(folder))

                self.run_file_action("export", export_files)

    def copy(self) -> None:
        editor = self.page.editors.currentWidget()
        if editor:
            QApplication.clipboard().setText(editor.toPlainText())

    def import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self.page, "Nhập nội dung", "", "Text (*.txt);;Images (*.png *.jpg)"
        )
        if path:
            try:
                if Path(path).suffix.lower() == ".txt":
                    if Path(path).stat().st_size > 200000:
                        raise ValueError("File quá lớn.")
                    self.page.prompts[self.page.tabs.currentIndex()].setPlainText(
                        Path(path).read_text(encoding="utf-8")
                    )
                elif self.page.kind == "image":
                    self.page.toast.show_message("Đã chọn ảnh tham khảo.")
                    self.page.prompts[1].setPlainText(f"Ảnh tham khảo: {Path(path).name}")
                    self.page.tabs.setCurrentIndex(1)
            except (OSError, ValueError):
                self.page.toast.show_message("Không thể đọc tệp TXT UTF-8.", "error")

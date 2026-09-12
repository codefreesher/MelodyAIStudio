"""History filters, preview and exports."""

from pathlib import Path

from PySide6.QtCore import QObject, QThreadPool, QUrl, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog

from app.services.history_service import HistoryService
from app.ui.pages.history.history_page import HistoryPage
from app.ui.widgets.dialog import ConfirmDialog
from app.utils.async_utils import Worker


class HistoryController(QObject):
    def __init__(self, page: HistoryPage, service: HistoryService) -> None:
        super().__init__(page)
        self.page, self.service, self.index, self.rows = page, service, 0, []
        self.dialog = None
        self.worker = None
        page.refresh_requested.connect(self.reset)
        page.page_requested.connect(self.turn)
        page.action_requested.connect(self.action)

    def reset(self) -> None:
        self.index = 0
        self.refresh()

    def turn(self, delta: int) -> None:
        self.index = max(0, self.index + delta)
        self.refresh()

    def refresh(self) -> None:
        kind = ["", "music", "lyric", "audio", "image"][self.page.tabs.currentIndex()]
        self.rows, total = self.service.list(
            kind=kind,
            search=self.page.search.text(),
            page=self.index,
            ascending=self.page.sort.currentIndex() == 1,
        )
        if not self.rows and self.index:
            self.index -= 1
            return self.refresh()
        self.page.show_rows(self.rows, total, self.index)

    def action(self, action: str, index: int) -> None:
        if self.worker:
            return
        if index < 0 or index >= len(self.rows):
            self.page.toast.show_message("Chọn một kết quả trước.")
            return
        row = self.rows[index]
        if action == "delete":
            self.dialog = ConfirmDialog(
                "Xóa lịch sử", "Xóa bản ghi này? Tệp kết quả vẫn được giữ lại.", self.page, True
            )
            self.dialog.accepted.connect(lambda: self._delete(row["uuid"]))
            self.dialog.open()
        elif action == "export":
            folder = QFileDialog.getExistingDirectory(self.page, "Thư mục xuất")
            if folder:
                self.worker = Worker(lambda: self.service.export(row, Path(folder)))
                self.worker.signals.result.connect(self._exported)
                self.worker.signals.error.connect(self._export_error)
                self.worker.signals.finished.connect(self._export_finished)
                QThreadPool.globalInstance().start(self.worker)
        else:
            path = Path(row["result_path"])
            if not path.is_file():
                self.page.toast.show_message("Tệp kết quả không còn tồn tại.", "error")
                return
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _delete(self, uuid: str) -> None:
        self.service.delete(uuid)
        self.refresh()

    @Slot(object)
    def _exported(self, value):
        self.page.toast.show_message("Đã xuất kết quả.", "success")

    @Slot(object)
    def _export_error(self, error):
        self.page.toast.show_message("Không thể xuất tệp kết quả.", "error")

    @Slot()
    def _export_finished(self):
        self.worker = None

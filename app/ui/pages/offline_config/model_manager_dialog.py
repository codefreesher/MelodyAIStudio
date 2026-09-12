"""Ollama model manager: list installed models, pull new ones, delete, cancel.

Talks to OfflineConfigService directly (via its own Worker jobs), fully
independent of the shared ConfigController — that controller has no notion
of "list models" or a per-row delete, and the reference's dialog needs its
own pull-with-progress + cancel flow anyway.
"""

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.buttons import OutlineButton, PrimaryButton
from app.ui.widgets.text_link import TextLink
from app.utils.async_utils import Worker


def _format_size(size: int) -> str:
    if not size:
        return ""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{int(value)}{unit}" if unit == "B" else f"{value:.1f}{unit}"
        value /= 1024
    return f"{value:.1f}TB"


class ModelManagerDialog(QDialog):
    def __init__(self, service, provider_name: str, provider_data: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self.provider_name = provider_name
        self.provider_data = provider_data
        self.worker: Worker | None = None
        self._pending_refresh = False
        self.setObjectName("modelManagerDialog")
        self.setWindowTitle("Quản lý model Ollama")
        self.setMinimumWidth(420)

        root = QVBoxLayout(self)

        installed_label = QLabel("Đã cài")
        installed_label.setObjectName("modelSectionLabel")
        root.addWidget(installed_label)
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("modelList")
        root.addWidget(self.list_widget)

        pull_label = QLabel("Tải model")
        pull_label.setObjectName("modelSectionLabel")
        root.addWidget(pull_label)
        pull_row = QHBoxLayout()
        pull_row.setSpacing(8)
        self.pull_input = QLineEdit()
        self.pull_input.setObjectName("modelPullInput")
        self.pull_input.setPlaceholderText("qwen2.5:7b")
        pull_row.addWidget(self.pull_input, 1)
        self.pull_button = PrimaryButton("Pull")
        self.pull_button.setObjectName("modelPullButton")
        self.pull_button.clicked.connect(self._pull)
        pull_row.addWidget(self.pull_button)
        root.addLayout(pull_row)

        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("modelProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        progress_row.addWidget(self.progress_bar, 1)
        self.cancel_link = TextLink("Hủy")
        self.cancel_link.setObjectName("modelCancelLink")
        self.cancel_link.hide()
        self.cancel_link.clicked.connect(self._cancel)
        progress_row.addWidget(self.cancel_link)
        root.addLayout(progress_row)

        self.status_label = QLabel("")
        self.status_label.setObjectName("modelManagerStatus")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        close_row = QHBoxLayout()
        close_row.addStretch(1)
        self.close_button = OutlineButton("Đóng")
        self.close_button.clicked.connect(self.close)
        close_row.addWidget(self.close_button)
        root.addLayout(close_row)

        self._refresh()

    # -- plain (no-progress) jobs: list + delete ---------------------------

    def _run(self, function, on_result) -> None:
        if self.worker:
            return
        self.service.cancel_event.clear()
        self.worker = Worker(function)
        self.worker.signals.result.connect(on_result)
        self.worker.signals.error.connect(self._on_error)
        self.worker.signals.finished.connect(self._on_finished)
        QThreadPool.globalInstance().start(self.worker)

    def _refresh(self) -> None:
        self._run(lambda: self.service.list_models(self.provider_name, self.provider_data), self._on_list)

    def _on_list(self, models: object) -> None:
        self.list_widget.clear()
        for item in models:
            row = QWidget()
            row.setObjectName("modelListRow")
            layout = QHBoxLayout(row)
            layout.setContentsMargins(8, 4, 8, 4)
            layout.setSpacing(8)
            name_label = QLabel(item["name"])
            name_label.setObjectName("modelItemName")
            layout.addWidget(name_label, 1)
            size_label = QLabel(_format_size(item.get("size", 0)))
            size_label.setObjectName("modelItemSize")
            layout.addWidget(size_label)
            delete_button = QPushButton("Xóa")
            delete_button.setObjectName("modelDeleteButton")
            delete_button.clicked.connect(lambda _checked=False, name=item["name"]: self._delete(name))
            layout.addWidget(delete_button)
            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(row.sizeHint())
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, row)

    def _delete(self, model: str) -> None:
        data = dict(self.provider_data, model=model)
        self._run(lambda: self.service.delete(self.provider_name, data), self._on_delete_done)

    def _on_delete_done(self, message: object) -> None:
        self.status_label.setText(str(message))
        self._pending_refresh = True

    # -- pull job: needs its own Worker to wire the progress signal --------

    def _pull(self) -> None:
        model = self.pull_input.text().strip()
        if self.worker or not model:
            return
        data = dict(self.provider_data, model=model)
        self.service.cancel_event.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.cancel_link.show()
        self.pull_button.setEnabled(False)
        self.worker = Worker(lambda: self.service.pull(self.provider_name, data, self.worker.signals.progress.emit))
        self.worker.signals.progress.connect(self.progress_bar.setValue)
        self.worker.signals.result.connect(self._on_pull_done)
        self.worker.signals.error.connect(self._on_error)
        self.worker.signals.finished.connect(self._on_finished)
        QThreadPool.globalInstance().start(self.worker)

    def _on_pull_done(self, message: object) -> None:
        self.status_label.setText(str(message))
        self.pull_input.clear()
        self._pending_refresh = True

    def _cancel(self) -> None:
        self.service.cancel_event.set()

    # -- shared completion path ---------------------------------------------

    def _on_error(self, error: object) -> None:
        self.status_label.setText(str(error) if isinstance(error, ValueError) else "Không thể thực hiện.")

    def _on_finished(self) -> None:
        # result (if any) is always delivered before finished — safe to act
        # on _pending_refresh here, and only here, since self.worker must be
        # cleared first or the guard in _run()/_pull() would block it.
        self.worker = None
        self.progress_bar.hide()
        self.cancel_link.hide()
        self.pull_button.setEnabled(True)
        if self._pending_refresh:
            self._pending_refresh = False
            self._refresh()

    def closeEvent(self, event) -> None:  # noqa: ANN001 - Qt signature
        self.service.cancel_event.set()
        super().closeEvent(event)

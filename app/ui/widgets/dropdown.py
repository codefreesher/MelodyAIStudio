"""Shared combo box with a reversible loading placeholder."""

from collections.abc import Iterable

from PySide6.QtWidgets import QComboBox, QWidget


class ComboBox(QComboBox):
    def __init__(self, items: Iterable[str] = (), parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.addItems(list(items))
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.setMinimumContentsLength(12)
        self._loading = False

    def set_loading(self, loading: bool) -> None:
        if loading == self._loading:
            return
        self._loading = loading
        if loading:
            self._previous = (self.currentIndex(), self.placeholderText(), self.isEnabled())
            self.setPlaceholderText("Đang tải…")
            self.setCurrentIndex(-1)
            self.setEnabled(False)
        else:
            index, placeholder, enabled = self._previous
            self.setPlaceholderText(placeholder)
            self.setCurrentIndex(index if index < self.count() else -1)
            self.setEnabled(enabled)

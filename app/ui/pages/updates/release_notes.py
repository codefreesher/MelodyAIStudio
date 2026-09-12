"""Render GitHub release notes as a compact, scrollable bullet list.

No markdown/HTML rendering, no raw JSON — ``release.notes`` is GitHub's raw
release-body text; this only extracts bullet-style lines for a clean list,
falling back to plain wrapped text for anything else.
"""

import re

from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

_BULLET = re.compile(r"^\s*[-*•]\s+(.*)")


class ReleaseNotes(QScrollArea):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("releaseNotesScroll")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setMaximumHeight(150)
        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self.setWidget(container)

    def set_notes(self, text: str) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        lines = [line for line in (text or "").splitlines() if line.strip()]
        bullets = [match.group(1) for line in lines if (match := _BULLET.match(line))]
        if bullets:
            for entry in bullets:
                label = QLabel(f"•  {entry}")
                label.setObjectName("releaseNoteItem")
                label.setWordWrap(True)
                self._layout.addWidget(label)
        elif lines:
            label = QLabel("\n".join(lines))
            label.setObjectName("releaseNoteItem")
            label.setWordWrap(True)
            self._layout.addWidget(label)
        else:
            label = QLabel("Không có ghi chú phát hành.")
            label.setObjectName("releaseNoteEmpty")
            self._layout.addWidget(label)
        self._layout.addStretch(1)

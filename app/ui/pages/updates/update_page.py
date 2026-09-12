"""Compose the Update page: a heading plus one compact, capped-width card.

No Owner/Repository fields — the GitHub source is fixed app configuration
(see app/core/constants.py), not something an ordinary user edits here.
"""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.pages.updates.update_card import UpdateCard
from app.ui.widgets.toast import Toast


class UpdatePage(QWidget):
    def __init__(self, version: str) -> None:
        super().__init__()
        self.setObjectName("updatePage")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(14)

        heading = QLabel("Cập nhật ứng dụng")
        heading.setObjectName("updateHeading")
        root.addWidget(heading)

        self.toast = Toast(plain=True)
        root.addWidget(self.toast)

        card_row = QHBoxLayout()
        self.card = UpdateCard(version)
        self.card.setMinimumWidth(480)
        self.card.setMaximumWidth(620)
        card_row.addWidget(self.card)
        card_row.addStretch(1)
        root.addLayout(card_row)
        root.addStretch(1)

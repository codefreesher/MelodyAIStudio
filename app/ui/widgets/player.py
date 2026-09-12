"""Local audio playback through Qt Multimedia; no network/provider calls."""

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSlider, QStyle, QVBoxLayout, QWidget

from app.ui.widgets.buttons import IconButton


class AudioPlayer(QFrame):
    error = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("role", "card")
        self.media = QMediaPlayer(self)
        self.output = QAudioOutput(self)
        self.output.setVolume(0.7)
        self.media.setAudioOutput(self.output)
        layout = QVBoxLayout(self)
        self.title = QLabel("Chưa có audio")
        layout.addWidget(self.title)
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0, 0)
        self.seek.setAccessibleName("Vị trí phát")
        layout.addWidget(self.seek)
        row = QHBoxLayout()
        self.play_button = IconButton(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay), "Phát / Tạm dừng"
        )
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.toggle_playback)
        row.addWidget(self.play_button)
        self.time = QLabel("0:00 / 0:00")
        row.addWidget(self.time)
        row.addStretch()
        self.volume_label = QLabel("Âm lượng")
        row.addWidget(self.volume_label)
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(70)
        self.volume.setMaximumWidth(120)
        self.volume.setAccessibleName("Âm lượng")
        self.volume.valueChanged.connect(lambda value: self.output.setVolume(value / 100))
        row.addWidget(self.volume)
        layout.addLayout(row)
        self.seek.sliderMoved.connect(self.media.setPosition)
        self.seek.sliderReleased.connect(lambda: self.media.setPosition(self.seek.value()))
        self.media.positionChanged.connect(self._position_changed)
        self.media.durationChanged.connect(self._duration_changed)
        self.media.playbackStateChanged.connect(self._state_changed)
        self.media.errorOccurred.connect(self._error)
        self.media.mediaStatusChanged.connect(self._status_changed)

    def set_source(self, path: str | Path) -> None:
        source = Path(path).expanduser().resolve()
        self.media.stop()
        if not source.is_file():
            self.media.setSource(QUrl())
            self.title.setText("Không tìm thấy audio")
            self.play_button.setEnabled(False)
            self.error.emit("Không tìm thấy tệp audio.")
            return
        self.title.setText(source.name)
        self.media.setSource(QUrl.fromLocalFile(str(source)))

    def toggle_playback(self) -> None:
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media.pause()
        else:
            self.media.play()

    def _status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        busy = status in (QMediaPlayer.MediaStatus.LoadingMedia, QMediaPlayer.MediaStatus.StalledMedia)
        self.play_button.set_loading(busy, "")
        if not busy:
            self.play_button.setEnabled(
                status not in (QMediaPlayer.MediaStatus.NoMedia, QMediaPlayer.MediaStatus.InvalidMedia)
            )
        self.seek.setEnabled(self.media.isSeekable() and not busy)

    def _state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        icon = (
            QStyle.StandardPixmap.SP_MediaPause
            if state == QMediaPlayer.PlaybackState.PlayingState
            else QStyle.StandardPixmap.SP_MediaPlay
        )
        self.play_button.setIcon(self.style().standardIcon(icon))

    def _duration_changed(self, duration: int) -> None:
        self.seek.setRange(0, duration)
        self._position_changed(self.media.position())

    def _position_changed(self, position: int) -> None:
        if not self.seek.isSliderDown():
            self.seek.setValue(position)
        self.time.setText(f"{self._format_time(position)} / {self._format_time(self.media.duration())}")

    @staticmethod
    def _format_time(milliseconds: int) -> str:
        seconds = max(0, milliseconds // 1000)
        return f"{seconds // 60}:{seconds % 60:02d}"

    def _error(self, error: QMediaPlayer.Error, message: str) -> None:
        self.play_button.set_loading(False)
        self.play_button.setEnabled(False)
        self.title.setText("Không thể phát audio")
        self.error.emit("Không thể phát tệp audio. Kiểm tra định dạng hoặc thiết bị âm thanh.")

    def closeEvent(self, event: object) -> None:
        self.media.stop()
        super().closeEvent(event)

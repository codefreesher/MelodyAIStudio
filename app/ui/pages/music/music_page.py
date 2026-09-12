"""Dedicated MelodyAI music-generation workspace."""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QSlider,
    QStyle,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.buttons import IconButton, OutlineButton, PrimaryButton
from app.ui.widgets.dropdown import ComboBox
from app.ui.widgets.toast import Toast
from app.ui.widgets.toggle import ToggleSwitch
from app.ui.widgets.waveform import Waveform

_IMAGES = Path(__file__).resolve().parents[3] / "assets/images"


class RotatingMusicCover(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("musicCover")
        self.setFixedSize(190, 190)
        self._source = QPixmap(str(_IMAGES / "default_music_cover.png"))
        self._angle = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._advance)

    def set_playing(self, state: QMediaPlayer.PlaybackState) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._timer.start()
        else:
            self._timer.stop()

    def _advance(self) -> None:
        self._angle = (self._angle + 0.55) % 360
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002 - Qt signature
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#FFF0F6"))
        painter.drawRoundedRect(self.rect(), 14, 14)
        if self._source.isNull():
            return
        artwork = self._source.scaled(
            176,
            176,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)
        painter.drawPixmap(-artwork.width() // 2, -artwork.height() // 2, artwork)


class MusicPlayer(QFrame):
    error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("musicPlayer")
        self.media = QMediaPlayer(self)
        self.output = QAudioOutput(self)
        self.output.setVolume(0.7)
        self.media.setAudioOutput(self.output)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0, 0)
        self.seek.setAccessibleName("Vị trí phát")
        layout.addWidget(self.seek)
        time_row = QHBoxLayout()
        self.current_time = QLabel("0:00")
        self.duration_time = QLabel("0:00")
        for label in (self.current_time, self.duration_time):
            label.setObjectName("musicPlayerTime")
        time_row.addWidget(self.current_time)
        time_row.addStretch(1)
        time_row.addWidget(self.duration_time)
        layout.addLayout(time_row)
        controls = QHBoxLayout()
        controls.addStretch(1)
        self.previous_button = IconButton(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipBackward), "Về đầu"
        )
        self.play_button = IconButton(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay), "Phát / Tạm dừng"
        )
        self.play_button.setObjectName("musicPlayButton")
        self.next_button = IconButton(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward), "Đến cuối"
        )
        for button in (self.previous_button, self.play_button, self.next_button):
            button.setEnabled(False)
            controls.addWidget(button)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.previous_button.clicked.connect(lambda: self.media.setPosition(0))
        self.next_button.clicked.connect(lambda: self.media.setPosition(self.media.duration()))
        self.play_button.clicked.connect(self.toggle_playback)
        self.seek.sliderMoved.connect(self.media.setPosition)
        self.seek.sliderReleased.connect(lambda: self.media.setPosition(self.seek.value()))
        self.media.positionChanged.connect(self._position_changed)
        self.media.durationChanged.connect(self._duration_changed)
        self.media.playbackStateChanged.connect(self._state_changed)
        self.media.mediaStatusChanged.connect(self._status_changed)
        self.media.errorOccurred.connect(self._error)

    def set_source(self, path: str | Path) -> None:
        source = Path(path).expanduser().resolve()
        self.media.stop()
        if not source.is_file():
            self.media.setSource(QUrl())
            self._set_controls_enabled(False)
            self.error.emit("Không tìm thấy tệp audio.")
            return
        self.media.setSource(QUrl.fromLocalFile(str(source)))

    def toggle_playback(self) -> None:
        if self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media.pause()
        else:
            self.media.play()

    def _set_controls_enabled(self, enabled: bool) -> None:
        for button in (self.previous_button, self.play_button, self.next_button):
            button.setEnabled(enabled)

    def _status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        ready = status not in (
            QMediaPlayer.MediaStatus.NoMedia,
            QMediaPlayer.MediaStatus.InvalidMedia,
            QMediaPlayer.MediaStatus.LoadingMedia,
        )
        self._set_controls_enabled(ready)
        self.seek.setEnabled(ready and self.media.isSeekable())

    def _state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        icon = (
            QStyle.StandardPixmap.SP_MediaPause
            if state == QMediaPlayer.PlaybackState.PlayingState
            else QStyle.StandardPixmap.SP_MediaPlay
        )
        self.play_button.setIcon(self.style().standardIcon(icon))

    def _duration_changed(self, duration: int) -> None:
        self.seek.setRange(0, duration)
        self.duration_time.setText(self._format_time(duration))

    def _position_changed(self, position: int) -> None:
        if not self.seek.isSliderDown():
            self.seek.setValue(position)
        self.current_time.setText(self._format_time(position))

    def _error(self, error: QMediaPlayer.Error, message: str) -> None:  # noqa: ARG002
        self._set_controls_enabled(False)
        self.error.emit("Không thể phát tệp audio. Kiểm tra định dạng hoặc thiết bị âm thanh.")

    @staticmethod
    def _format_time(milliseconds: int) -> str:
        seconds = max(0, milliseconds // 1000)
        return f"{seconds // 60}:{seconds % 60:02d}"


class MusicPage(QWidget):
    generate_requested = Signal(str, dict)
    cancel_requested = Signal()
    save_requested = Signal()
    export_requested = Signal()
    import_requested = Signal()
    copy_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.kind = "music"
        self.setObjectName("musicPage")
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 20)
        root.setSpacing(10)

        heading_row = QHBoxLayout()
        heading_icon = QLabel("♫")
        heading_icon.setObjectName("musicHeadingIcon")
        heading = QLabel("Tạo nhạc")
        heading.setObjectName("musicHeading")
        heading_row.addWidget(heading_icon)
        heading_row.addWidget(heading)
        heading_row.addStretch(1)
        root.addLayout(heading_row)
        self.toast = Toast(plain=True)
        root.addWidget(self.toast)

        workspace = QHBoxLayout()
        workspace.setSpacing(16)
        root.addLayout(workspace, 1)
        form_panel = QWidget()
        form_panel.setObjectName("musicFormPanel")
        form = QVBoxLayout(form_panel)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)
        workspace.addWidget(form_panel, 58)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("musicTabs")
        self.prompts: list[QPlainTextEdit] = []
        placeholders = [
            "Nhập mô tả bài hát của bạn…\nVí dụ: Bài hát về tuổi trẻ, phong cách Pop, vui tươi…",
            "Dán lời bài hát có sẵn vào đây…",
            "Mô tả chi tiết cấu trúc, nhạc cụ và phong cách…",
        ]
        for caption, placeholder in zip(
            ("Từ prompt", "Từ lyric có sẵn", "Tùy chỉnh nâng cao"), placeholders
        ):
            editor = QPlainTextEdit()
            editor.setPlaceholderText(placeholder)
            editor.setObjectName("musicPrompt")
            self.tabs.addTab(editor, caption)
            self.prompts.append(editor)
        form.addWidget(self.tabs, 1)

        self.import_button = OutlineButton("Nhập file TXT")
        self.import_button.setObjectName("musicImport")
        self.import_button.clicked.connect(self.import_requested.emit)
        form.addWidget(self.import_button)

        options_row = QHBoxLayout()
        options_row.setSpacing(8)
        self.options: dict[str, ComboBox] = {}
        choices = {
            "genre": ("Thể loại", ["Pop", "Ballad", "Jazz", "Rock"]),
            "mood": ("Tâm trạng", ["Vui vẻ", "Thư giãn", "Buồn"]),
            "language": ("Ngôn ngữ", ["Vietnamese", "English"]),
            "duration": ("Thời lượng", ["6", "15", "30"]),
        }
        for key, (caption, values) in choices.items():
            field_column = QVBoxLayout()
            label = QLabel(caption)
            label.setObjectName("musicOptionLabel")
            field = ComboBox(values)
            self.options[key] = field
            field_column.addWidget(label)
            field_column.addWidget(field)
            options_row.addLayout(field_column, 1)
        form.addLayout(options_row)
        self.options["provider"] = ComboBox(["Auto", "Online", "Local"])
        self.options["provider"].hide()

        self.extra = ToggleSwitch("Tạo kèm lyric")
        self.extra.setObjectName("musicIncludeLyric")
        form.addWidget(self.extra)
        self.generate_button = PrimaryButton("♫   Tạo nhạc")
        self.generate_button.setObjectName("musicGenerate")
        self.cancel_button = OutlineButton("Hủy tác vụ")
        self.cancel_button.setObjectName("musicCancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.hide()
        form.addWidget(self.generate_button)
        form.addWidget(self.cancel_button)
        self.generate_button.clicked.connect(self._generate)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)

        result_panel = QWidget()
        result_panel.setObjectName("musicResultPanel")
        result = QVBoxLayout(result_panel)
        result.setContentsMargins(16, 16, 16, 16)
        result.setSpacing(8)
        workspace.addWidget(result_panel, 42)
        result_heading = QLabel("Kết quả")
        result_heading.setObjectName("musicResultHeading")
        result.addWidget(result_heading)
        self.cover = RotatingMusicCover()
        result.addWidget(self.cover, alignment=Qt.AlignmentFlag.AlignCenter)
        self.result_title = QLabel("Bản nhạc của bạn sẽ xuất hiện tại đây")
        self.result_title.setObjectName("musicResultTitle")
        self.result_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_title.setWordWrap(True)
        result.addWidget(self.result_title)
        self.waveform = Waveform()
        self.waveform.hide()
        self.player = MusicPlayer()
        self.player.media.playbackStateChanged.connect(self.cover.set_playing)
        result.addWidget(self.player)
        actions = QHBoxLayout()
        self.export_button = OutlineButton("Tải xuống")
        self.save_button = OutlineButton("Lưu vào lịch sử")
        self.export_button.clicked.connect(self.export_requested.emit)
        self.save_button.clicked.connect(self.save_requested.emit)
        actions.addWidget(self.export_button)
        actions.addWidget(self.save_button)
        result.addLayout(actions)
        result.addStretch(1)

        self.editors = QTabWidget()
        self.editors.hide()
        self.copy_button = OutlineButton("Sao chép")
        self.copy_button.hide()
        self.gallery = None
        self.set_result_enabled(False)

    def _generate(self) -> None:
        options = {key: field.currentText() for key, field in self.options.items()}
        options["tab"] = self.tabs.tabText(self.tabs.currentIndex())
        options["extra"] = self.extra.isChecked()
        self.generate_requested.emit(self.prompts[self.tabs.currentIndex()].toPlainText(), options)

    def set_result_enabled(self, enabled: bool) -> None:
        self.save_button.setEnabled(enabled)
        self.export_button.setEnabled(enabled)

    def set_loading(self, loading: bool) -> None:
        self.generate_button.set_loading(loading)
        self.cancel_button.setVisible(loading)
        self.cancel_button.setEnabled(loading)
        self.tabs.setEnabled(not loading)
        self.import_button.setEnabled(not loading)

    def show_result(self, generated: object, texts: list[str]) -> None:  # noqa: ARG002
        self.result_title.setText(generated.title)
        self.player.set_source(generated.paths[0])
        self.waveform.set_values(generated.metadata.get("waveform", []))
        self.set_result_enabled(True)

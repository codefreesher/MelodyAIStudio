"""Generation lifecycle, cancellation, edits and exports without Qt."""

import shutil
import threading
from pathlib import Path
from uuid import uuid4

from app.database.repositories.history_repository import HistoryRepository
from app.models.generation import Generation
from app.providers.online.provider_manager import ProviderManager


class AIService:
    def __init__(self, kind: str, root: Path, providers: ProviderManager, history: HistoryRepository) -> None:
        self.kind, self.root, self.providers, self.history = kind, root, providers, history
        self.cancel_event = threading.Event()
        self.authorize = lambda: None

    def generate(self, prompt: str, options: dict) -> Generation:
        self.authorize()
        if not prompt.strip():
            raise ValueError("Vui lòng nhập nội dung sáng tạo.")
        if len(prompt) > 50000:
            raise ValueError("Nội dung quá dài (tối đa 50.000 ký tự).")
        if self.kind in ("image", "lyric"):
            allowed = (1, 2, 4) if self.kind == "image" else (1, 2, 3)
            if int(options.get("count", 1)) not in allowed:
                raise ValueError("Số phiên bản không hợp lệ.")
        if self.kind == "image" and options.get("ratio", "1:1") not in ("1:1", "16:9", "9:16", "4:3", "3:2"):
            raise ValueError("Tỉ lệ ảnh không hợp lệ.")
        folder = self.root / self.kind / str(uuid4())
        try:
            result = self.providers.get(self.kind).generate(prompt, options, folder, self.cancel_event)
            if self.kind in ("music", "audio"):
                from app.media.waveform_service import read_waveform

                result.metadata["waveform"] = read_waveform(result.paths[0])
                if options.get("format") == "MP3":
                    from app.media.ffmpeg_service import FFmpegService

                    source = result.paths[0]
                    result.paths[0] = FFmpegService().convert_mp3(
                        source, source.with_suffix(".mp3"), self.cancel_event
                    )
                    source.unlink()
            if self.cancel_event.is_set():
                raise ValueError("Đã hủy tác vụ.")
            return result
        except Exception:
            shutil.rmtree(folder, ignore_errors=True)
            raise

    def prepare(self) -> None:
        self.cancel_event.clear()

    def cancel(self) -> None:
        self.cancel_event.set()

    def save(self, result: Generation, texts: list[str] | None = None) -> None:
        if texts is not None and result.type == "lyric":
            for path, text in zip(result.paths, texts):
                path.write_text(text, encoding="utf-8")
        self.history.save(result)

    def download(self, result: Generation, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        for source in result.paths:
            target = folder / source.name
            if target.resolve() != source.resolve():
                shutil.copy2(source, target)

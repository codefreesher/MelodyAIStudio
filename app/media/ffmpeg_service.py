"""Bounded, cancellable FFmpeg conversion without shell commands."""

import shutil
import subprocess
import threading
import time
from pathlib import Path


class FFmpegService:
    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or shutil.which("ffmpeg")

    def convert_mp3(self, source: Path, destination: Path, cancel: threading.Event) -> Path:
        if not self.executable:
            raise ValueError("Cần FFmpeg để xuất MP3. Cài FFmpeg vào PATH hoặc chọn WAV.")
        process = subprocess.Popen(
            [
                self.executable,
                "-nostdin",
                "-y",
                "-v",
                "error",
                "-i",
                str(source),
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "3",
                str(destination),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        deadline = time.monotonic() + 120
        try:
            while process.poll() is None:
                if cancel.wait(0.05) or time.monotonic() >= deadline:
                    raise ValueError("Đã hủy hoặc hết thời gian chuyển MP3.")
            if process.returncode or not destination.is_file():
                raise ValueError("FFmpeg không thể tạo MP3.")
            return destination
        except Exception:
            process.kill()
            process.wait()
            destination.unlink(missing_ok=True)
            raise

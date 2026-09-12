"""Real local TTS adapter for Piper-compatible command line engines."""

import subprocess
from pathlib import Path
from uuid import uuid4

from app.database.repositories.settings_repository import SettingsRepository
from app.models.generation import Generation


class LocalTTSProvider:
    def __init__(self, settings: SettingsRepository) -> None:
        self.settings = settings

    def generate(self, prompt: str, options: dict, folder: Path, cancel) -> Generation:
        config = self.settings.get("offline:TTS Local", {})
        executable = Path(str(config.get("executable") or ""))
        model_value = str(config.get("model") or "").strip()
        models_folder = Path(str(config.get("models_folder") or ""))
        model = Path(model_value)
        if not model.is_absolute():
            model = models_folder / model
        if not executable.is_file() or not model.is_file():
            raise ValueError("Chưa cấu hình executable và voice model TTS local hợp lệ.")
        folder.mkdir(parents=True, exist_ok=True)
        output = folder / "speech.wav"
        process = subprocess.Popen(
            [str(executable), "--model", str(model), "--output_file", str(output)],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        try:
            _, error = process.communicate(prompt, timeout=300)
        except subprocess.TimeoutExpired as exc:
            process.kill()
            process.wait()
            raise ValueError("TTS local quá thời gian xử lý.") from exc
        if cancel.is_set():
            output.unlink(missing_ok=True)
            raise ValueError("Đã hủy tác vụ.")
        if process.returncode or not output.is_file():
            raise ValueError("TTS local không tạo được audio: " + (error.strip()[:160] or "unknown error"))
        return Generation(str(uuid4()), "audio", "Giọng đọc local", prompt, [output], "Piper", {"model": model.name})

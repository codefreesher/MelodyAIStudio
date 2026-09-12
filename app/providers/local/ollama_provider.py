"""Real lyric generation through a locally running Ollama server."""

from pathlib import Path
from uuid import uuid4

import httpx

from app.database.repositories.settings_repository import SettingsRepository
from app.models.generation import Generation


class OllamaTextProvider:
    def __init__(self, settings: SettingsRepository) -> None:
        self.settings = settings

    def generate(self, prompt: str, options: dict, folder: Path, cancel) -> Generation:
        config = self.settings.get("offline:Ollama", {})
        url = str(config.get("url") or "http://127.0.0.1:11434").rstrip("/")
        model = str(config.get("model") or "").strip()
        if not model:
            raise ValueError("Chưa chọn model Ollama trong Cấu hình Offline.")
        count = int(options.get("count", 1))
        folder.mkdir(parents=True, exist_ok=True)
        paths = []
        instruction = (
            "Bạn là nhạc sĩ chuyên nghiệp. Hãy viết lời bài hát hoàn chỉnh bằng tiếng Việt, "
            "có cấu trúc Verse/Chorus rõ ràng. Chỉ trả về lời bài hát.\n\nYêu cầu: " + prompt
        )
        try:
            for index in range(count):
                if cancel.is_set():
                    raise ValueError("Đã hủy tác vụ.")
                response = httpx.post(
                    url + "/api/generate",
                    json={"model": model, "prompt": instruction, "stream": False},
                    timeout=300,
                )
                response.raise_for_status()
                text = response.json().get("response")
                if not isinstance(text, str) or not text.strip():
                    raise ValueError("Ollama không trả về nội dung.")
                path = folder / f"lyric-{index + 1}.txt"
                path.write_text(text.strip() + "\n", encoding="utf-8")
                paths.append(path)
        except httpx.RequestError as exc:
            raise ValueError("Không kết nối được Ollama. Hãy khởi động engine local.") from exc
        except httpx.HTTPStatusError as exc:
            raise ValueError("Ollama từ chối yêu cầu tạo lyric.") from exc
        return Generation(str(uuid4()), "lyric", "Lyric từ Ollama", prompt, paths, "Ollama", {"model": model})

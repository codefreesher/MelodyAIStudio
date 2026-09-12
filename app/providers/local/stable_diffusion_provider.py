"""Real image generation through Stable Diffusion WebUI's local API."""

import base64
from pathlib import Path
from uuid import uuid4

import httpx

from app.database.repositories.settings_repository import SettingsRepository
from app.models.generation import Generation

SIZES = {"1:1": (768, 768), "16:9": (1024, 576), "9:16": (576, 1024), "4:3": (896, 672), "3:2": (960, 640)}


class StableDiffusionProvider:
    def __init__(self, settings: SettingsRepository) -> None:
        self.settings = settings

    def generate(self, prompt: str, options: dict, folder: Path, cancel) -> Generation:
        config = self.settings.get("offline:Stable Diffusion", {})
        url = str(config.get("url") or "http://127.0.0.1:7860").rstrip("/")
        width, height = SIZES.get(str(options.get("ratio", "1:1")), SIZES["1:1"])
        payload = {
            "prompt": prompt, "negative_prompt": str(options.get("negative_prompt", "")),
            "batch_size": int(options.get("count", 1)), "width": width, "height": height,
            "steps": int(options.get("steps") or 25), "cfg_scale": float(options.get("cfg_scale") or 7),
        }
        seed = str(options.get("seed", "")).strip()
        if seed:
            payload["seed"] = int(seed)
        if cancel.is_set():
            raise ValueError("Đã hủy tác vụ.")
        try:
            response = httpx.post(url + "/sdapi/v1/txt2img", json=payload, timeout=600)
            response.raise_for_status()
            images = response.json().get("images", [])
        except (httpx.RequestError, ValueError) as exc:
            raise ValueError("Không kết nối được Stable Diffusion WebUI local.") from exc
        except httpx.HTTPStatusError as exc:
            raise ValueError("Stable Diffusion không thể tạo ảnh.") from exc
        if not isinstance(images, list) or not images:
            raise ValueError("Stable Diffusion không trả về ảnh.")
        folder.mkdir(parents=True, exist_ok=True)
        paths = []
        for index, encoded in enumerate(images):
            if cancel.is_set():
                raise ValueError("Đã hủy tác vụ.")
            path = folder / f"image-{index + 1}.png"
            try:
                path.write_bytes(base64.b64decode(encoded.split(",")[-1], validate=True))
            except (ValueError, TypeError) as exc:
                raise ValueError("Dữ liệu ảnh từ Stable Diffusion không hợp lệ.") from exc
            paths.append(path)
        return Generation(str(uuid4()), "image", "Ảnh Stable Diffusion", prompt, paths, "Stable Diffusion", payload)

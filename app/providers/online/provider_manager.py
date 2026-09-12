"""Select real local creative engines from persisted Offline settings."""

from app.database.repositories.settings_repository import SettingsRepository
from app.providers.local.local_tts_provider import LocalTTSProvider
from app.providers.local.ollama_provider import OllamaTextProvider
from app.providers.local.stable_diffusion_provider import StableDiffusionProvider


class UnconfiguredMusicProvider:
    def generate(self, prompt, options, folder, cancel):
        raise ValueError("Chưa cấu hình engine tạo nhạc local. Cần cài MusicGen/AudioCraft trước.")


class ProviderManager:
    def __init__(self, settings: SettingsRepository) -> None:
        self.providers = {
            "music": UnconfiguredMusicProvider(),
            "lyric": OllamaTextProvider(settings),
            "audio": LocalTTSProvider(settings),
            "image": StableDiffusionProvider(settings),
        }

    def get(self, kind: str) -> object:
        return self.providers[kind]

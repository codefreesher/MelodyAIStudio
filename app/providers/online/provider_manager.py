"""Development provider selection; online/local adapters can replace mocks later."""

from app.providers.mock.creative import (
    MockImageProvider,
    MockMusicProvider,
    MockTextProvider,
    MockTTSProvider,
)


class ProviderManager:
    def __init__(self) -> None:
        self.providers = {
            "music": MockMusicProvider(),
            "lyric": MockTextProvider(),
            "audio": MockTTSProvider(),
            "image": MockImageProvider(),
        }

    def get(self, kind: str) -> object:
        return self.providers[kind]

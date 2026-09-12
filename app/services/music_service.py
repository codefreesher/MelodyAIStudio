"""Music generation service."""

from app.services.ai_service import AIService


class MusicService(AIService):
    def __init__(self, root, providers, history) -> None:
        super().__init__("music", root, providers, history)

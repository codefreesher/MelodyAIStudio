"""Audio generation service."""

from app.services.ai_service import AIService


class AudioService(AIService):
    def __init__(self, root, providers, history) -> None:
        super().__init__("audio", root, providers, history)

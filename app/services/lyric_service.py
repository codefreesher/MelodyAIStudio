"""Lyric generation service."""

from app.services.ai_service import AIService


class LyricService(AIService):
    def __init__(self, root, providers, history) -> None:
        super().__init__("lyric", root, providers, history)

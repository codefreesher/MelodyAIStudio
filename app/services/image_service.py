"""Image generation service."""

from app.services.ai_service import AIService


class ImageService(AIService):
    def __init__(self, root, providers, history) -> None:
        super().__init__("image", root, providers, history)

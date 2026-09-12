"""Semantic design tokens for MelodyAI's Pink Light theme."""

from types import MappingProxyType

PINK_LIGHT = MappingProxyType(
    {
        "background": "#FFF8FB",
        "surface": "#FFFFFF",
        "sidebar": "#FFF4F8",
        "primary": "#FF4F9A",
        "secondary": "#FF78B2",
        "gradient_end": "#FF79B0",
        "soft": "#FFE4EF",
        "border": "#F1DCE5",
        "text": "#25232A",
        "muted": "#77717A",
        "hover": "#FFF0F6",
        "pressed": "#D92F79",
        "disabled": "#F5EDF1",
        "disabled_text": "#A89DA4",
        "danger": "#B42346",
        "danger_hover": "#941C39",
        "focus": "#B52D69",
        "selection": "#FFD0E3",
    }
)
TYPOGRAPHY = MappingProxyType(
    {
        "body": 10,
        "caption": 9,
        "subtitle": 12,
        "heading": 18,
        "title": 28,
    }
)
RADII = MappingProxyType({"card": 14, "button": 10, "input": 8})
FONT_FAMILIES = ("Inter", "Segoe UI", "Noto Sans", "DejaVu Sans")

"""Stable application identity; version lives in VERSION."""

APP_NAME = "MelodyAI"
APP_SUBTITLE = "AI Music & Creative Studio"

# Default GitHub release source for in-app updates. Not user-editable from
# the main Update page (see app/ui/pages/updates/) — a developer override
# still exists via AppConfig.github_owner/github_repository (config/app.json).
UPDATE_PROVIDER = "github"
UPDATE_OWNER = "codefreesher"
UPDATE_REPOSITORY = "MelodyAIStudio"
UPDATE_CHANNEL = "stable"

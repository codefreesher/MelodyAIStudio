"""Base error for application failures."""


class MelodyAIError(Exception):
    """A recoverable application error."""


class AuthenticationError(MelodyAIError):
    """Authentication failed with a user-safe explanation."""


class LicenseError(MelodyAIError):
    """A user-safe license validation or storage failure."""

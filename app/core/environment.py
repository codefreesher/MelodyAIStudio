"""Validate the supported Python runtime."""

import sys


def check_environment() -> None:
    if sys.version_info < (3, 12):
        raise RuntimeError("MelodyAI requires Python 3.12 or newer")

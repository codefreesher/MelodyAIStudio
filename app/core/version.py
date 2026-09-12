"""Read the single version source."""

from importlib.metadata import PackageNotFoundError, version

from app.core.paths import bundle_root


def get_version() -> str:
    path = bundle_root() / "VERSION"
    if path.is_file():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value
        raise RuntimeError("VERSION is empty")
    try:
        return version("melodyai")
    except PackageNotFoundError as exc:
        raise RuntimeError("Application version is unavailable") from exc

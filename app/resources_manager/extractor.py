"""ZIP extraction blocks traversal, symlinks and oversized archives."""

import stat
import zipfile
from pathlib import Path, PurePosixPath


def extract_zip(archive: Path, destination: Path, limit: int = 12 * 1024**3) -> None:
    with zipfile.ZipFile(archive) as source:
        total = 0
        for info in source.infolist():
            name = info.filename.replace("\\", "/")
            parts = PurePosixPath(name)
            target = (destination / name).resolve()
            if (
                parts.is_absolute()
                or ".." in parts.parts
                or ":" in name
                or not target.is_relative_to(destination.resolve())
            ):
                raise ValueError("Archive chứa đường dẫn không an toàn.")
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError("Không chấp nhận symlink trong archive.")
            total += info.file_size
            if total > limit:
                raise ValueError("Archive giải nén quá lớn.")
        destination.mkdir(parents=True, exist_ok=True)
        source.extractall(destination)

"""Emit release artifact SHA256 metadata without credentials."""

import argparse
import hashlib
import json
from pathlib import Path


def generate(paths: list[Path]) -> dict:
    version = (Path(__file__).resolve().parents[1] / "VERSION").read_text().strip()
    assets = []
    for path in paths:
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        assets.append({"name": path.name, "size": path.stat().st_size, "sha256": digest})
    return {"version": version, "assets": assets}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("assets", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("release-manifest.json"))
    args = parser.parse_args()
    args.output.write_text(json.dumps(generate(args.assets), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

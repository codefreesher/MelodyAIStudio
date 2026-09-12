"""Prepare an explicit draft release via GitHub CLI; never publish automatically."""

import argparse
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--notes", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("assets", nargs="+", type=Path)
    args = parser.parse_args()
    version = (Path(__file__).resolve().parents[1] / "VERSION").read_text().strip()
    for path in [args.notes, *args.assets]:
        if not path.is_file():
            parser.error(f"Missing file: {path}")
    command = [
        "gh",
        "release",
        "create",
        "v" + version,
        "--repo",
        args.repo,
        "--draft",
        "--title",
        "MelodyAI " + version,
        "--notes-file",
        str(args.notes),
        *map(str, args.assets),
    ]
    if not args.execute:
        print(subprocess.list2cmdline(command))
        return 0
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())

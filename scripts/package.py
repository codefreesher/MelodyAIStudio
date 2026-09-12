"""Compile the Windows installer with Inno Setup 6."""

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iscc", default="ISCC.exe")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text().strip()
    executable = shutil.which(args.iscc) or args.iscc
    command = [executable, f"/DMyAppVersion={version}", str(ROOT / "installer/installer.iss")]
    if args.dry_run:
        print(subprocess.list2cmdline(command))
        return 0
    if not (ROOT / "dist/MelodyAI/MelodyAI.exe").is_file():
        parser.error("Build on Windows before packaging.")
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())

"""Build a native onedir bundle; Windows Python produces MelodyAI.exe."""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_command() -> list[str]:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--name",
        "MelodyAI",
        "--paths",
        str(ROOT),
        "--distpath",
        str(ROOT / "dist"),
        "--workpath",
        str(ROOT / "build/pyinstaller"),
        "--specpath",
        str(ROOT / "build"),
        "--exclude-module",
        "admin_tools",
        "--exclude-module",
        "tests",
        "--collect-submodules",
        "app",
        "--collect-submodules",
        "keyring.backends",
        "--add-data",
        f"{ROOT / 'VERSION'}:.",
        "--add-data",
        f"{ROOT / 'app/assets'}:app/assets",
        "--add-data",
        f"{ROOT / 'app/ui/themes'}:app/ui/themes",
        "--add-data",
        f"{ROOT / 'app/ui/pages'}:app/ui/pages",
        "--add-data",
        f"{ROOT / 'app/ui/widgets/sidebar_styles.qss'}:app/ui/widgets",
        "--add-data",
        f"{ROOT / 'app/database/schema.sql'}:app/database",
    ]
    if sys.platform == "win32":
        command += ["--icon", str(ROOT / "app/assets/icons/melodyai.ico")]
    return command + [str(ROOT / "scripts/entrypoint.py")]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--require-public-key", action="store_true")
    args = parser.parse_args()
    if args.require_public_key and not (ROOT / "app/assets/keys/license_public.pem").is_file():
        parser.error("Copy the issuer public key into app/assets/keys before a licensed release.")
    for path in (ROOT / "app").rglob("*"):
        if path.is_file() and (path.suffix in (".key", ".pem") and path.name != "license_public.pem"):
            parser.error(f"Unexpected key file in desktop tree: {path.name}")
        if path.is_file() and path.suffix == ".pem" and b"PRIVATE KEY" in path.read_bytes():
            parser.error("Private key material must never enter desktop assets.")
    command = build_command()
    if args.dry_run:
        print(subprocess.list2cmdline(command))
        return 0
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())

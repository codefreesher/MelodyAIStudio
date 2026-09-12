"""Launch with python -m app.main."""

import argparse
import sys

from app.bootstrap import bootstrap


def main() -> int:
    parser = argparse.ArgumentParser(description="MelodyAI desktop application")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Open the window and close automatically to validate startup",
    )
    parser.add_argument("--showcase", action="store_true", help="Open Stage 03 component showcase")
    args = parser.parse_args()
    return bootstrap([sys.argv[0]], smoke_test=args.smoke_test, showcase=args.showcase)


if __name__ == "__main__":
    raise SystemExit(main())

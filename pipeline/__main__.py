"""Command line: `python -m pipeline film [--root DIR]` (what `make film` runs)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline import run
from pipeline.providers import default_providers
from pipeline.storyboard import StoryboardError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pipeline")
    parser.add_argument("target", choices=["film"], help="what to build")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project directory (default: current)")
    args = parser.parse_args(argv)

    try:
        result = run.film(args.root.resolve(), default_providers())
    except StoryboardError as e:
        print(e, file=sys.stderr)
        return 2
    print(f"film: {result.video} ({result.duration_s:g} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

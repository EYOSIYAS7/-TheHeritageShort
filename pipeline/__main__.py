"""Command line: `python -m pipeline film|review [--root DIR]` (what `make film` / `make review` run)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline import run, storyboard
from pipeline.providers import default_providers
from pipeline.stages import script
from pipeline.storyboard import StoryboardError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pipeline")
    parser.add_argument("target", choices=["film", "review"], help="build the film, or list unreviewed Amharic")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project directory (default: current)")
    args = parser.parse_args(argv)

    root: Path = args.root.resolve()
    try:
        if args.target == "review":
            return _review(root)
        result = run.film(root, default_providers(root))
    except StoryboardError as e:
        print(e, file=sys.stderr)
        return 2
    print(f"film: {result.video} ({result.duration_s:g} s)")
    if result.drafted:
        print(f"Amharic drafted for {len(result.drafted)} line(s); review them with `make review`.")
    if result.undrafted:
        print(f"No Amharic yet for {', '.join(result.undrafted)} (no GEMINI_API_KEY in .env): narrated in English.")
    return 0


def _review(root: Path) -> int:
    """Print every unreviewed line, English beside Amharic, for the author to check."""
    lines = script.unreviewed(storyboard.load(root / "storyboard.json"))
    for line in lines:
        print(f"[{line.id}] shot {line.shot}")
        print(f"  EN: {line.en}")
        print(f"  AM: {line.am or '(not drafted yet)'}")
        print()
    if lines:
        print(f"{len(lines)} line(s) to review. Correct `am` in storyboard.json if needed, "
              "then set `am_reviewed` to true.")
    else:
        print("Every line's Amharic is reviewed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

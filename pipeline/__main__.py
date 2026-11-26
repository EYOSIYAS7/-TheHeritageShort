"""Command line: `python -m pipeline film|gpu|review|voices|costs [--root DIR]` (what the make targets run)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pipeline import costs, run, storyboard
from pipeline.providers import default_providers
from pipeline.stages import script
from pipeline.storyboard import StoryboardError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pipeline")
    parser.add_argument("target", choices=["film", "rough-cut", "radio-cut", "review", "voices", "costs", "gpu"],
                        help="build a cut, list unreviewed Amharic, or run the voice trial")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project directory (default: current)")
    args = parser.parse_args(argv)

    root: Path = args.root.resolve()
    try:
        if args.target == "review":
            return _review(root)
        if args.target == "costs":
            print(costs.report(costs.load(root / "runs.jsonl")), end="")
            return 0
        if args.target == "voices":
            for voice, path in run.voice_trial(root, default_providers(root)).items():
                print(f"{voice}: {path.relative_to(root)}")
            print("Listen, then set narrator.voice and narrator.voice_reason in storyboard.json.")
            return 0
        if args.target == "gpu":
            score, clips = run.gpu_stages(root, default_providers(root))
            for i, path in sorted(score.candidates.items()):
                print(f"music candidate {i}: {path.relative_to(root)}")
            for shot, path in sorted(clips.items()):
                print(f"moving shot {shot}: {path.relative_to(root)}")
            print("Anything missing fell back; the reason is the `fallback` line in runs.jsonl.")
            return 0
        log_lines = _log_length(root)
        cut: run.Cut = "radio-cut" if args.target == "radio-cut" else "rough-cut" if args.target == "rough-cut" else "film"
        result = run.film(root, default_providers(root), cut=cut)
    except StoryboardError as e:
        print(e, file=sys.stderr)
        return 2
    _print_run_summary(root, log_lines)
    for aspect, video in result.videos.items():
        print(f"{aspect}: {video.relative_to(root)} ({result.duration_s:g} s)")
    if result.missing_keyframes:
        print(f"No keyframe for shot(s) {result.missing_keyframes} (no Cloudflare keys): labelled placeholders.")
    score = result.score
    if score.track is None:
        print("Music: placeholder pad (no score track yet; needs Kaggle keys).")
    elif score.chosen is None and score.candidates:
        names = ", ".join(str(p.relative_to(root)) for p in score.candidates.values())
        print(f"Music: candidate 0 for now. Listen to {names}, then set music.chosen and music.reason.")
    if result.drafted:
        print(f"Amharic drafted for {len(result.drafted)} line(s); review them with `make review`.")
    if result.undrafted:
        print(f"No Amharic yet for {', '.join(result.undrafted)} (no GEMINI_API_KEY in .env): narrated in English.")
    return 0


def _log_length(root: Path) -> int:
    path = root / "runs.jsonl"
    return len(path.read_text(encoding="utf-8").splitlines()) if path.exists() else 0


def _print_run_summary(root: Path, start: int) -> None:
    """What this run made new and what it reused, read back from the lines it added to runs.jsonl."""
    path = root / "runs.jsonl"
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()[start:]] if path.exists() else []
    made = [f"{r['stage']} {r['item']}" for r in lines if r["cache"] == "miss" and r["outcome"] == "ok"]
    reused = sum(1 for r in lines if r["cache"] == "hit")
    print(f"This run: {len(made)} made new ({', '.join(made) or 'nothing'}); {reused} reused from the cache.")


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

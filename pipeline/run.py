"""The single pipeline entry point.

Validates the storyboard before any stage runs, then runs every stage with the
injected providers, the cache and the run log. The script stage may write
Amharic drafts back into the storyboard, which is then validated again. Tests call `film()` with fake
providers; `make film` calls it through `python -m pipeline film`.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal
from pathlib import Path

from pipeline import storyboard, timing
from pipeline.cache import Cache
from pipeline.providers import Providers
from pipeline.runlog import RunLog
from pipeline.storyboard import StoryboardError
from pipeline.stages import assemble, narration, script, voices


def voice_trial(root: Path, providers: Providers, *, sleep: Callable[[float], None] = time.sleep) -> dict[str, Path]:
    """`make voices`: the storyboard's trial line spoken by each trial voice."""
    board = storyboard.load(root / "storyboard.json")
    log = RunLog(root / "runs.jsonl", sleep=sleep)
    return voices.run(board, providers.speech, Cache(root), log, root / "outputs")


@dataclass(frozen=True)
class FilmResult:
    video: Path
    duration_s: float
    drafted: list[str]  # narration lines whose Amharic was just drafted (need review)
    undrafted: list[str]  # narration lines still without Amharic (no text model available)


def film(root: Path, providers: Providers, *, cut: Literal["film", "radio-cut"] = "film",
         sleep: Callable[[float], None] = time.sleep) -> FilmResult:
    """Build the film (or the radio cut) from `root/storyboard.json` into `root/outputs/film/`.

    Every model call is logged to `root/runs.jsonl`. The final film refuses
    unreviewed Amharic; the radio cut allows it, for early user tests.
    """
    path = root / "storyboard.json"
    board = storyboard.load(path)  # raises StoryboardError before any provider call

    outputs = root / "outputs"
    cache = Cache(root)
    log = RunLog(root / "runs.jsonl", sleep=sleep)

    drafts = script.run(path, board, providers.text, cache, log, outputs)
    if drafts.drafted:
        board = storyboard.load(path)
    if cut == "film":
        unreviewed = script.unreviewed(board)
        if unreviewed:
            raise StoryboardError([f"narration line {line.id!r}: Amharic not reviewed yet (run `make review`)"
                                   for line in unreviewed])
    audio = narration.run(board, providers.speech, cache, log, outputs)
    placed = timing.place(board, audio)
    timing.check(board, placed)
    video = assemble.run(board, placed, outputs, name="film" if cut == "film" else cut)
    return FilmResult(video=video, duration_s=board.total_s, drafted=drafts.drafted, undrafted=drafts.undrafted)

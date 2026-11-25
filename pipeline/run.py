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
from pathlib import Path

from pipeline import storyboard
from pipeline.cache import Cache
from pipeline.providers import Providers
from pipeline.runlog import RunLog
from pipeline.stages import assemble, narration, script


@dataclass(frozen=True)
class FilmResult:
    video: Path
    duration_s: float
    drafted: list[str]  # narration lines whose Amharic was just drafted (need review)
    undrafted: list[str]  # narration lines still without Amharic (no text model available)


def film(root: Path, providers: Providers, *, sleep: Callable[[float], None] = time.sleep) -> FilmResult:
    """Build the film from `root/storyboard.json` into `root/outputs/`, logging to `root/runs.jsonl`."""
    path = root / "storyboard.json"
    board = storyboard.load(path)  # raises StoryboardError before any provider call

    outputs = root / "outputs"
    cache = Cache(root)
    log = RunLog(root / "runs.jsonl", sleep=sleep)

    drafts = script.run(path, board, providers.text, cache, log, outputs)
    if drafts.drafted:
        board = storyboard.load(path)
    audio = narration.run(board, providers.speech, cache, log, outputs)
    video = assemble.run(board, audio, outputs)
    return FilmResult(video=video, duration_s=board.total_s, drafted=drafts.drafted, undrafted=drafts.undrafted)

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
from pipeline.storyboard import ASPECTS, Aspect, StoryboardError

Cut = Literal["film", "rough-cut", "radio-cut"]
from pipeline.stages import assemble, characters, keyframes, narration, pans, script, voices


def voice_trial(root: Path, providers: Providers, *, sleep: Callable[[float], None] = time.sleep) -> dict[str, Path]:
    """`make voices`: the storyboard's trial line spoken by each trial voice."""
    board = storyboard.load(root / "storyboard.json")
    log = RunLog(root / "runs.jsonl", sleep=sleep)
    return voices.run(board, providers.speech, Cache(root), log, root / "outputs")


@dataclass(frozen=True)
class FilmResult:
    videos: dict[Aspect, Path]
    duration_s: float
    missing_keyframes: list[int]  # shots shown as a labelled placeholder (no keyframe, no image keys)
    drafted: list[str]  # narration lines whose Amharic was just drafted (need review)
    undrafted: list[str]  # narration lines still without Amharic (no text model available)

    @property
    def video(self) -> Path:
        return self.videos["16:9"]


def film(root: Path, providers: Providers, *, cut: Cut = "film",
         sleep: Callable[[float], None] = time.sleep) -> FilmResult:
    """Build a cut from `root/storyboard.json` into `root/outputs/film/`.

    - radio-cut: narration, subtitles and music on a black screen, 16:9 (user test 1)
    - rough-cut: plus character sheet, keyframes and pan shots, 16:9 and 9:16
    - film: the rough cut's stages, refusing unreviewed Amharic

    Every model call is logged to `root/runs.jsonl`.
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
    if cut == "radio-cut":
        video = assemble.run(board, placed, outputs, name=cut, aspect="16:9", clips=None)
        return FilmResult(videos={"16:9": video}, duration_s=board.total_s, missing_keyframes=[],
                          drafted=drafts.drafted, undrafted=drafts.undrafted)

    sheet = characters.run(board, providers.image, cache, log, outputs)
    frames = keyframes.run(board, providers.image, sheet, cache, log, outputs)
    clips = pans.run(board, frames, outputs)
    videos = {aspect: assemble.run(board, placed, outputs, name=cut, aspect=aspect, clips=clips[aspect])
              for aspect in ASPECTS}
    return FilmResult(videos=videos, duration_s=board.total_s,
                      missing_keyframes=[s.id for s in board.shots if s.id not in frames],
                      drafted=drafts.drafted, undrafted=drafts.undrafted)

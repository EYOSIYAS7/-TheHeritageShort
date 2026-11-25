"""Timing checks that need the measured narration audio.

A line may run into the next shot, but it may not overlap the next line or
run past the last shot (into the saying card). Nothing is auto-stretched: the
author fixes offsets, durations or wording.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pipeline.stages.narration import audio_seconds
from pipeline.storyboard import Line, Storyboard, StoryboardError


@dataclass(frozen=True)
class Placed:
    line: Line
    line_audio: Path
    start_s: float
    length_s: float

    @property
    def end_s(self) -> float:
        return self.start_s + self.length_s


def place(board: Storyboard, audio: dict[str, Path]) -> list[Placed]:
    """Every line with its start on the film timeline and its measured length, in time order."""
    placed = [Placed(line, audio[line.id], board.line_start_s(line), audio_seconds(audio[line.id]))
              for line in board.narration]
    return sorted(placed, key=lambda p: p.start_s)


def check(board: Storyboard, placed: list[Placed]) -> None:
    problems: list[str] = []
    for here, after in zip(placed, placed[1:]):
        if here.end_s > after.start_s:
            problems.append(
                f"narration line {here.line.id!r} ({here.length_s:.2f} s of audio) overlaps line "
                f"{after.line.id!r} by {here.end_s - after.start_s:.2f} s"
            )
    if placed and placed[-1].end_s > board.shots_s:
        last = placed[-1]
        problems.append(
            f"narration line {last.line.id!r} ({last.length_s:.2f} s of audio) runs "
            f"{last.end_s - board.shots_s:.2f} s past the end of the last shot"
        )
    if problems:
        raise StoryboardError(problems)

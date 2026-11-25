"""Picture stages: the character sheet, then keyframes, cached per shot."""

from __future__ import annotations

from typing import Any

from pipeline import storyboard
from pipeline.cache import Cache
from pipeline.runlog import RunLog
from pipeline.stages import characters, keyframes
from tests.conftest import FakeImage, Project, no_sleep


def draw_all(project: Project, image: FakeImage) -> None:
    board = storyboard.load(project.root / "storyboard.json")
    cache, log, outputs = Cache(project.root), RunLog(project.root / "runs.jsonl", sleep=no_sleep), project.root / "outputs"
    sheet = characters.run(board, image, cache, log, outputs)
    keyframes.run(board, image, sheet, cache, log, outputs)


def test_changing_one_shot_prompt_regenerates_exactly_that_keyframe(project: Project) -> None:
    draw_all(project, FakeImage())
    first_run = len(project.runs)  # 3 character images + 3 keyframes

    def reword(d: dict[str, Any]) -> None:
        d["shots"][1]["keyframe_prompt"] = "keyframe 2, now at dusk"

    project.edit(reword)
    second = FakeImage()
    draw_all(project, second)

    assert len(second.prompts) == 1 and second.prompts[0].startswith("keyframe 2, now at dusk.")
    misses = [(r["stage"], r["item"]) for r in project.runs[first_run:] if r["cache"] == "miss"]
    assert misses == [("keyframes", "shot-02")]

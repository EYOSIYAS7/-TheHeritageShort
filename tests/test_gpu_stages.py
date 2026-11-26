"""GPU stages (Kaggle): the score and the moving shots, with a fake GPU provider and real FFmpeg."""

from __future__ import annotations

from typing import Any

from pipeline import run, storyboard
from pipeline.cache import Cache
from pipeline.media import run_ffmpeg
from pipeline.runlog import RunLog
from pipeline.stages import moving
from tests.conftest import FakeGpu, FakeSpeech, Project, no_sleep, providers


def test_score_reuses_the_last_chosen_track_when_the_gpu_job_fails(project: Project) -> None:
    gpu = FakeGpu()
    run.film(project.root, providers(FakeSpeech(), gpu=gpu), cut="radio-cut", sleep=no_sleep)
    assert gpu.jobs == [["candidate-0"]]

    def choose(d: dict[str, Any]) -> None:
        d["music"]["chosen"], d["music"]["reason"] = 0, "the quietest start"

    project.edit(choose)
    start = len(project.runs)
    result = run.film(project.root, providers(FakeSpeech(), gpu=gpu), cut="radio-cut", sleep=no_sleep)
    music = [r for r in project.runs[start:] if r["stage"] == "music"]
    assert gpu.jobs == [["candidate-0"]]  # unchanged caption, duration and seeds: no Kaggle call
    assert [r["cache"] for r in music] == ["hit"]
    assert result.score.track is not None

    def recaption(d: dict[str, Any]) -> None:
        d["music"]["caption"] = "quieter still"

    project.edit(recaption)
    start = len(project.runs)
    failing = FakeGpu(fail=True)
    result = run.film(project.root, providers(FakeSpeech(), gpu=failing), cut="radio-cut", sleep=no_sleep)

    assert failing.jobs == [["candidate-0"]]
    assert result.score.track == project.root / "outputs" / "music" / "chosen.wav"
    fallbacks = [r["error"] for r in project.runs[start:] if r["outcome"] == "fallback" and r["item"] == "track"]
    assert fallbacks == ["candidate 0 unavailable: the last chosen track is reused"]
    assert result.video.exists()


def test_moving_shot_falls_back_to_its_pan_shot_when_the_gpu_job_fails(project: Project) -> None:
    def make_moving(d: dict[str, Any]) -> None:
        d["shots"][1]["type"] = "moving"

    project.edit(make_moving)
    board = storyboard.load(project.root / "storyboard.json")
    keyframe = project.root / "outputs" / "keyframes" / "shot-02.jpg"
    keyframe.parent.mkdir(parents=True)
    run_ffmpeg(["-f", "lavfi", "-i", "color=c=gray:s=320x180", "-frames:v", "1", str(keyframe)])
    log = RunLog(project.root / "runs.jsonl", sleep=no_sleep)
    gpu = FakeGpu(fail=True)

    clips = moving.run(board, {2: keyframe}, gpu, Cache(project.root), log, project.root / "outputs")

    assert clips == {}  # no clip: place() keeps the pan shot
    assert gpu.jobs == [["shot-02"]]
    lines = [(r["item"], r["outcome"], r["error"]) for r in project.runs]
    assert ("kaggle-job", "error", "PermanentError: fake Kaggle job failed") in lines
    assert ("shot-02", "fallback", "Kaggle job failed (PermanentError): the pan shot is used") in lines

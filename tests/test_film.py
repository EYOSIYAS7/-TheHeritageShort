"""Seam tests: the pipeline entry point with fake providers and real FFmpeg.

They assert only what is visible from outside: errors raised, provider calls
the fakes recorded, lines in runs.jsonl, and ffprobe/ffmpeg facts about the MP4.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest

from pipeline import run
from pipeline.runlog import PermanentError
from pipeline.storyboard import Aspect, StoryboardError
from tests.conftest import FakeSpeech, Project, no_sleep, providers

REQUIRED_LOG_FIELDS = {"ts", "stage", "item", "model", "params", "seed", "latency_s", "cost_usd", "cache", "attempt", "outcome"}


def build(project: Project, speech: FakeSpeech) -> run.FilmResult:
    return run.film(project.root, providers(speech), cut="radio-cut", sleep=no_sleep)


# --- validation happens before any provider call --------------------------------------------


def test_schema_violation_fails_naming_the_shot_and_field_with_no_provider_call(project: Project) -> None:
    def bad_duration(d: dict[str, Any]) -> None:
        d["shots"][1]["duration_s"] = -5

    project.edit(bad_duration)
    speech = FakeSpeech()

    with pytest.raises(StoryboardError) as err:
        build(project, speech)

    assert "shots[1] (shot 2).duration_s" in str(err.value)
    assert speech.calls == []
    assert project.runs == []


def test_film_shorter_than_60s_fails_with_the_total_and_no_provider_call(project: Project) -> None:
    def short(d: dict[str, Any]) -> None:
        for shot in d["shots"]:
            shot["duration_s"] = 10

    project.edit(short)
    speech = FakeSpeech()

    with pytest.raises(StoryboardError) as err:
        build(project, speech)

    message = str(err.value)
    assert "total length: 37 s" in message
    assert "60–90 s" in message
    assert speech.calls == []
    assert project.runs == []


def test_film_longer_than_90s_fails_with_the_total_and_no_provider_call(project: Project) -> None:
    def long(d: dict[str, Any]) -> None:
        d["shots"][0]["duration_s"] = 50

    project.edit(long)
    speech = FakeSpeech()

    with pytest.raises(StoryboardError) as err:
        build(project, speech)

    message = str(err.value)
    assert "total length: 97 s" in message
    assert "60–90 s" in message
    assert speech.calls == []
    assert project.runs == []


def test_narration_anchored_to_a_missing_shot_fails_naming_the_line(project: Project) -> None:
    def dangling(d: dict[str, Any]) -> None:
        d["narration"][2]["shot"] = 9

    project.edit(dangling)
    speech = FakeSpeech()

    with pytest.raises(StoryboardError) as err:
        build(project, speech)

    assert "narration[2] (line 'c').shot: there is no shot 9" in str(err.value)
    assert speech.calls == []


# --- run log and cache ------------------------------------------------------------------------


def test_first_run_narrates_every_line_and_logs_one_line_per_call(project: Project) -> None:
    speech = FakeSpeech()

    build(project, speech)

    # The pinned Amharic is spoken; lines without Amharic yet fall back to English.
    assert speech.calls == ["Let's talk tomorrow, Dad.", "ነገ አባባ ነገ", "Not every tomorrow is promised."]
    runs = project.narration_runs
    assert [r["item"] for r in runs] == ["a", "b", "c"]
    for r in runs:
        assert REQUIRED_LOG_FIELDS <= r.keys()
        assert r["stage"] == "narration"
        assert r["model"] == "fake-tts"
        assert r["seed"] == 42
        assert r["cache"] == "miss"
        assert r["outcome"] == "ok"
        assert r["cost_usd"] == 0.001
    assert runs[1]["params"]["voice"] == "TestVoice"
    assert runs[1]["params"]["language"] == "am"


def test_second_run_with_no_changes_makes_zero_calls(project: Project) -> None:
    build(project, FakeSpeech())
    second = FakeSpeech()

    build(project, second)

    assert second.calls == []
    new_lines = project.narration_runs[3:]
    assert [(r["item"], r["cache"]) for r in new_lines] == [("a", "hit"), ("b", "hit"), ("c", "hit")]


def test_changing_one_narration_line_makes_exactly_one_speech_call(project: Project) -> None:
    build(project, FakeSpeech())

    def reword(d: dict[str, Any]) -> None:
        d["narration"][2]["en"] = "Because not every tomorrow is promised."

    project.edit(reword)
    second = FakeSpeech()

    build(project, second)

    assert second.calls == ["Because not every tomorrow is promised."]
    misses = [r["item"] for r in project.narration_runs[3:] if r["cache"] == "miss"]
    assert misses == ["c"]


def test_cache_manifest_maps_input_hashes_to_output_files(project: Project) -> None:
    build(project, FakeSpeech())

    manifest = json.loads((project.root / "outputs" / "cache-manifest.json").read_text(encoding="utf-8"))

    assert sorted(e["item"] for e in manifest.values()) == ["a", "b", "c"]
    for key, entry in manifest.items():
        assert re.fullmatch(r"[0-9a-f]{64}", key)
        assert (project.root / entry["path"]).is_file()


def test_transient_failure_is_retried_and_every_attempt_is_logged(project: Project) -> None:
    speech = FakeSpeech(fail_first=1)
    delays: list[float] = []

    run.film(project.root, providers(speech), cut="radio-cut", sleep=delays.append)

    assert len(speech.calls) == 4  # line a twice, then b and c
    assert [(r["item"], r["attempt"], r["outcome"]) for r in project.narration_runs] == [
        ("a", 1, "retry"), ("a", 2, "ok"), ("b", 1, "ok"), ("c", 1, "ok"),
    ]
    assert "fake transient failure" in project.narration_runs[0]["error"]
    assert delays == [2.0]


def test_call_that_keeps_failing_is_logged_as_an_error_and_stops_the_run(project: Project) -> None:
    speech = FakeSpeech(always_fail=True)

    with pytest.raises(ConnectionError):
        build(project, speech)

    assert len(speech.calls) == 3
    assert [(r["item"], r["attempt"], r["outcome"]) for r in project.narration_runs] == [
        ("a", 1, "retry"), ("a", 2, "retry"), ("a", 3, "error"),
    ]


def test_permanent_failure_is_not_retried(project: Project) -> None:
    speech = FakeSpeech(always_fail=True, permanent=True)

    with pytest.raises(PermanentError):
        build(project, speech)

    assert len(speech.calls) == 1
    assert [(r["item"], r["attempt"], r["outcome"]) for r in project.narration_runs] == [("a", 1, "error")]


# --- the exported film ------------------------------------------------------------------------


def ffprobe(path: Path) -> dict[str, Any]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    data: dict[str, Any] = json.loads(out)
    return data


def sound_starts(path: Path) -> list[float]:
    """Times where audio rises out of silence, from FFmpeg's silencedetect."""
    err = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=n=-40dB:d=0.3", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    ).stderr
    duration = float(ffprobe(path)["format"]["duration"])
    ends = [float(t) for t in re.findall(r"silence_end: ([\d.]+)", err)]
    return [t for t in ends if t < duration - 0.2]  # trailing silence also "ends" at end of file


def test_film_is_a_black_screen_mp4_at_the_storyboard_length_with_narration_audio(project: Project) -> None:
    result = build(project, FakeSpeech())

    info = ffprobe(result.video)
    video = [s for s in info["streams"] if s["codec_type"] == "video"]
    audio = [s for s in info["streams"] if s["codec_type"] == "audio"]
    assert len(video) == 1 and len(audio) == 1
    assert (video[0]["width"], video[0]["height"]) == (1920, 1080)
    # 3 x 20 s shots + 4 s saying card + 3 s end card
    assert float(info["format"]["duration"]) == pytest.approx(67.0, abs=0.1)


def test_each_line_is_placed_at_its_shot_start_plus_offset(project: Project) -> None:
    def mute_music(d: dict[str, Any]) -> None:  # so only the voice breaks the silence
        d["music"]["volume_points"] = [{"t_s": 0, "gain": 0.0}]

    project.edit(mute_music)
    result = build(project, FakeSpeech())

    # a: shot 1 (0 s) + 1.0; b: shot 2 (20 s) + 2.0; c: shot 3 (40 s) + 0.5
    assert sound_starts(result.video) == pytest.approx([1.0, 22.0, 40.5], abs=0.1)


def test_burned_subtitles_come_from_the_storyboard_english(project: Project) -> None:
    result = build(project, FakeSpeech())

    srt = result.video.with_suffix(".en.srt").read_text(encoding="utf-8")
    cue_texts = [block.splitlines()[2] for block in srt.strip().split("\n\n")]
    assert cue_texts == ["Let's talk tomorrow, Dad.", "Tomorrow, Dad.", "Not every tomorrow is promised."]


def test_line_that_overlaps_the_next_fails_naming_both_lines_and_the_overrun(project: Project) -> None:
    def crowd(d: dict[str, Any]) -> None:  # b starts 0.4 s after a, but every fake line is 1 s long
        d["narration"][1]["shot"] = 1
        d["narration"][1]["offset_s"] = 1.4

    project.edit(crowd)

    with pytest.raises(StoryboardError) as err:
        build(project, FakeSpeech())

    assert "narration line 'a' (1.00 s of audio) overlaps line 'b' by 0.60 s" in str(err.value)


# --- the final film ---------------------------------------------------------------------------


def test_final_film_refuses_unreviewed_amharic_before_any_speech_call(project: Project) -> None:
    speech = FakeSpeech()

    with pytest.raises(StoryboardError) as err:
        run.film(project.root, providers(speech), cut="film", sleep=no_sleep)

    assert "narration line 'a': Amharic not reviewed yet" in str(err.value)
    assert speech.calls == []


def test_final_film_exports_16x9_and_9x16_with_cards_at_the_storyboard_length(project: Project) -> None:
    def review_all(d: dict[str, Any]) -> None:
        for line in d["narration"]:
            line["am"] = line["am"] or "ሙከራ"
            line["am_reviewed"] = True

    project.edit(review_all)

    result = run.film(project.root, providers(FakeSpeech()), cut="film", sleep=no_sleep)

    sizes: dict[Aspect, tuple[int, int]] = {"16:9": (1920, 1080), "9:16": (1080, 1920)}
    for aspect, size in sizes.items():
        info = ffprobe(result.videos[aspect])
        video = [s for s in info["streams"] if s["codec_type"] == "video"]
        audio = [s for s in info["streams"] if s["codec_type"] == "audio"]
        assert (video[0]["width"], video[0]["height"]) == size
        assert len(audio) == 1
        # 3 x 20 s shots (labelled placeholders: no image keys) + 4 s saying card + 3 s end card
        assert float(info["format"]["duration"]) == pytest.approx(67.0, abs=0.1)

"""Fixtures for seam tests: a tiny project directory and a fake speech provider."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from pipeline.media import write_tone_wav
from pipeline.providers import Providers
from pipeline.runlog import PermanentError

REPO = Path(__file__).resolve().parent.parent


def _pan() -> dict[str, Any]:
    view = {"x": 0.5, "y": 0.5, "zoom": 1.0}
    return {"16:9": {"start": view, "end": view}, "9:16": {"start": view, "end": view}}


def _shot(shot_id: int, duration_s: float) -> dict[str, Any]:
    return {
        "id": shot_id, "act": "Mornings", "duration_s": duration_s, "type": "pan",
        "characters": ["father"], "keyframe_prompt": f"keyframe {shot_id}",
        "motion_prompt": "slow push in", "seed": shot_id, "grade": "copper", "pan": _pan(),
    }


def _line(line_id: str, shot: int, offset_s: float, en: str, am: str | None = None) -> dict[str, Any]:
    return {"id": line_id, "shot": shot, "offset_s": offset_s, "en": en, "am": am,
            "am_pinned": am is not None, "am_reviewed": am is not None}


# Three 20 s shots + 4 s saying card + 3 s end card = 67 s.
TINY_STORYBOARD: dict[str, Any] = {
    "title": {"en": "Test", "am": "ሙከራ"},
    "saying": {"am": "በእጅ የያዙት ወርቅ እንደ መዳብ ይቆጠራል", "en": "Gold held in the hand is counted as copper.", "duration_s": 4},
    "end_card": {"text": "Made with AI.", "duration_s": 3},
    "style": {"words": "painterly", "grades": {"copper": "muted copper", "gold": "warm gold"}},
    "characters": {
        "father": {"description": "an old man", "seed": 1},
        "son": {"description": "a young man", "seed": 2},
        "coffee_corner": {"description": "a coffee corner", "seed": 3},
    },
    "script": {"instruction": "Translate into Amharic.", "seed": 7},
    "narrator": {"voice": "TestVoice", "style": "warm", "seed": 42},
    "music": {"caption": "quiet", "duration_s": 67, "candidates": 1, "chosen": None, "reason": None,
              "volume_points": [{"t_s": 0, "gain": 1.0}]},
    "shots": [_shot(1, 20), _shot(2, 20), _shot(3, 20)],
    "narration": [
        _line("a", 1, 1.0, "Let's talk tomorrow, Dad."),
        _line("b", 2, 2.0, "Tomorrow, Dad.", am="ነገ አባባ ነገ"),
        _line("c", 3, 0.5, "Not every tomorrow is promised."),
    ],
}


class FakeSpeech:
    """Records every synthesize call and writes a real 1 s tone, so FFmpeg has real audio."""

    model = "fake-tts"
    LINE_S = 1.0

    def __init__(self, fail_first: int = 0, always_fail: bool = False, permanent: bool = False) -> None:
        self.calls: list[str] = []
        self.fail_first = fail_first
        self.always_fail = always_fail
        self.permanent = permanent

    def synthesize(self, text: str, *, language: str, voice: str, style: str, seed: int, out_path: Path) -> None:
        self.calls.append(text)
        if self.always_fail or len(self.calls) <= self.fail_first:
            if self.permanent:
                raise PermanentError("fake rejected request")
            raise ConnectionError("fake transient failure")
        write_tone_wav(out_path, self.LINE_S, freq_hz=440.0, amplitude=0.5)

    def cost_estimate_usd(self, text: str) -> float:
        return 0.001


class FakeText:
    """Records every prompt and answers with a recognisable fake 'translation'."""

    model = "fake-text"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str, *, seed: int) -> str:
        self.prompts.append(prompt)
        return "AM:" + prompt.rsplit("English: ", 1)[-1]

    def cost_estimate_usd(self, prompt: str) -> float:
        return 0.0


class Project:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.write(copy.deepcopy(TINY_STORYBOARD))

    @property
    def runs(self) -> list[dict[str, Any]]:
        path = self.root / "runs.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def read(self) -> dict[str, Any]:
        data: dict[str, Any] = json.loads((self.root / "storyboard.json").read_text(encoding="utf-8"))
        return data

    def write(self, data: dict[str, Any]) -> None:
        (self.root / "storyboard.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def edit(self, change: Callable[[dict[str, Any]], None]) -> None:
        data = self.read()
        change(data)
        self.write(data)


@pytest.fixture
def project(tmp_path: Path) -> Project:
    return Project(tmp_path)


def providers(speech: FakeSpeech, text: FakeText | None = None) -> Providers:
    return Providers(speech=speech, text=(text,) if text else ())


def no_sleep(_: float) -> None:
    pass

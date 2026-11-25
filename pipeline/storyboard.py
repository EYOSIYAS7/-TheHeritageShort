"""Storyboard: the only module that knows the storyboard.json format.

`load()` validates the file against the JSON Schema in `schema/`, then runs the
checks the schema cannot express (references between shots and narration,
total film length), and returns a typed `Storyboard`. Any problem raises
`StoryboardError` whose messages name the shot, line and field.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "storyboard.schema.json"

MIN_FILM_S = 60.0
MAX_FILM_S = 90.0


class StoryboardError(Exception):
    """The storyboard is invalid. `problems` holds one human-readable message per issue."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("storyboard.json is invalid:\n" + "\n".join(f"  - {p}" for p in problems))


@dataclass(frozen=True)
class Shot:
    id: int
    act: str
    duration_s: float
    type: Literal["pan", "moving"]
    keyframe_prompt: str
    motion_prompt: str
    seed: int
    grade: Literal["copper", "gold"]


@dataclass(frozen=True)
class Line:
    id: str
    shot: int
    offset_s: float
    en: str
    am: str | None
    am_pinned: bool
    am_reviewed: bool
    am_from_en: str | None


@dataclass(frozen=True)
class Narrator:
    voice: str
    style: str
    seed: int


@dataclass(frozen=True)
class Script:
    """How the script stage drafts the Amharic: the translation instruction and seed."""

    instruction: str
    seed: int


@dataclass(frozen=True)
class Storyboard:
    shots: list[Shot]
    narration: list[Line]
    script: Script
    narrator: Narrator
    saying_card_s: float
    end_card_s: float

    @property
    def shots_s(self) -> float:
        return sum(s.duration_s for s in self.shots)

    @property
    def total_s(self) -> float:
        """Film length: every shot, then the saying card, then the end card."""
        return self.shots_s + self.saying_card_s + self.end_card_s

    def shot_start_s(self, shot_id: int) -> float:
        """Start of a shot on the film timeline (shots play in storyboard order)."""
        t = 0.0
        for shot in self.shots:
            if shot.id == shot_id:
                return t
            t += shot.duration_s
        raise KeyError(shot_id)

    def line_start_s(self, line: Line) -> float:
        return self.shot_start_s(line.shot) + line.offset_s


def load(path: Path) -> Storyboard:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise StoryboardError([f"{path} not found"]) from None
    except json.JSONDecodeError as e:
        raise StoryboardError([f"not valid JSON: line {e.lineno}, column {e.colno}: {e.msg}"]) from None

    _check_schema(raw)
    _check_consistency(raw)
    return _to_storyboard(raw)


def _check_schema(raw: Any) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(raw), key=lambda e: [str(p) for p in e.absolute_path])
    if errors:
        raise StoryboardError([f"{_where(raw, list(e.absolute_path))}: {e.message}" for e in errors])


def _where(raw: Any, path: list[str | int]) -> str:
    """Render a JSON path like `shots[2] (shot 3).duration_s`, naming shots and lines by id."""
    if not path:
        return "(top level)"
    out = ""
    node = raw
    for i, part in enumerate(path):
        if isinstance(part, int):
            out += f"[{part}]"
            label = _item_label(path[i - 1] if i else None, node, part)
            if label:
                out += f" ({label})"
        else:
            out += f".{part}" if out else part
        try:
            node = node[part]
        except (KeyError, IndexError, TypeError):
            node = None
    return out


def _item_label(collection: str | int | None, node: Any, index: int) -> str | None:
    try:
        item_id = node[index]["id"]
    except (KeyError, IndexError, TypeError):
        return None
    if collection == "shots":
        return f"shot {item_id}"
    if collection == "narration":
        return f"line {item_id!r}"
    return None


def _check_consistency(raw: dict[str, Any]) -> None:
    problems: list[str] = []
    shots = raw["shots"]
    durations = {s["id"]: s["duration_s"] for s in shots}

    seen: set[int] = set()
    for i, shot in enumerate(shots):
        if shot["id"] in seen:
            problems.append(f"shots[{i}] (shot {shot['id']}).id: shot id {shot['id']} is used more than once")
        seen.add(shot["id"])

    seen_lines: set[str] = set()
    for i, line in enumerate(raw["narration"]):
        where = f"narration[{i}] (line {line['id']!r})"
        if line["id"] in seen_lines:
            problems.append(f"{where}.id: line id {line['id']!r} is used more than once")
        seen_lines.add(line["id"])
        if line["shot"] not in durations:
            problems.append(f"{where}.shot: there is no shot {line['shot']}")
        elif line["offset_s"] >= durations[line["shot"]]:
            problems.append(
                f"{where}.offset_s: {line['offset_s']} s is past the end of shot {line['shot']} "
                f"({durations[line['shot']]} s long)"
            )
        if line["am_pinned"] and not line["am"]:
            problems.append(f"{where}.am: the line is pinned but has no Amharic text")

    shots_s = sum(durations.values())
    saying_s = raw["saying"]["duration_s"]
    end_s = raw["end_card"]["duration_s"]
    total = shots_s + saying_s + end_s
    if not MIN_FILM_S <= total <= MAX_FILM_S:
        problems.append(
            f"total length: {total:g} s (shots {shots_s:g} s + saying card {saying_s:g} s + "
            f"end card {end_s:g} s) is outside {MIN_FILM_S:g}–{MAX_FILM_S:g} s"
        )

    if problems:
        raise StoryboardError(problems)


def _to_storyboard(raw: dict[str, Any]) -> Storyboard:
    shots = [
        Shot(
            id=s["id"],
            act=s["act"],
            duration_s=float(s["duration_s"]),
            type=s["type"],
            keyframe_prompt=s["keyframe_prompt"],
            motion_prompt=s["motion_prompt"],
            seed=s["seed"],
            grade=s["grade"],
        )
        for s in raw["shots"]
    ]
    narration = [
        Line(
            id=n["id"],
            shot=n["shot"],
            offset_s=float(n["offset_s"]),
            en=n["en"],
            am=n["am"],
            am_pinned=n["am_pinned"],
            am_reviewed=n["am_reviewed"],
            am_from_en=n.get("am_from_en"),
        )
        for n in raw["narration"]
    ]
    narrator = raw["narrator"]
    return Storyboard(
        shots=shots,
        narration=narration,
        script=Script(instruction=raw["script"]["instruction"], seed=raw["script"]["seed"]),
        narrator=Narrator(voice=narrator["voice"], style=narrator["style"], seed=narrator["seed"]),
        saying_card_s=float(raw["saying"]["duration_s"]),
        end_card_s=float(raw["end_card"]["duration_s"]),
    )

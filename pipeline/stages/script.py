"""Script stage: draft the Amharic for each narration line from its English.

Writes each draft back into `storyboard.json` with `am_reviewed: false` and
`am_from_en` set to the English it came from; the author then corrects the
Amharic and sets `am_reviewed: true`. A line is drafted only when it is not
pinned and either has no Amharic or its English has changed since the draft
(`am_from_en` differs). Amharic written by hand without `am_from_en` is left
alone. Drafts are cached by the prompt (instruction + English) and seed, so
changing a line back to earlier English reuses the earlier draft.

Text models are tried in order; every attempt on every model is logged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pipeline.cache import Cache, input_hash
from pipeline.providers import TextProvider
from pipeline.runlog import Call, RunLog
from pipeline.storyboard import Line, Storyboard

STAGE = "script"


@dataclass(frozen=True)
class ScriptResult:
    drafted: list[str]  # line ids whose Amharic was (re)drafted and now needs review
    undrafted: list[str]  # line ids that need a draft but no text model is available


def run(storyboard_path: Path, board: Storyboard, texts: tuple[TextProvider, ...], cache: Cache, log: RunLog,
        outputs: Path) -> ScriptResult:
    """Draft every line that needs it and write the drafts back into the storyboard file."""
    drafts: dict[str, str] = {}
    undrafted: list[str] = []
    for line in board.narration:
        if not _needs_draft(line):
            continue
        prompt = f"{board.script.instruction}\n\nEnglish: {line.en}"
        seed = board.script.seed
        key = input_hash({"stage": STAGE, "prompt": prompt, "seed": seed})

        cached = cache.get(key)
        if cached is not None:
            saved = json.loads(cached.read_text(encoding="utf-8"))
            log.cache_hit(Call(stage=STAGE, item=line.id, model=saved["model"], params={"prompt": prompt}, seed=seed))
            drafts[line.id] = saved["am"]
            continue
        if not texts:
            undrafted.append(line.id)
            continue

        am, model = _draft(texts, prompt, seed, line.id, log)
        out = outputs / STAGE / f"{line.id}-{key[:12]}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"en": line.en, "am": am, "model": model}, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        cache.put(key, stage=STAGE, item=line.id, path=out)
        drafts[line.id] = am

    if drafts:
        _write_back(storyboard_path, drafts)
    return ScriptResult(drafted=list(drafts), undrafted=undrafted)


def _needs_draft(line: Line) -> bool:
    if line.am_pinned:
        return False
    if not line.am:
        return True
    return line.am_from_en is not None and line.am_from_en != line.en


def _draft(texts: tuple[TextProvider, ...], prompt: str, seed: int, item: str, log: RunLog) -> tuple[str, str]:
    """Ask each text model in turn (each with the run log's retries); return the first answer and its model."""
    error: Exception | None = None
    for text in texts:
        call = Call(stage=STAGE, item=item, model=text.model, params={"prompt": prompt}, seed=seed)
        try:
            am = log.call(call, lambda: text.generate(prompt, seed=seed), cost_usd=text.cost_estimate_usd(prompt))
        except Exception as e:  # already logged; fall through to the next model
            error = e
            continue
        return am.strip().strip('"“”«»').strip(), text.model
    assert error is not None
    raise error


def _write_back(path: Path, drafts: dict[str, str]) -> None:
    raw = json.loads(path.read_text(encoding="utf-8"))
    for line in raw["narration"]:
        if line["id"] in drafts:
            line["am"] = drafts[line["id"]]
            line["am_from_en"] = line["en"]
            line["am_reviewed"] = False
    path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def unreviewed(board: Storyboard) -> list[Line]:
    """Lines whose Amharic the author has not yet checked (including lines with no Amharic yet)."""
    return [line for line in board.narration if not line.am_reviewed]

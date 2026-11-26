"""Score stage: ACE-Step 1.5 candidates for the storyboard's music cue, and the chosen track.

The cue's caption and duration, with seeds `seed`, `seed + 1`, ..., go to one
Kaggle job (`kaggle/acestep_score.py`) for every candidate not in the cache,
so an unchanged caption, duration and seeds make no Kaggle call. The author
listens to the candidates and records `music.chosen` (0-based) and
`music.reason` in the storyboard; until then candidate 0 is used.

The chosen candidate is also copied to `outputs/music/chosen.wav`. When the
chosen candidate can't be made (no Kaggle keys, or the job failed after the
caption changed), that last chosen track is reused; with no track at all the
placeholder pad plays. Either way the fallback is logged.
"""

from __future__ import annotations

import filecmp
import shutil
from dataclasses import dataclass
from pathlib import Path

from pipeline.cache import Cache, input_hash
from pipeline.providers import GpuJobs
from pipeline.runlog import Call, RunLog
from pipeline.storyboard import Storyboard

STAGE = "music"
MODEL = "ACE-Step-1.5/acestep-v15-turbo"
REPO = "https://github.com/ace-step/ACE-Step-1.5.git"
CONFIG = "acestep-v15-turbo"
LM = "acestep-5Hz-lm-0.6B"
STEPS = 8  # the turbo model's recommended step count
SHIFT = 3.0  # recommended for turbo
NOTEBOOK = Path(__file__).resolve().parents[2] / "kaggle" / "acestep_score.py"


@dataclass(frozen=True)
class Score:
    track: Path | None  # what assembly plays; None = the placeholder pad
    candidates: dict[int, Path]
    chosen: int | None  # the storyboard's choice; None = not chosen yet


def run(board: Storyboard, gpu: GpuJobs, cache: Cache, log: RunLog, outputs: Path) -> Score:
    music = board.music
    folder = outputs / STAGE
    candidates: dict[int, Path] = {}
    todo: list[tuple[int, str, Call]] = []
    for i in range(music.candidates):
        params = {"caption": music.caption, "duration_s": music.duration_s, "steps": STEPS, "shift": SHIFT}
        seed = music.seed + i
        key = input_hash({"kind": "music", "model": MODEL, "seed": seed, **params})
        call = Call(stage=STAGE, item=f"candidate-{i}", model=MODEL, params=params, seed=seed)
        cached = cache.get(key)
        if cached is not None:
            log.cache_hit(call)
            candidates[i] = cached
        else:
            todo.append((i, key, call))

    if todo and gpu.available:
        candidates.update(_generate(todo, gpu, cache, log, folder))
    elif todo:
        for _, _, call in todo:
            log.fallback(call, "no Kaggle credentials in .env: not generated")

    pick = music.chosen if music.chosen is not None else 0
    last = folder / "chosen.wav"
    track = candidates.get(pick)
    fallback = Call(stage=STAGE, item="track", model=MODEL, params={"chosen": music.chosen}, seed=None)
    if track is not None:
        if music.chosen is not None and not (last.exists() and filecmp.cmp(track, last, shallow=False)):
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copy(track, last)
    elif last.exists():
        log.fallback(fallback, f"candidate {pick} unavailable: the last chosen track is reused")
        track = last
    else:
        log.fallback(fallback, f"candidate {pick} unavailable and no track chosen before: placeholder pad")
    return Score(track=track, candidates=candidates, chosen=music.chosen)


def _generate(todo: list[tuple[int, str, Call]], gpu: GpuJobs, cache: Cache, log: RunLog,
              folder: Path) -> dict[int, Path]:
    items = [{"id": call.item, "seed": call.seed, **call.params} for _, _, call in todo]
    job_call = Call(stage=STAGE, item="kaggle-job", model=gpu.model,
                    params={"notebook": NOTEBOOK.name, "items": [i["id"] for i in items], "model": MODEL}, seed=None)
    try:
        result = log.call(job_call, lambda: gpu.run(NOTEBOOK, {"items": items, "repo": REPO, "config": CONFIG, "lm": LM},
                                                    {}, folder / "job"), cost_usd=0.0)
    except Exception:  # logged by the run log; the fallback below takes over
        for _, _, call in todo:
            log.fallback(call, "Kaggle job failed: not generated")
        return {}
    made: dict[int, Path] = {}
    for i, key, call in todo:
        seconds = result.seconds.get(call.item, 0.0)
        timed = Call(call.stage, call.item, call.model, {**call.params, "gpu_minutes": round(seconds / 60, 2)}, call.seed)
        file = result.files.get(call.item)
        if file is None:
            log.record(timed, latency_s=seconds, outcome="error", error=result.errors.get(call.item))
            continue
        log.record(timed, latency_s=seconds, outcome="ok")
        out = folder / f"{call.item}-{key[:12]}.wav"
        shutil.copy(file, out)
        cache.put(key, stage=STAGE, item=call.item, path=out)
        made[i] = out
    return made

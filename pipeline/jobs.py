"""What a remote GPU job returns: one file (or an error) per item, timed on the GPU.

A GPU stage sends every item that missed the cache to one job (one Kaggle
notebook run), because loading a video or music model takes minutes; the
notebook saves each item as it finishes and writes `results.json`
({item: {"file", "seconds"} or {"error", "seconds"}}) after each one, so a run
that dies part-way still returns what it finished.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class JobResult:
    files: dict[str, Path] = field(default_factory=dict)  # item -> downloaded output
    seconds: dict[str, float] = field(default_factory=dict)  # item -> GPU seconds, measured in the notebook
    errors: dict[str, str] = field(default_factory=dict)  # item -> why it produced nothing


def read_results(results: dict[str, dict[str, object]], out_dir: Path, items: list[str]) -> JobResult:
    """Turn a notebook's results.json into a JobResult; an item it never reached is an error."""
    files: dict[str, Path] = {}
    seconds: dict[str, float] = {}
    errors: dict[str, str] = {}
    for item in items:
        entry = results.get(item, {})
        seconds[item] = float(str(entry.get("seconds", 0.0)))
        name = entry.get("file")
        if isinstance(name, str) and (out_dir / name).exists():
            files[item] = out_dir / name
        else:
            errors[item] = str(entry.get("error") or results.get("_job", {}).get("error")
                               or "the notebook did not reach this item")
    return JobResult(files=files, seconds=seconds, errors=errors)

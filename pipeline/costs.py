"""Cost report: a per-stage summary of `runs.jsonl` (what `make costs` prints).

Counts every logged line by stage and model: attempts that reached the
provider (ok, retried, failed), cache hits and skips; sums the measured
latency; and prices each successful image call at Cloudflare's list rate from
its logged size and reference images. Every call in this project ran on a
free tier, so the logged `cost_usd` is 0; the image column is what the same
calls would cost on the paid tier. Text and TTS calls are priced in COSTS.md
from the measured audio and token counts, which the log doesn't hold.
GPU minutes are summed from the per-item `gpu_minutes` the Kaggle notebooks measure;
a `fallback` line (item not generated, fallback used) is counted with the skips.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Cloudflare Workers AI list price, FLUX.2 klein 4B (developers.cloudflare.com/workers-ai/platform/pricing/)
NEURONS_PER_OUTPUT_TILE = 26.05  # per 512x512 output tile
NEURONS_PER_INPUT_TILE = 5.37  # per 512x512 reference-image tile
USD_PER_1000_NEURONS = 0.011
REFERENCE_TILES = 4  # character-sheet references are 1024x1024


@dataclass
class Row:
    attempts: int = 0
    ok: int = 0
    retried: int = 0
    failed: int = 0
    hits: int = 0
    skipped: int = 0
    latency_s: float = 0.0
    neurons: float = 0.0
    gpu_minutes: float = 0.0
    days: set[str] = field(default_factory=set)


def summarise(lines: list[dict[str, Any]]) -> dict[tuple[str, str], Row]:
    rows: dict[tuple[str, str], Row] = defaultdict(Row)
    for r in lines:
        row = rows[(r["stage"], r["model"])]
        gpu_minutes = r["params"].get("gpu_minutes") if isinstance(r.get("params"), dict) else None
        if isinstance(gpu_minutes, (int, float)):
            row.gpu_minutes += float(gpu_minutes)
        if r["outcome"] in ("skipped", "fallback"):
            row.skipped += 1
            continue
        if r["cache"] == "hit":
            row.hits += 1
            continue
        row.attempts += 1
        row.latency_s += r["latency_s"]
        row.days.add(r["ts"][:10])
        if r["outcome"] == "ok":
            row.ok += 1
            row.neurons += image_neurons(r)
        elif r["outcome"] == "retry":
            row.retried += 1
        else:
            row.failed += 1
    return dict(rows)


def image_neurons(r: dict[str, Any]) -> float:
    """Workers AI neurons for one successful image call, from its logged size and references."""
    params = r["params"]
    if not r["model"].startswith("@cf/") or "width" not in params:
        return 0.0
    tiles = math.ceil(int(params["width"]) * int(params["height"]) / (512 * 512))
    references = len(params.get("references", []))
    return float(tiles * NEURONS_PER_OUTPUT_TILE + references * REFERENCE_TILES * NEURONS_PER_INPUT_TILE)


def report(lines: list[dict[str, Any]]) -> str:
    rows = summarise(lines)
    out = [
        "| Stage | Model | Attempts | OK | Retried | Failed | Cache hits | Skipped | Latency (s) | Mean per attempt (s) | Image list price ($) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    total = Row()
    for (stage, model), row in sorted(rows.items()):
        mean = f"{row.latency_s / row.attempts:.1f}" if row.attempts else "-"
        price = f"{row.neurons * USD_PER_1000_NEURONS / 1000:.4f}" if row.neurons else "-"
        out.append(f"| {stage} | `{model}` | {row.attempts} | {row.ok} | {row.retried} | {row.failed} | {row.hits} "
                   f"| {row.skipped} | {row.latency_s:.1f} | {mean} | {price} |")
        for name in ("attempts", "ok", "retried", "failed", "hits", "skipped", "latency_s", "neurons", "gpu_minutes"):
            setattr(total, name, getattr(total, name) + getattr(row, name))
    out.append(f"| **total** | | {total.attempts} | {total.ok} | {total.retried} | {total.failed} | {total.hits} "
               f"| {total.skipped} | {total.latency_s:.1f} | | {total.neurons * USD_PER_1000_NEURONS / 1000:.4f} |")
    out += ["", f"Image calls used {total.neurons:,.0f} Workers AI neurons (free allowance: 10,000 per day). "
                f"Kaggle GPU minutes: {total.gpu_minutes:.1f} (free quota: about 30 GPU hours a week)."]
    return "\n".join(out) + "\n"


def load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

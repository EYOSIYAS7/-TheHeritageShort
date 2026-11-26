"""`make costs`: a per-stage summary of the run log."""

from __future__ import annotations

from typing import Any

from pipeline import costs


def line(stage: str, model: str, cache: str | None, outcome: str, latency: float, **params: Any) -> dict[str, Any]:
    return {"ts": "2026-11-26T10:00:00+00:00", "stage": stage, "item": "x", "model": model, "params": params,
            "seed": 1, "latency_s": latency, "cost_usd": 0.0, "cache": cache, "attempt": 1, "outcome": outcome,
            "error": None}


def test_report_counts_attempts_hits_and_prices_images_per_stage() -> None:
    log = [
        line("narration", "tts", "miss", "retry", 1.0),
        line("narration", "tts", "miss", "ok", 3.0),
        line("narration", "tts", "hit", "ok", 0.0),
        # 1024x1024 = 4 output tiles, one reference = 4 input tiles: 4*26.05 + 4*5.37 = 125.68 neurons
        line("keyframes", "@cf/flux", "miss", "ok", 10.0, width=1024, height=1024, references=["father.jpg"]),
    ]

    text = costs.report(log)

    assert "| narration | `tts` | 2 | 1 | 1 | 0 | 1 | 0 | 4.0 | 2.0 | - |" in text
    assert "| keyframes | `@cf/flux` | 1 | 1 | 0 | 0 | 0 | 0 | 10.0 | 10.0 | 0.0014 |" in text
    assert "126 Workers AI neurons" in text

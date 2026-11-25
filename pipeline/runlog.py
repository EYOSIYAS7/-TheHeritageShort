"""Run log: every provider call goes through here.

Adds retries with exponential backoff, measures latency, and appends one JSON
line per model call (every attempt, including failed ones) to `runs.jsonl`:
timestamp, stage, item (shot or line), model, parameters, seed, latency, cost
estimate, cache hit or miss, attempt number and outcome. Cache hits are logged
too, so a re-run leaves evidence that nothing was regenerated.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypeVar

T = TypeVar("T")

Outcome = Literal["ok", "retry", "error"]


class PermanentError(Exception):
    """Raised by a provider for a failure that retrying cannot fix (bad key, rejected prompt)."""


@dataclass(frozen=True)
class Call:
    """What is being asked of which model: the fields every log line shares."""

    stage: str
    item: str
    model: str
    params: dict[str, Any]
    seed: int | None


class RunLog:
    def __init__(
        self,
        path: Path,
        *,
        max_attempts: int = 3,
        base_delay_s: float = 2.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.path = path
        self.max_attempts = max_attempts
        self.base_delay_s = base_delay_s
        self.sleep = sleep

    def call(self, call: Call, fn: Callable[[], T], *, cost_usd: float) -> T:
        """Run `fn`, retrying transient failures with backoff; log one line per attempt."""
        for attempt in range(1, self.max_attempts + 1):
            start = time.monotonic()
            try:
                result = fn()
            except Exception as e:  # free tiers fail in many ways; all but PermanentError are retried
                final = isinstance(e, PermanentError) or attempt == self.max_attempts
                # A failed attempt may still be billed, so it carries the same estimate.
                self._write(call, time.monotonic() - start, cost_usd, "miss", attempt,
                            "error" if final else "retry", f"{type(e).__name__}: {e}")
                if final:
                    raise
                self.sleep(self.base_delay_s * 2 ** (attempt - 1))
                continue
            self._write(call, time.monotonic() - start, cost_usd, "miss", attempt, "ok", None)
            return result
        raise AssertionError("unreachable: the loop returns or raises")

    def cache_hit(self, call: Call) -> None:
        self._write(call, 0.0, 0.0, "hit", 0, "ok", None)

    def _write(
        self,
        call: Call,
        latency_s: float,
        cost_usd: float,
        cache: Literal["hit", "miss"],
        attempt: int,
        outcome: Outcome,
        error: str | None,
    ) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "stage": call.stage,
            "item": call.item,
            "model": call.model,
            "params": call.params,
            "seed": call.seed,
            "latency_s": round(latency_s, 3),
            "cost_usd": cost_usd,
            "cache": cache,
            "attempt": attempt,
            "outcome": outcome,
            "error": error,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

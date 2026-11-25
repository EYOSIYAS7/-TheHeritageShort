"""Cache: maps a hash of an item's declared inputs to its output file.

The manifest (`outputs/cache-manifest.json`) is committed with the outputs
(ADR 0002), so a clean clone reuses every generated file. A stage asks the
cache before calling a provider; any change to a declared input changes the
hash and so forces regeneration of that item only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

MANIFEST = Path("outputs") / "cache-manifest.json"


def input_hash(inputs: dict[str, Any]) -> str:
    """Stable SHA-256 of the declared inputs (key order and whitespace don't matter)."""
    canonical = json.dumps(inputs, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class Cache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.manifest_path = root / MANIFEST
        self.entries: dict[str, dict[str, str]] = {}
        if self.manifest_path.exists():
            self.entries = json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def get(self, key: str) -> Path | None:
        """The cached output for this input hash, or None if missing or deleted from disk."""
        entry = self.entries.get(key)
        if entry is None:
            return None
        path = self.root / entry["path"]
        return path if path.exists() else None

    def put(self, key: str, *, stage: str, item: str, path: Path) -> None:
        self.entries[key] = {"stage": stage, "item": item, "path": path.relative_to(self.root).as_posix()}
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        # Saved after every item, so a crash mid-run keeps everything already generated.
        self.manifest_path.write_text(
            json.dumps(self.entries, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
        )

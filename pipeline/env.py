"""Read API keys from the git-ignored `.env` file, and only from there.

Keys are never read from the process environment, so what a run used is always
what `.env` says. Empty values count as missing, which is how a provider is
skipped rather than failed.
"""

from __future__ import annotations

from pathlib import Path


def load_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.removeprefix("export ").partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if value:
            values[key.strip()] = value
    return values

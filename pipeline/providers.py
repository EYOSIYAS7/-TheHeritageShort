"""Provider interfaces, one per capability, and the offline placeholder adapters.

Providers are chosen at the pipeline entry point and injected into the stages,
so tests use fakes and real adapters (`pipeline.adapters`: Gemini, Cloudflare,
Kaggle) plug in without changing any stage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pipeline.adapters import GeminiSpeech, GeminiText
from pipeline.env import load_env


class SpeechProvider(Protocol):
    """Text to speech: writes one audio file (WAV) for one narration line."""

    model: str

    def synthesize(self, text: str, *, language: str, voice: str, style: str, seed: int, out_path: Path) -> None: ...

    def cost_estimate_usd(self, text: str) -> float: ...


class TextProvider(Protocol):
    """Text generation: drafts (e.g. the Amharic narration) from a prompt."""

    model: str

    def generate(self, prompt: str, *, seed: int) -> str: ...

    def cost_estimate_usd(self, prompt: str) -> float: ...


class ImageProvider(Protocol):
    """Text (plus optional reference images) to one image file (PNG)."""

    model: str

    def generate(self, prompt: str, *, seed: int, width: int, height: int, out_path: Path,
                 references: tuple[Path, ...] = ()) -> None: ...

    def cost_estimate_usd(self, prompt: str) -> float: ...


class GpuJobs(Protocol):
    """Remote GPU jobs (Kaggle notebooks). Push and poll arrive with the GPU stages."""

    model: str

    def authenticate(self) -> str: ...


# Tried in order. gemini-3.8-flash answered only 503 "high demand" or 429 quota errors in the
# first script run while gemini-3.5-flash drafted every line (FAILURES.md F1), so 3.5 goes first.
TEXT_MODELS = ("gemini-3.5-flash", "gemini-3.8-flash")


@dataclass(frozen=True)
class Providers:
    speech: SpeechProvider
    text: tuple[TextProvider, ...] = ()  # tried in order; empty means no drafting (no key)


def default_providers(root: Path) -> Providers:
    """Real adapters, with the keys in `root/.env`.

    Without GEMINI_API_KEY, narration still builds from cached audio; a line
    that needs new audio fails with a message naming the missing key. Text
    drafting is skipped (lines without Amharic are narrated in English).
    """
    env = load_env(root / ".env")
    key = env.get("GEMINI_API_KEY")
    text: tuple[TextProvider, ...] = tuple(GeminiText(key, model) for model in TEXT_MODELS) if key else ()
    return Providers(speech=GeminiSpeech(key or ""), text=text)

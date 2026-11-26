"""Provider interfaces, one per capability, and the offline placeholder adapters.

Providers are chosen at the pipeline entry point and injected into the stages,
so tests use fakes and real adapters (`pipeline.adapters`: Gemini, Cloudflare,
Kaggle) plug in without changing any stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from pipeline.adapters import CloudflareImage, GeminiSpeech, GeminiText, KaggleJobs
from pipeline.env import load_env
from pipeline.jobs import JobResult
from pipeline.runlog import PermanentError


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
    """Text (plus optional reference images) to one image file."""

    model: str
    available: bool  # False without credentials: only cached images can be used

    def generate(self, prompt: str, *, seed: int, width: int, height: int, out_path: Path,
                 references: tuple[Path, ...] = ()) -> None: ...

    def cost_estimate_usd(self, prompt: str) -> float: ...


class GpuJobs(Protocol):
    """Remote GPU jobs (Kaggle notebooks): run one notebook over a batch of items, return each item's file."""

    model: str
    available: bool  # False without credentials: GPU stages use their fallbacks

    def run(self, notebook: Path, job: dict[str, Any], files: dict[str, Path], out_dir: Path) -> JobResult: ...


class NoGpu:
    """No GPU provider: every GPU item falls back (pan shot, last chosen track)."""

    model = "none"
    available = False

    def run(self, notebook: Path, job: dict[str, Any], files: dict[str, Path], out_dir: Path) -> JobResult:
        raise PermanentError("no GPU provider configured")


# Tried in order. gemini-3.8-flash answered only 503 "high demand" or 429 quota errors in the
# first script run while gemini-3.5-flash drafted every line (FAILURES.md F1), so 3.5 goes first.
TEXT_MODELS = ("gemini-3.5-flash", "gemini-3.8-flash")


@dataclass(frozen=True)
class Providers:
    speech: SpeechProvider
    image: ImageProvider
    text: tuple[TextProvider, ...] = ()  # tried in order; empty means no drafting (no key)
    gpu: GpuJobs = field(default_factory=NoGpu)


def default_providers(root: Path) -> Providers:
    """Real adapters, with the keys in `root/.env`.

    Without Kaggle keys, moving shots fall back to pan shots and the score to the
    last chosen track (ADR 0002). Without GEMINI_API_KEY, narration still builds from cached audio; a line
    that needs new audio fails with a message naming the missing key. Text
    drafting is skipped (lines without Amharic are narrated in English).
    """
    env = load_env(root / ".env")
    key = env.get("GEMINI_API_KEY")
    text: tuple[TextProvider, ...] = tuple(GeminiText(key, model) for model in TEXT_MODELS) if key else ()
    image = CloudflareImage(env.get("CLOUDFLARE_ACCOUNT_ID", ""), env.get("CLOUDFLARE_API_TOKEN", ""))
    gpu = KaggleJobs(env.get("KAGGLE_USERNAME", ""), env.get("KAGGLE_KEY", ""))
    return Providers(speech=GeminiSpeech(key or ""), image=image, text=text, gpu=gpu)

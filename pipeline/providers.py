"""Provider interfaces, one per capability, and the offline placeholder adapters.

Providers are chosen at the pipeline entry point and injected into the stages,
so tests use fakes and real adapters (`pipeline.adapters`: Gemini, Cloudflare,
Kaggle) plug in without changing any stage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pipeline.media import write_tone_wav


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


class PlaceholderSpeech:
    """Offline stand-in for TTS: a quiet tone as long as the line would take to speak.

    Not a model: it is logged under the model name "placeholder-tone" so the run
    log never passes it off as real TTS. Used until the Gemini TTS adapter
    exists. Length assumes about 2.5 words per second.
    """

    model = "placeholder-tone"
    WORDS_PER_S = 2.5

    def synthesize(self, text: str, *, language: str, voice: str, style: str, seed: int, out_path: Path) -> None:
        words = len(text.split())
        write_tone_wav(out_path, max(0.8, words / self.WORDS_PER_S))

    def cost_estimate_usd(self, text: str) -> float:
        return 0.0


@dataclass(frozen=True)
class Providers:
    speech: SpeechProvider


def default_providers() -> Providers:
    return Providers(speech=PlaceholderSpeech())

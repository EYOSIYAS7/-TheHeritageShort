"""Narration stage: one audio file per narration line, cached per line.

The narrator speaks the line's Amharic (English only while a line has no
Amharic yet). `speak` is shared with the voice trial, and the cache key
doesn't name the stage, so the trial clip in the chosen voice is reused as
that line's narration.
"""

from __future__ import annotations

import wave
from pathlib import Path

from pipeline.cache import Cache, input_hash
from pipeline.providers import SpeechProvider
from pipeline.runlog import Call, RunLog
from pipeline.storyboard import Line, Storyboard

STAGE = "narration"


def run(storyboard: Storyboard, speech: SpeechProvider, cache: Cache, log: RunLog, outputs: Path) -> dict[str, Path]:
    """Return the audio file for every narration line, generating only lines whose inputs changed."""
    n = storyboard.narrator
    return {
        line.id: speak(line, n.voice, storyboard, speech, cache, log, stage=STAGE, item=line.id,
                       out_dir=outputs / STAGE)
        for line in storyboard.narration
    }


def speak(line: Line, voice: str, storyboard: Storyboard, speech: SpeechProvider, cache: Cache, log: RunLog, *,
          stage: str, item: str, out_dir: Path) -> Path:
    """Audio for `line` in `voice` with the narrator's style and seed: from the cache, or one logged TTS call."""
    narrator = storyboard.narrator
    text, language = spoken_text_and_language(line)
    params = {"text": text, "language": language, "voice": voice, "style": narrator.style}
    call = Call(stage=stage, item=item, model=speech.model, params=params, seed=narrator.seed)
    key = input_hash({"kind": "speech", "model": speech.model, "seed": narrator.seed, **params})

    cached = cache.get(key)
    if cached is not None:
        log.cache_hit(call)
        return cached

    out = out_dir / f"{line.id}-{voice.lower()}-{key[:12]}.wav"
    log.call(
        call,
        lambda: speech.synthesize(text, language=language, voice=voice, style=narrator.style, seed=narrator.seed,
                                  out_path=out),
        cost_usd=speech.cost_estimate_usd(text),
    )
    cache.put(key, stage=stage, item=item, path=out)
    return out


def spoken_text_and_language(line: Line) -> tuple[str, str]:
    if line.am:
        return line.am, "am"
    return line.en, "en"


def audio_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()

"""Narration stage: one audio file per narration line, cached per line.

The narrator speaks the line's Amharic. Until the script stage has drafted
Amharic for a line, the English is spoken instead (tracer-bullet behaviour,
removed in ticket 04 when the final film requires reviewed Amharic).
"""

from __future__ import annotations

from pathlib import Path

from pipeline.cache import Cache, input_hash
from pipeline.providers import SpeechProvider
from pipeline.runlog import Call, RunLog
from pipeline.storyboard import Line, Storyboard

STAGE = "narration"


def run(storyboard: Storyboard, speech: SpeechProvider, cache: Cache, log: RunLog, outputs: Path) -> dict[str, Path]:
    """Return the audio file for every narration line, generating only lines whose inputs changed."""
    audio: dict[str, Path] = {}
    narrator = storyboard.narrator
    for line in storyboard.narration:
        text, language = _spoken_text_and_language(line)
        params = {"text": text, "language": language, "voice": narrator.voice, "style": narrator.style}
        call = Call(stage=STAGE, item=line.id, model=speech.model, params=params, seed=narrator.seed)
        key = input_hash({"stage": STAGE, "model": speech.model, "seed": narrator.seed, **params})

        cached = cache.get(key)
        if cached is not None:
            log.cache_hit(call)
            audio[line.id] = cached
            continue

        out = outputs / STAGE / f"{line.id}-{key[:12]}.wav"
        log.call(
            call,
            lambda: speech.synthesize(
                text, language=language, voice=narrator.voice, style=narrator.style, seed=narrator.seed, out_path=out
            ),
            cost_usd=speech.cost_estimate_usd(text),
        )
        cache.put(key, stage=STAGE, item=line.id, path=out)
        audio[line.id] = out
    return audio


def _spoken_text_and_language(line: Line) -> tuple[str, str]:
    if line.am:
        return line.am, "am"
    return line.en, "en"

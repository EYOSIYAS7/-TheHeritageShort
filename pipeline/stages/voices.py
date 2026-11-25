"""Voice trial (`make voices`): one narration line spoken by each candidate voice.

The author listens, sets `narrator.voice` (and `voice_reason`) in the
storyboard, and the narration stage then reuses the chosen voice's clip.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.cache import Cache
from pipeline.providers import SpeechProvider
from pipeline.runlog import RunLog
from pipeline.stages.narration import speak
from pipeline.storyboard import Storyboard

STAGE = "voices"


def run(storyboard: Storyboard, speech: SpeechProvider, cache: Cache, log: RunLog, outputs: Path) -> dict[str, Path]:
    n = storyboard.narrator
    line = next(line for line in storyboard.narration if line.id == n.trial_line)
    return {
        voice: speak(line, voice, storyboard, speech, cache, log, stage=STAGE, item=f"{line.id}@{voice}",
                     out_dir=outputs / "narration")
        for voice in n.trial_voices
    }

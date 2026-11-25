"""Small FFmpeg / audio helpers shared by stages and providers."""

from __future__ import annotations

import math
import struct
import subprocess
import wave
from pathlib import Path

TTS_SAMPLE_RATE = 24_000  # Gemini TTS returns 24 kHz mono 16-bit PCM; placeholders match it.


def run_ffmpeg(args: list[str]) -> None:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({result.returncode}): {result.stderr.strip()}\ncommand: {' '.join(cmd)}")


def write_tone_wav(path: Path, duration_s: float, *, freq_hz: float = 220.0, amplitude: float = 0.3) -> None:
    """A sine tone as 24 kHz mono 16-bit WAV, with 20 ms fades so it doesn't click."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(duration_s * TTS_SAMPLE_RATE)
    fade = int(0.02 * TTS_SAMPLE_RATE)
    frames = bytearray()
    for i in range(n):
        env = min(1.0, i / fade, (n - 1 - i) / fade) if fade else 1.0
        sample = amplitude * env * math.sin(2 * math.pi * freq_hz * i / TTS_SAMPLE_RATE)
        frames += struct.pack("<h", int(sample * 32767))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TTS_SAMPLE_RATE)
        w.writeframes(bytes(frames))

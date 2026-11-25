"""Assembly stage: pure FFmpeg, no model calls; the same inputs give the same output.

Tracer-bullet version: a black screen for the whole film (shots, saying card,
end card) with each narration line placed at its shot's start plus offset.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.media import run_ffmpeg
from pipeline.storyboard import Storyboard

WIDTH, HEIGHT, FPS = 1920, 1080, 24
AUDIO_RATE = 48_000


def run(storyboard: Storyboard, narration_audio: dict[str, Path], outputs: Path) -> Path:
    out = outputs / "film" / "film-16x9.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    total = f"{storyboard.total_s:.3f}"

    inputs = [
        "-f", "lavfi", "-t", total, "-i", f"color=c=black:s={WIDTH}x{HEIGHT}:r={FPS}",
        "-f", "lavfi", "-t", total, "-i", f"anullsrc=r={AUDIO_RATE}:cl=stereo",
    ]
    filters: list[str] = []
    mix = ["[1:a]"]
    for n, line in enumerate(storyboard.narration, start=2):
        inputs += ["-i", str(narration_audio[line.id])]
        delay_ms = round(storyboard.line_start_s(line) * 1000)
        filters.append(
            f"[{n}:a]aresample={AUDIO_RATE},aformat=channel_layouts=stereo,adelay=delays={delay_ms}:all=1[l{n}]"
        )
        mix.append(f"[l{n}]")
    # duration=first: the silent bed sets the length, so the audio is exactly the film's length.
    filters.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0[aout]")

    run_ffmpeg([
        *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", total,
        "-movflags", "+faststart",
        str(out),
    ])
    return out

"""Pan shots: a slow pan and zoom across each keyframe, rendered by FFmpeg for exactly the shot's length.

Each aspect ratio has its own pan path: a view is a centre (x, y as fractions
of the keyframe) and a zoom, where zoom 1 is the largest 16:9 or 9:16 window
that fits in the keyframe. The view moves from the start view to the end view
with an ease-in-out. A shot without a keyframe becomes a labelled placeholder,
so the cut always renders. Clips are cached by their inputs (file exists:
skip); no model is called here.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from pipeline.cache import input_hash
from pipeline.media import run_ffmpeg
from pipeline.storyboard import ASPECTS, Aspect, Shot, Storyboard

FPS = 24
SIZE: dict[Aspect, tuple[int, int]] = {"16:9": (1920, 1080), "9:16": (1080, 1920)}
RENDERER = 1  # bump to re-render every clip after changing how pans are drawn


def run(board: Storyboard, frames: dict[int, Path], outputs: Path) -> dict[Aspect, list[Path]]:
    """One clip per shot, in storyboard order, for each aspect ratio."""
    return {aspect: [render(shot, frames.get(shot.id), aspect, outputs / "shots") for shot in board.shots]
            for aspect in ASPECTS}


def render(shot: Shot, keyframe: Path | None, aspect: Aspect, out_dir: Path) -> Path:
    start, end = shot.pan[aspect]
    key = input_hash({
        "renderer": RENDERER, "aspect": aspect, "duration_s": shot.duration_s, "shot": shot.id,
        "keyframe": hashlib.sha256(keyframe.read_bytes()).hexdigest() if keyframe else None,
        "pan": [vars(start), vars(end)],
    })
    out = out_dir / f"shot-{shot.id:02}-{aspect.replace(':', 'x')}-{key[:12]}.mp4"
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    width, height = SIZE[aspect]
    frames = round(shot.duration_s * FPS)
    encode = ["-frames:v", str(frames), "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
              "-pix_fmt", "yuv420p", str(out)]

    if keyframe is None:
        label = f"Shot {shot.id}: keyframe missing"
        run_ffmpeg(["-f", "lavfi", "-i", f"color=c=0x202020:s={width}x{height}:r={FPS}",
                    "-vf", f"drawtext=font='Noto Sans':text='{label}':fontcolor=0xBBBBBB:fontsize={height // 24}"
                           ":x=(w-text_w)/2:y=(h-text_h)/2", *encode])
        return out

    # Eased progress 0 -> 1 over the shot, then the view's zoom and centre at that progress.
    p = f"min(t/{shot.duration_s}\\,1)"
    ease = f"({p})*({p})*(3-2*({p}))"
    zoom = f"({start.zoom}+({end.zoom - start.zoom})*{ease})"
    cx = f"({start.x}+({end.x - start.x})*{ease})"
    cy = f"({start.y}+({end.y - start.y})*{ease})"
    # Scale so the view (zoom 1 = widest window of this aspect in the keyframe) fills the output width.
    scale = f"{width}*{zoom}/min(iw\\,ih*{width}/{height})"
    vf = (f"scale=w='trunc(iw*{scale}/2)*2':h='trunc(ih*{scale}/2)*2':eval=frame:flags=bicubic,"
          f"crop=w={width}:h={height}:x='clip({cx}*iw-ow/2\\,0\\,iw-ow)':y='clip({cy}*ih-oh/2\\,0\\,ih-oh)',"
          "setsar=1")
    run_ffmpeg(["-loop", "1", "-framerate", str(FPS), "-i", str(keyframe), "-vf", vf, *encode])
    return out

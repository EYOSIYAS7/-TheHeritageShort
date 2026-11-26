"""Moving-shot stage: Wan 2.2 TI2V-5B image-to-video for the shots marked `"type": "moving"`.

Each moving shot's keyframe (resized to 480p) and motion prompt go to one
Kaggle job (`kaggle/wan22_i2v.py`). A clip's cache key covers its keyframe,
motion prompt, seed, model and generation settings, so only changed moving
shots are re-sent. The raw clip is then fitted to the shot: scaled and cropped
to 16:9, cropped for 9:16 around the centre of the shot's 9:16 pan (where the
people are), trimmed to the shot's length or held on its last frame.

A moving shot without a clip (no keyframe, no Kaggle keys, or the job failed)
keeps its pan shot, and the reason is logged as a `fallback` line (ADR 0001).
"""

from __future__ import annotations

import hashlib
import math
import shutil
from pathlib import Path

from pipeline.cache import Cache, input_hash
from pipeline.media import run_ffmpeg
from pipeline.providers import GpuJobs
from pipeline.runlog import Call, RunLog
from pipeline.stages.pans import FPS, SIZE
from pipeline.storyboard import ASPECTS, Aspect, Shot, Storyboard

STAGE = "moving"
MODEL = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
DIFFUSERS = "diffusers>=0.35.0"  # the first release with Wan 2.2
NOTEBOOK = Path(__file__).resolve().parents[2] / "kaggle" / "wan22_i2v.py"
WIDTH, HEIGHT = 832, 480  # 480p, multiples of 32 (VAE 16 x patch 2), close to the keyframe's 16:9
MAX_FRAMES = 81  # about 3.4 s at 24 fps; 121 (5 s) ran out of memory on a Kaggle T4 (FAILURES.md F10)
STEPS = 30
GUIDANCE = 5.0
FLOW_SHIFT = 3.0  # diffusers' advice for 480p
NEGATIVE = ("blurry, distorted hands, extra fingers, deformed faces, flicker, text, watermark, "
            "fast camera motion, cut, static image")
FIT_RENDERER = 1  # bump to re-fit every clip after changing how clips are fitted


def frames_for(duration_s: float) -> int:
    """Wan needs 4k + 1 frames: enough for the shot, at most MAX_FRAMES (a longer shot holds its last frame)."""
    k = math.ceil((duration_s * FPS - 1) / 4)
    return min(4 * k + 1, MAX_FRAMES)


def run(board: Storyboard, frames: dict[int, Path], gpu: GpuJobs, cache: Cache, log: RunLog,
        outputs: Path) -> dict[int, Path]:
    """The raw clip of every moving shot that has one (cached or generated now)."""
    clips: dict[int, Path] = {}
    todo: list[tuple[Shot, Path, str, Call]] = []
    for shot in (s for s in board.shots if s.type == "moving"):
        params = {"prompt": shot.motion_prompt, "negative_prompt": NEGATIVE, "width": WIDTH, "height": HEIGHT,
                  "num_frames": frames_for(shot.duration_s), "steps": STEPS, "guidance": GUIDANCE,
                  "flow_shift": FLOW_SHIFT, "fps": FPS}
        keyframe = frames.get(shot.id)
        call = Call(stage=STAGE, item=f"shot-{shot.id:02}", model=MODEL,
                    params={**params, "keyframe": keyframe.name if keyframe else None}, seed=shot.seed)
        if keyframe is None:
            log.fallback(call, "no keyframe: the placeholder pan shot is used")
            continue
        key = input_hash({"kind": "video", "model": MODEL, "seed": shot.seed,
                          "keyframe": hashlib.sha256(keyframe.read_bytes()).hexdigest(), **params})
        cached = cache.get(key)
        if cached is not None:
            log.cache_hit(call)
            clips[shot.id] = cached
        else:
            todo.append((shot, keyframe, key, call))

    if not todo:
        return clips
    if not gpu.available:
        for _, _, _, call in todo:
            log.fallback(call, "no Kaggle credentials in .env: the pan shot is used")
        return clips

    inputs = outputs / STAGE / "inputs"
    files: dict[str, Path] = {}
    items = []
    for shot, keyframe, _, call in todo:
        small = inputs / f"{call.item}.jpg"
        small.parent.mkdir(parents=True, exist_ok=True)
        run_ffmpeg(["-i", str(keyframe), "-vf", f"scale={WIDTH}:{HEIGHT}:flags=lanczos", "-q:v", "2", str(small)])
        files[small.name] = small
        items.append({"id": call.item, "image": small.name, "seed": shot.seed,
                      **{k: v for k, v in call.params.items() if k != "keyframe"}})
    job_call = Call(stage=STAGE, item="kaggle-job", model=gpu.model,
                    params={"notebook": NOTEBOOK.name, "items": [i["id"] for i in items], "model": MODEL}, seed=None)
    try:
        result = log.call(job_call, lambda: gpu.run(NOTEBOOK, {"items": items, "model": MODEL, "diffusers": DIFFUSERS},
                                                    files, outputs / STAGE / "job"), cost_usd=0.0)
    except Exception as e:  # logged by the run log; the film still renders with pan shots
        for _, _, _, call in todo:
            log.fallback(call, f"Kaggle job failed ({type(e).__name__}): the pan shot is used")
        return clips

    for shot, _, key, call in todo:
        seconds = result.seconds.get(call.item, 0.0)
        timed = Call(call.stage, call.item, call.model, {**call.params, "gpu_minutes": round(seconds / 60, 2)}, call.seed)
        made = result.files.get(call.item)
        if made is None:
            log.record(timed, latency_s=seconds, outcome="error", error=result.errors.get(call.item))
            log.fallback(call, "no clip from the Kaggle job: the pan shot is used")
            continue
        log.record(timed, latency_s=seconds, outcome="ok")
        out = outputs / STAGE / f"{call.item}-{key[:12]}.mp4"
        shutil.copy(made, out)
        cache.put(key, stage=STAGE, item=call.item, path=out)
        clips[shot.id] = out
    return clips


def place(board: Storyboard, pan_clips: dict[Aspect, list[Path]], moving: dict[int, Path],
          outputs: Path) -> dict[Aspect, list[Path]]:
    """The cut's clips: each moving shot's fitted clip where it has one, else its pan shot."""
    out: dict[Aspect, list[Path]] = {}
    for aspect in ASPECTS:
        out[aspect] = [fit(shot, moving[shot.id], aspect, outputs / "shots") if shot.id in moving else clip
                       for shot, clip in zip(board.shots, pan_clips[aspect])]
    return out


def fit(shot: Shot, clip: Path, aspect: Aspect, out_dir: Path) -> Path:
    """Scale and crop a raw clip to the aspect, then trim it to the shot or hold its last frame."""
    centre = shot.pan["9:16"][0].x
    key = input_hash({"renderer": FIT_RENDERER, "aspect": aspect, "duration_s": shot.duration_s,
                      "clip": hashlib.sha256(clip.read_bytes()).hexdigest(), "centre": centre})
    out = out_dir / f"shot-{shot.id:02}-moving-{aspect.replace(':', 'x')}-{key[:12]}.mp4"
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    width, height = SIZE[aspect]
    if aspect == "9:16":
        frame = (f"crop=w='trunc(ih*9/16/2)*2':h=ih:x='clip({centre}*iw-ow/2\\,0\\,iw-ow)':y=0,"
                 f"scale={width}:{height}:flags=lanczos")
    else:
        frame = f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,crop={width}:{height}"
    vf = f"fps={FPS},{frame},setsar=1,tpad=stop_mode=clone:stop_duration={shot.duration_s}"
    run_ffmpeg(["-i", str(clip), "-vf", vf, "-an", "-frames:v", str(round(shot.duration_s * FPS)), "-r", str(FPS),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(out)])
    return out

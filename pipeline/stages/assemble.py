"""Assembly stage: pure FFmpeg, no model calls; the same inputs give the same output.

Radio-cut version: a black screen for the whole film (shots, saying card, end
card), each narration line at its shot's start plus offset, burned-in English
subtitles timed from the measured audio, and a placeholder music bed (a soft
generated chord, no third-party audio) that follows the storyboard's volume
points and is ducked under the voice by sidechain compression.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.media import run_ffmpeg
from pipeline.storyboard import Storyboard
from pipeline.timing import Placed

WIDTH, HEIGHT, FPS = 1920, 1080, 24
AUDIO_RATE = 48_000
SUBTITLE_HOLD_S = 0.4  # subtitles stay up a little after the voice ends (never past the next line)
SUBTITLE_STYLE = "FontName=Noto Sans,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=1.5,Shadow=0,MarginV=40"
# A quiet A-minor pad with a slow swell: a stand-in until the ACE-Step score exists.
PAD = ("0.10*sin(2*PI*110*t)+0.07*sin(2*PI*130.81*t)+0.06*sin(2*PI*164.81*t)+0.04*sin(2*PI*220*t)")
PAD_SWELL = "(0.75+0.25*sin(2*PI*t/9))"


def run(storyboard: Storyboard, placed: list[Placed], outputs: Path, *, name: str) -> Path:
    out = outputs / "film" / f"{name}-16x9.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    srt = write_subtitles(placed, out.with_suffix(".en.srt"))
    total = f"{storyboard.total_s:.3f}"

    inputs = [
        "-f", "lavfi", "-t", total, "-i", f"color=c=black:s={WIDTH}x{HEIGHT}:r={FPS}",
        "-f", "lavfi", "-t", total, "-i", f"anullsrc=r={AUDIO_RATE}:cl=stereo",
        "-f", "lavfi", "-t", total, "-i", f"aevalsrc=({PAD})*{PAD_SWELL}:s={AUDIO_RATE}:c=stereo",
    ]
    filters: list[str] = []
    voice = ["[1:a]"]
    for n, p in enumerate(placed, start=3):
        inputs += ["-i", str(p.line_audio)]
        delay_ms = round(p.start_s * 1000)
        filters.append(
            f"[{n}:a]aresample={AUDIO_RATE},aformat=channel_layouts=stereo,adelay=delays={delay_ms}:all=1[l{n}]"
        )
        voice.append(f"[l{n}]")
    # duration=first: the silent bed sets the length, so the audio is exactly the film's length.
    filters += [
        f"{''.join(voice)}amix=inputs={len(voice)}:duration=first:normalize=0,volume=-2dB,asplit[voice][key]",
        f"[2:a]lowpass=f=1800,volume='{volume_expression(storyboard)}':eval=frame[music]",
        "[music][key]sidechaincompress=threshold=0.015:ratio=10:attack=30:release=600[ducked]",
        # Gemini TTS clips peak at 0 dBFS: the voice is lowered 2 dB above and the limiter keeps
        # voice + music under about -1 dBFS, so AAC encoding doesn't clip.
        "[voice][ducked]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89:level=false[aout]",
        f"[0:v]subtitles='{_escape(srt)}':force_style='{SUBTITLE_STYLE}'[vout]",
    ]

    run_ffmpeg([
        *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", total,
        "-movflags", "+faststart",
        str(out),
    ])
    return out


def write_subtitles(placed: list[Placed], path: Path) -> Path:
    """English SRT, one cue per narration line, from the line's start to the end of its audio (plus a hold)."""
    cues = []
    for i, p in enumerate(placed):
        end = p.end_s + SUBTITLE_HOLD_S
        if i + 1 < len(placed):
            end = min(end, placed[i + 1].start_s)
        cues.append(f"{i + 1}\n{_srt_time(p.start_s)} --> {_srt_time(end)}\n{p.line.en}\n")
    path.write_text("\n".join(cues), encoding="utf-8")
    return path


def volume_expression(storyboard: Storyboard) -> str:
    """FFmpeg expression for the music gain: linear between the storyboard's volume points."""
    points = storyboard.music_volume
    expr = f"{points[-1][1]}"
    for (t0, g0), (t1, g1) in reversed(list(zip(points, points[1:]))):
        span = t1 - t0
        ramp = f"{g0}+({g1}-{g0})*(t-{t0})/{span}" if span > 0 else f"{g1}"
        expr = f"if(lt(t\\,{t1})\\,{ramp}\\,{expr})"
    return f"if(lt(t\\,{points[0][0]})\\,{points[0][1]}\\,{expr})"


def _srt_time(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _escape(path: Path) -> str:
    """A path inside a quoted filter argument: escape the characters FFmpeg treats specially."""
    return str(path).replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")

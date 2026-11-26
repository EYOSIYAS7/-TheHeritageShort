"""Assembly stage: pure FFmpeg, no model calls; the same inputs give the same output.

The picture is the shot clips in storyboard order (or a black screen for the
radio cut), then the saying card and the end card. Each narration
line plays at its shot's start plus offset; English subtitles are timed from
the measured audio and burned in. A placeholder music bed (a soft generated
chord, no third-party audio) follows the storyboard's volume points and is
ducked under the voice by sidechain compression. Loudness is normalised as
the last audio step (-14 LUFS integrated, -1.5 dBTP: the usual target for
phones and social platforms).
"""

from __future__ import annotations

from pathlib import Path

from pipeline.media import filter_path, run_ffmpeg
from pipeline.stages.pans import FPS, SIZE
from pipeline.storyboard import Aspect, Storyboard
from pipeline.timing import Placed

AUDIO_RATE = 48_000
SUBTITLE_HOLD_S = 0.4  # subtitles stay up a little after the voice ends (never past the next line)
SUBTITLE_STYLE: dict[Aspect, str] = {
    "16:9": "FontName=Noto Sans,FontSize=20,Outline=1.5,Shadow=0,MarginV=40",
    "9:16": "FontName=Noto Sans,FontSize=11,Outline=1,Shadow=0,MarginV=70,MarginL=30,MarginR=30",
}
# A quiet A-minor pad with a slow swell: a stand-in until the ACE-Step score exists.
PAD = ("0.10*sin(2*PI*110*t)+0.07*sin(2*PI*130.81*t)+0.06*sin(2*PI*164.81*t)+0.04*sin(2*PI*220*t)")
PAD_SWELL = "(0.75+0.25*sin(2*PI*t/9))"


LOUDNESS = "loudnorm=I=-14:TP=-1.5:LRA=11"


def run(storyboard: Storyboard, placed: list[Placed], outputs: Path, *, name: str, aspect: Aspect,
        clips: list[Path] | None, cards: list[Path]) -> Path:
    """Export one cut at one aspect ratio. `clips` None means a black picture under the shots (the radio cut)."""
    out = outputs / "film" / f"{name}-{aspect.replace(':', 'x')}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    srt = write_subtitles(placed, out.with_suffix(".en.srt"))
    width, height = SIZE[aspect]
    total = f"{storyboard.total_s:.3f}"

    # Inputs: 0 silent bed, 1 music pad, then the narration lines, then the picture.
    inputs = [
        "-f", "lavfi", "-t", total, "-i", f"anullsrc=r={AUDIO_RATE}:cl=stereo",
        "-f", "lavfi", "-t", total, "-i", f"aevalsrc=({PAD})*{PAD_SWELL}:s={AUDIO_RATE}:c=stereo",
    ]
    filters: list[str] = []
    voice = ["[0:a]"]
    n = 2
    for p in placed:
        inputs += ["-i", str(p.line_audio)]
        delay_ms = round(p.start_s * 1000)
        filters.append(
            f"[{n}:a]aresample={AUDIO_RATE},aformat=channel_layouts=stereo,adelay=delays={delay_ms}:all=1[l{n}]"
        )
        voice.append(f"[l{n}]")
        n += 1

    parts = []
    if clips is None:
        inputs += ["-f", "lavfi", "-t", f"{storyboard.shots_s:.3f}", "-i", f"color=c=black:s={width}x{height}:r={FPS}"]
        clips_in = 1
    else:
        inputs += [arg for clip in clips for arg in ("-i", str(clip))]
        clips_in = len(clips)
    inputs += [arg for card in cards for arg in ("-i", str(card))]
    for _ in range(clips_in + len(cards)):
        parts.append(f"[{n}:v]")
        n += 1
    filters.append(f"{''.join(parts)}concat=n={len(parts)}:v=1:a=0,setsar=1[pic]")

    # duration=first: the silent bed sets the length, so the audio is exactly the film's length.
    # Gemini TTS clips peak at 0 dBFS: the voice is lowered 2 dB and the limiter keeps voice + music
    # under about -1 dBFS, so AAC encoding doesn't clip.
    filters += [
        f"{''.join(voice)}amix=inputs={len(voice)}:duration=first:normalize=0,volume=-2dB,asplit[voice][key]",
        f"[1:a]lowpass=f=1800,volume='{volume_expression(storyboard)}':eval=frame[music]",
        "[music][key]sidechaincompress=threshold=0.015:ratio=10:attack=30:release=600[ducked]",
        f"[voice][ducked]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89:level=false,"
        f"{LOUDNESS},aresample={AUDIO_RATE}[aout]",
        f"[pic]subtitles='{filter_path(srt)}':force_style='{SUBTITLE_STYLE[aspect]}'[vout]",
    ]

    run_ffmpeg([
        *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
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

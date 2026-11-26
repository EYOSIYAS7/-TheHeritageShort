"""Cards: the saying card and the AI end card, rendered by FFmpeg from storyboard text.

The saying card shows the Amharic saying in an Ethiopic font (Noto Sans
Ethiopic) with its English translation; the end card shows the title and the
end-card text stating the film was made with AI. Durations come from the
storyboard. Clips are cached by their inputs (file exists: skip); no model is
called here.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.cache import input_hash
from pipeline.media import filter_path, run_ffmpeg
from pipeline.stages.pans import FPS, SIZE
from pipeline.storyboard import ASPECTS, Aspect, Storyboard

RENDERER = 2
BACKGROUND = "0x14100b"  # near-black, warm
GOLD = "0xE8C27A"
PAPER = "0xD9D0C1"
GREY = "0x9A9288"
FADE_S = 0.6


def run(board: Storyboard, outputs: Path) -> dict[Aspect, list[Path]]:
    """The saying card then the end card, for each aspect ratio."""
    out_dir = outputs / "cards"
    return {aspect: [
        card("saying", aspect, board.saying_card_s,
             [(board.saying_am, "Noto Sans Ethiopic", GOLD, 1.0), (board.saying_en, "Noto Sans", PAPER, 0.45)],
             out_dir),
        card("end", aspect, board.end_card_s,
             [(board.title_am, "Noto Sans Ethiopic", GOLD, 0.8), (board.title_en, "Noto Sans", PAPER, 0.45),
              (board.end_card_text, "Noto Sans", GREY, 0.36)],
             out_dir),
    ] for aspect in ASPECTS}


def card(name: str, aspect: Aspect, duration_s: float, blocks: list[tuple[str, str, str, float]],
         out_dir: Path) -> Path:
    """A card of stacked, centred text blocks: (text, font, colour, size relative to the largest)."""
    key = input_hash({"renderer": RENDERER, "name": name, "aspect": aspect, "duration_s": duration_s,
                      "blocks": blocks})
    out = out_dir / f"{name}-{aspect.replace(':', 'x')}-{key[:12]}.mp4"
    if out.exists():
        return out
    out_dir.mkdir(parents=True, exist_ok=True)
    width, height = SIZE[aspect]
    big = width / 22 if aspect == "16:9" else width / 11

    # One drawtext per line (a newline inside drawtext renders as a missing-glyph box),
    # each centred; the blocks are stacked and the stack is centred vertically.
    laid: list[tuple[Path, str, str, int, float]] = []
    y = 0.0
    for i, (text, font, colour, scale) in enumerate(blocks):
        size = round(big * scale)
        per_line = max(8, int(width * 0.84 / (size * (0.95 if "Ethiopic" in font else 0.52))))
        for j, line in enumerate(wrap(text, per_line)):
            text_file = out_dir / f"{name}-{aspect.replace(':', 'x')}-{key[:12]}-{i}-{j}.txt"
            text_file.write_text(line, encoding="utf-8")
            laid.append((text_file, font, colour, size, y))
            y += size * 1.4
        y += size * 0.8
    top = (height - y) / 2

    draws = [
        f"drawtext=textfile='{filter_path(f)}':font='{font}':fontcolor={colour}:fontsize={size}:"
        f"x=(w-text_w)/2:y={round(top + offset)}"
        for f, font, colour, size, offset in laid
    ]
    fades = f"fade=t=in:st=0:d={FADE_S},fade=t=out:st={duration_s - FADE_S / 2:.3f}:d={FADE_S / 2}"
    run_ffmpeg(["-f", "lavfi", "-i", f"color=c={BACKGROUND}:s={width}x{height}:r={FPS}",
                "-vf", ",".join([*draws, fades, "setsar=1"]),
                "-frames:v", str(round(duration_s * FPS)), "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "18", "-pix_fmt", "yuv420p", str(out)])
    return out


def wrap(text: str, per_line: int) -> list[str]:
    """Greedy word wrap to about `per_line` characters per line."""
    lines: list[str] = []
    for word in text.split():
        if lines and len(lines[-1]) + 1 + len(word) <= per_line:
            lines[-1] += " " + word
        else:
            lines.append(word)
    return lines

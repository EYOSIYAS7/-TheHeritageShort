"""Keyframe stage: one 16:9 still per shot, the source of its pan shot.

The prompt is built only from storyboard text: the shot's keyframe prompt,
the fixed description of each character in the shot, the global style words
and the shot's grade words. When `style.reference_images` is true, the
character-sheet images of the shot's characters are passed as FLUX.2 klein
reference images; either way the choice is in the logged parameters. The
cache key covers the prompt (so style, grade and descriptions), the seed, the
size, the model and the reference images used.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.cache import Cache
from pipeline.providers import ImageProvider
from pipeline.runlog import RunLog
from pipeline.stages.characters import draw, join_prompt
from pipeline.storyboard import Shot, Storyboard

STAGE = "keyframes"
SIZE = (1920, 1088)  # 16:9, both sides multiples of 16; the 9:16 pan crops from it


def run(board: Storyboard, image: ImageProvider, sheet: dict[str, Path], cache: Cache, log: RunLog,
        outputs: Path) -> dict[int, Path]:
    """The keyframe of every shot that has one; shots left out get a labelled placeholder downstream."""
    frames: dict[int, Path] = {}
    for shot in board.shots:
        references = tuple(sheet[name] for name in shot.characters if name in sheet) \
            if board.style.reference_images else ()
        made = draw(STAGE, f"shot-{shot.id:02}", prompt_for(board, shot), shot.seed, SIZE, references,
                    image, cache, log, outputs / STAGE)
        if made is not None:
            frames[shot.id] = made
    return frames


def prompt_for(board: Storyboard, shot: Shot) -> str:
    people = [f"The {name.replace('_', ' ')}: {board.characters[name].description}" for name in shot.characters]
    return join_prompt([shot.keyframe_prompt, *people, board.style.words, board.style.grades[shot.grade]])

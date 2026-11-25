"""Character-sheet stage: one reference image per character, before any keyframe.

The prompt is the storyboard's character-sheet text, the character's fixed
description and the global style words; the seed is the character's own.
Keyframes are conditioned on these images when `style.reference_images` is
true (see the keyframe stage).
"""

from __future__ import annotations

from pathlib import Path

from pipeline.cache import Cache, input_hash
from pipeline.providers import ImageProvider
from pipeline.runlog import Call, RunLog
from pipeline.storyboard import Storyboard

STAGE = "characters"
SIZE = (1024, 1024)


def run(board: Storyboard, image: ImageProvider, cache: Cache, log: RunLog, outputs: Path) -> dict[str, Path]:
    """The reference image for each character that has one (cached or newly made); missing ones are left out."""
    sheet: dict[str, Path] = {}
    for name, character in board.characters.items():
        prompt = join_prompt([board.style.character_sheet, character.description, board.style.words])
        made = draw(STAGE, name, prompt, character.seed, SIZE, (), image, cache, log, outputs / STAGE)
        if made is not None:
            sheet[name] = made
    return sheet


def join_prompt(parts: list[str]) -> str:
    """Storyboard text fragments joined into one prompt, one sentence each."""
    return " ".join(part.strip().rstrip(".") + "." for part in parts if part.strip())


def draw(stage: str, item: str, prompt: str, seed: int, size: tuple[int, int], references: tuple[Path, ...],
         image: ImageProvider, cache: Cache, log: RunLog, out_dir: Path) -> Path | None:
    """One image: from the cache, or one logged call. None if it isn't cached and the provider has no keys."""
    width, height = size
    params = {"prompt": prompt, "width": width, "height": height, "references": [p.name for p in references]}
    key = input_hash({"kind": "image", "model": image.model, "seed": seed, **params})
    call = Call(stage=stage, item=item, model=image.model, params=params, seed=seed)

    cached = cache.get(key)
    if cached is not None:
        log.cache_hit(call)
        return cached
    if not image.available:
        return None

    out = out_dir / f"{item}-{key[:12]}.jpg"  # Workers AI FLUX.2 returns JPEG
    log.call(call, lambda: image.generate(prompt, seed=seed, width=width, height=height, out_path=out,
                                          references=references),
             cost_usd=image.cost_estimate_usd(prompt))
    cache.put(key, stage=stage, item=item, path=out)
    return out

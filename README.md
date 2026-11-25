# Tomorrow, Dad (ነገ አባባ ነገ)

A 60–90 s short film built around the Amharic saying **በእጅ የያዙት ወርቅ እንደ መዳብ ይቆጠራል** ("gold held in the hand is counted as copper"), and the pipeline that regenerates it from one file, `storyboard.json`.

## One command

```sh
make film
```

Requirements: `python3` with `venv`, and `ffmpeg`/`ffprobe` on the PATH (Ubuntu: `sudo apt install ffmpeg make python3-venv`). The first run creates `.venv/` and installs the Python dependencies.

What it does, in order:

1. **Validates** `storyboard.json` against `schema/storyboard.schema.json`, then checks shot references and that the film is 60–90 s long. Any problem stops the run before a single model call, with a message naming the shot or line and the field.
2. **Narration:** one audio file per narration line. Cached by a hash of the line's inputs, so only changed lines are regenerated.
3. **Assembly:** FFmpeg places each line at its shot's start plus offset and exports `outputs/film/film-16x9.mp4`.

Every model call (and every cache hit) is logged as one JSON line in `runs.jsonl`. The cache manifest (`outputs/cache-manifest.json`, input hash → file) is committed with the outputs, so a clean clone with no API keys rebuilds the film.

**Current state (tracer bullet):** the picture is a black screen and the narration is a placeholder tone as long as each line. Gemini TTS, keyframes, moving shots, score, subtitles and the 9:16 export arrive in later stages.

**Cost so far:** $0. The placeholder runs locally.

## Other commands

| Command | What it does |
|---|---|
| `make test` | pytest suite at the pipeline entry point (fake providers, real FFmpeg) |
| `make typecheck` | mypy, strict |

## Secrets

Copy `.env.example` to `.env` (git-ignored) and fill in the keys you have. Every key is optional. Keys are read only from `.env`, never from the shell environment.

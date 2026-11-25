# Tomorrow, Dad (ነገ አባባ ነገ)

A 60–90 s short film built around the Amharic saying **በእጅ የያዙት ወርቅ እንደ መዳብ ይቆጠራል** ("gold held in the hand is counted as copper"), and the pipeline that regenerates it from one file, `storyboard.json`.

## One command

```sh
make film
```

Requirements: `python3` with `venv`, and `ffmpeg`/`ffprobe` on the PATH (Ubuntu: `sudo apt install ffmpeg make python3-venv`). The first run creates `.venv/` and installs the Python dependencies.

What it does, in order:

1. **Validates** `storyboard.json` against `schema/storyboard.schema.json`, then checks shot references and that the film is 60–90 s long. Any problem stops the run before a single model call, with a message naming the shot or line and the field.
2. **Script:** Gemini drafts the Amharic for every narration line that isn't pinned (`gemini-3.5-flash`, with `gemini-3.8-flash` as fallback), from its English and the translation instruction in `storyboard.json`. Drafts are written back marked unreviewed. A line is redrafted only when its English changes. Without `GEMINI_API_KEY` the committed drafts are reused.
3. **Narration:** Gemini TTS (`gemini-3.8-flash-tts`, voice Enceladus) speaks each line's Amharic into its own file. Cached by a hash of the line's inputs, so only changed lines are regenerated. Each line's audio is measured: a line that overlaps the next one or runs past the last shot stops the run, naming the line and the overrun in seconds.
4. **Assembly:** FFmpeg places each line at its shot's start plus offset and exports `outputs/film/film-16x9.mp4`.

Every model call (and every cache hit) is logged as one JSON line in `runs.jsonl`. The cache manifest (`outputs/cache-manifest.json`, input hash → file) is committed with the outputs, so a clean clone with no API keys rebuilds the film.

**Current state (rough cut):** 12 illustrated keyframes (Cloudflare Workers AI, FLUX.2 klein 4B) as pan shots, with real Amharic narration, burned-in English subtitles and a placeholder music bed, 89.5 s, in 16:9 and 9:16. The moving shots (Wan 2.2), the ACE-Step score and the saying and end cards arrive in later stages.

**Cost so far:** $0. The placeholder runs locally.

## Other commands

| Command | What it does |
|---|---|
| `make review` | lists narration lines whose Amharic hasn't been reviewed, English beside Amharic. Correct `am` in `storyboard.json`, then set `am_reviewed: true`. |
| `make voices` | the voice trial: one narration line in each candidate voice (`narrator.voice_trial`), for picking the narrator by ear |
| `make rough-cut` | the character sheet, a FLUX.2 klein keyframe per shot and FFmpeg pan shots, with narration, subtitles and music: `outputs/film/rough-cut-16x9.mp4` and `-9x16.mp4`. A shot without a keyframe (no Cloudflare keys and nothing cached) shows a labelled placeholder. |
| `make radio-cut` | narration, burned-in English subtitles and a placeholder music bed (ducked under the voice) on a black screen: `outputs/film/radio-cut-16x9.mp4`, for user test 1. Allows unreviewed Amharic; `make film` refuses it. |
| `make test` | pytest suite at the pipeline entry point (fake providers, real FFmpeg) |
| `make typecheck` | mypy, strict |

## Secrets

Copy `.env.example` to `.env` (git-ignored) and fill in the keys you have. Every key is optional. Keys are read only from `.env`, never from the shell environment.

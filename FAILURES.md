# Failures

What broke, what was tried, what fixed it. Evidence for each entry is in `runs.jsonl` (filter by `stage` and `model`).

## F1. Gemini 3.8 Flash answers 503 "high demand" in long bursts (2026-11-25)

- **What broke:** Gemini text (`gemini-3.8-flash`), called once per run by a smoke test (since removed; its calls are in `runs.jsonl`, stage `smoke`). Across 5 smoke runs on 2026-11-25 the text call succeeded twice and failed 3 times: 16 attempts answered `HTTP 503: This model is currently experiencing high demand`. Successful calls took 71–90 s.
- **Tried:** the run log's default 3 attempts (backoff 2 s, 4 s) were not enough; then 5 attempts (2+4+8+16 = 30 s of backoff). The last run still failed after 5 attempts.
- **Status:** open. The TTS model (`gemini-3.8-flash-tts`) on the same key answered every time (one 503 retried). Options for the script stage (ticket 03): longer backoff for text calls, or fall back to `gemini-3.8-flash-lite`/`gemini-3.5-flash` and log which model answered. Because the Amharic draft is written back into `storyboard.json` and cached, the script stage only needs to succeed once.

## F2. Gemini TTS read more than the line with a one-line style prefix (2026-11-25)

- **What broke:** with the prompt `Say this in Amharic, <style>:\n<line>`, the three-word line ነገ አባባ ነገ came back as 11.8 s of audio, about 8.8 s of it before the line itself. FFmpeg's silencedetect finds 8 separate sound segments.
- **Fixed:** director's notes kept separate from the transcript (EXPERIMENTS.md E1). Same line, voice and seed: 2.7 s.

## Not yet verified (keys missing in `.env`; the smoke test was dropped)

- **Cloudflare FLUX.2 klein** (`@cf/black-forest-labs/flux-2-klein-4b`): the adapter follows the model page (multipart form, base64 `result.image`), but the field names (`prompt`, `seed`, `width`, `height`, `input_image_0`…) are not on the model page and have not been checked against the live API yet. Whether it accepts reference images is also still open; the first keyframe-stage run will settle both.
- **Kaggle**: the adapter authenticates against the REST API (`/api/v1/kernels/list?mine=true`) with basic auth, or bearer for the newer `KGAT_` tokens. Not yet run; the first GPU-stage run will settle it.

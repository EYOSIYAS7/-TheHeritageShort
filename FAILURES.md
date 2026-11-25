# Failures

What broke, what was tried, what fixed it. Evidence for each entry is in `runs.jsonl` (filter by `stage` and `model`).

## F1. Gemini 3.8 Flash answers 503 "high demand" in long bursts (2026-11-25)

- **What broke:** Gemini text (`gemini-3.8-flash`), called once per run by a smoke test (since removed; its calls are in `runs.jsonl`, stage `smoke`). Across 5 smoke runs on 2026-11-25 the text call succeeded twice and failed 3 times: 16 attempts answered `HTTP 503: This model is currently experiencing high demand`. Successful calls took 71–90 s.
- **Tried:** the run log's default 3 attempts (backoff 2 s, 4 s) were not enough; then 5 attempts (2+4+8+16 = 30 s of backoff). The last run still failed after 5 attempts.
- **Again in the first script-stage run (new key, same day):** `gemini-3.8-flash` failed every one of the 12 lines: 8 attempts answered 503, 28 answered `429` (quota). The fallback `gemini-3.5-flash` drafted all 12 (one 503 retried).
- **Fixed (worked around):** the script stage tries text models in order and logs which one answered (`pipeline/providers.py: TEXT_MODELS`). `gemini-3.5-flash` now goes first and `gemini-3.8-flash` is the fallback. Drafts are written into `storyboard.json` and cached, so they are made once.
- **Earlier note:** The TTS model (`gemini-3.8-flash-tts`) on the same key answered every time (one 503 retried). 

## F2. Gemini TTS read more than the line with a one-line style prefix (2026-11-25)

- **What broke:** with the prompt `Say this in Amharic, <style>:\n<line>`, the three-word line ነገ አባባ ነገ came back as 11.8 s of audio, about 8.8 s of it before the line itself. FFmpeg's silencedetect finds 8 separate sound segments.
- **Fixed:** director's notes kept separate from the transcript (EXPERIMENTS.md E1). Same line, voice and seed: 2.7 s.

## Not yet verified (keys missing in `.env`; the smoke test was dropped)

- **Cloudflare FLUX.2 klein** (`@cf/black-forest-labs/flux-2-klein-4b`): the adapter follows the model page (multipart form, base64 `result.image`), but the field names (`prompt`, `seed`, `width`, `height`, `input_image_0`…) are not on the model page and have not been checked against the live API yet. Whether it accepts reference images is also still open; the first keyframe-stage run will settle both.
- **Kaggle**: the adapter authenticates against the REST API (`/api/v1/kernels/list?mine=true`) with basic auth, or bearer for the newer `KGAT_` tokens. Not yet run; the first GPU-stage run will settle it.

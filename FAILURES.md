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

## F3. Gemini TTS free tier: 10 requests per day per project (2026-11-25)

- **What broke:** `make radio-cut` stopped at the first new narration line: `429 … generate_content_free_tier_requests, limit: 10, model: gemini-3.8-flash-tts … per day`. The new key shares its Google Cloud project, and so its daily quota, with the first key, which had already spent its requests on the smoke test and the TTS prompt experiment (E1).
- **Also broke:** the run log retried quota errors after 2 s and 4 s, and the first fix (wait for Google's `retryDelay`) then slept for hours on a daily limit. Fixed: a `retryDelay` up to 120 s is waited out (per-minute limits); a longer one is treated as permanent and fails at once.
- **Lesson:** at 10 TTS calls a day, every exploratory call costs a narration line. The full narration is 13 lines; the voice trial costs 3.

## F4. Narration overlapped once it was real (2026-11-25)

- **What broke:** `make radio-cut` stopped with 7 overlaps in the closing passage, for example: `narration line 'closing-06' (8.67 s of audio) overlaps line 'closing-07' by 1.97 s`. The storyboard had been timed with placeholder audio.
- **Fixed:** this is the timing check doing its job (built in ticket 04). Two lines were cut and Act 4 retimed from the measured audio (EXPERIMENTS.md E6).

## F5. Rate-limit handling slept for hours (2026-11-25)

- **What broke:** after the first fix for F3, the run log waited out Google's `retryDelay`, which for a daily quota was 39,533 s.
- **Fixed:** a `retryDelay` over 120 s is treated as a permanent error, and the run fails at once naming the quota.

## F6. FFmpeg filter syntax: colons and newlines (2026-11-26)

- **What broke:**
  - The missing-keyframe placeholder label "Shot 1: keyframe missing" ended the `drawtext` option at the colon, so a clean run with no image keys crashed. The ticket-08 seam test caught it.
  - The font name "Noto Sans:italic" broke the same way.
  - A newline inside a `drawtext` text file rendered as a missing-glyph box at the end of each card line.
- **Fixed:** no colons in labels; plain font names (no italic Noto is installed anyway); one `drawtext` per line.

## F7. Workers AI returns JPEG, not PNG (2026-11-26)

- **What broke:** the first character-sheet images were saved as `.png` but contain JPEG data.
- **Fixed:** images are saved as `.jpg`, and the three early files were renamed in the cache manifest. FFmpeg read them fine either way.

## F8. Pushing the final MP4s to GitHub failed (2026-11-26)

- **What broke:** the commit adding `film-16x9.mp4` and `film-9x16.mp4` (about 55 MB) failed to push over HTTPS ("the remote end hung up").
- **Fixed (decision):** the author ruled that no media goes to GitHub (ADR 0003). All images, audio and video are git-ignored, and the unpushed commit was amended so the MP4s never entered history.
- **Trade-off:** a fresh clone needs keys to regenerate the media.

## Moved or changed from the brief

- **Gemini models:** the brief's "Gemini 3.8 Flash" exists (`gemini-3.8-flash`, `gemini-3.8-flash-tts`). But on the free tier the text model was unusable for these two days (F1), and TTS allows only 10 requests a day per project (F3).
- **Cloudflare FLUX.2 klein:** the model page documents only an opaque `multipart` input. The field names (`prompt`, `seed`, `width`, `height`, `input_image_N`) were confirmed by the first real run.
  - Reference images are accepted (EXPERIMENTS.md E2), but more than one per keyframe hurts composition (E3).
  - Output is JPEG (F7).
- **Kaggle:** not used yet (tickets 06 and 07). The adapter authenticates with either legacy username+key or the newer `KGAT_` bearer tokens; neither has been tried live.

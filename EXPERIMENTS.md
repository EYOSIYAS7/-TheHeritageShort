# Experiments

Hypothesis → change → result. Every call made for an experiment is in `runs.jsonl` (stage `tts-prompt-experiment` for E1).

## E1. Gemini TTS prompt layout (2026-11-25)

- **Hypothesis:** a one-line style prefix (`Say this in Amharic, slow, warm…:`) is read aloud or padded, because the 3-word line came back 11.8 s long.
- **Change:** same line (ነገ አባባ ነገ), voice (Charon), seed (4242) and model (`gemini-3.8-flash-tts`), three prompt layouts: (a) colon prefix, (b) a `### DIRECTOR'S NOTES` block (language, style, "read only the transcript") then `### TRANSCRIPT`, (c) the bare line with no style. Each result was transcribed by `gemini-3.5-flash`.
- **Result:** (a) 11.82 s; the transcriber heard about 8.8 s before the line. (b) 2.68 s. (c) 2.60 s. Layout (b) keeps the style instruction at almost the length of the bare line, so `GeminiSpeech` uses it.
- **Caveats:** the transcriber gave the Amharic back in different spellings each time (ነገ አባባ ነገ / "Naga a baba. Naga" / እኔ አባባ እኔ), so it can judge length and extra speech, not pronunciation. The author judges that by ear when the narration stage switches to Gemini TTS (ticket 04). The same seed gave 2.68 s on one run and 3.11 s on another, so Gemini TTS is not fully deterministic by seed.

## E2. FLUX.2 klein reference images on Cloudflare Workers AI (2026-11-26)

- **Hypothesis:** passing the character-sheet images (Father, Son, coffee corner) as `input_image_0..2` keeps the characters recognisable across the 12 keyframes, if Workers AI accepts reference images at all. This was the open question from the dropped smoke test.
- **Change:** `style.reference_images: true`; each keyframe gets its shot's characters' sheet images, plus the fixed descriptions in the prompt.
- **Result:** accepted. 12 of 12 keyframes on the first attempt, 8–18 s each. The references are clearly used: the Father (white netela, grey hair and stubble) and the coffee corner (black pot, rush stool, tray of white cups) are the same in every shot.
- **Side effects, to fix next:**
  - The references are copied too literally. The coffee corner arrives with its plain studio background, so shots 2, 4, 5 and 8 have white voids instead of a room.
  - The Son's sheet holds a phone, so the phone appears in shot 12, where he should have put it away.
  - The Son is drawn as a child in shots 2, 10 and 12, despite "about thirty".
  - The copper grade barely shows in Acts 1–3.

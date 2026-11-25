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

## E3. How many reference images per keyframe (2026-11-26)

- **Hypothesis:** the E2 side effects come from the prompts and the Son's description, not from the references themselves.
- **Change 1 (prompts only):**
  - The Son is described as "a grown man… an adult not a boy", and his phone is taken out of his description (it stays only where a shot's prompt asks for it).
  - Room setting added to shots 2, 4, 5 and 8, stronger copper words, and shot 6 rewritten to show the Father in a hospital bed (the author's note: without him there, the fall is unreadable).
  - 13 images (the Son's sheet plus 12 keyframes), all references still passed.
- **Result 1:** the rooms, the copper grade and the Son's age are fixed (shots 1, 2, 5, 7, 8). But every shot with 2–3 references got worse: the model pasted a reference figure instead of composing the scene.
  - shot 3: the Son in the Father's netela
  - shot 4: two Fathers
  - shot 6: the Son alone on white, no hospital
  - shot 10: no people
  - shot 11: a handshake with a stranger
  - shot 12: the Son alone
- **Change 2:** a per-shot `references` list in the storyboard: only the main character's sheet for shots 3, 4, 6, 9, 10, 11 and 12 (7 images).
- **Result 2:** shots 3, 6, 11 and 12 now compose correctly (the hospital bed with the Son beside it; the hand-hold; side by side). Shot 10 still failed (two old men in a garden).
- **Change 3:** shot 10 with no references, descriptions only (1 image). **Result:** correct staging (the Son laying his phone face-down beside the Father). The cost is likeness: the Father is drawn in a blue shirt.
- **Conclusion:** on Workers AI FLUX.2 klein 4B, one reference image keeps a character; two or three make the model copy instead of compose. Total for the keyframes so far: 36 images (3 + 12, then 13, 7 and 1).

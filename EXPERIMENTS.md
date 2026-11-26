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

## E4. Narrator voice trial (2026-11-25)

- **Hypothesis:** one of three male Gemini TTS voices will suit "the older Son looking back" in Amharic better than the default (Charon).
- **Change:** `make voices` spoke the same line, closing-05 (ግን ህይወት ሌላ ነገን ቃል አትገባልንም።), in Charon, Iapetus and Enceladus, with the same style instruction and seed. Logged as stage `voices`.
- **Result:** Charon 3.43 s, Iapetus 4.07 s, Enceladus 3.99 s. The author listened and chose **Enceladus**, because "it feels like real talk": a man speaking to you rather than reading. This is recorded in `narrator.voice_reason`.
- **Reuse:** the trial clip in the chosen voice became closing-05's narration (cache hit), so the trial cost one call fewer.

## E5. Which text model drafts the Amharic (2026-11-25)

- **Hypothesis:** the newest Flash (`gemini-3.8-flash`) gives the best Amharic, with `gemini-3.5-flash` as a fallback.
- **Change:** the script stage tries the models in order and logs which one answered.
- **Result:** `gemini-3.8-flash` drafted **0 of 12** lines (36 attempts: 503 "high demand", then 429 quota). `gemini-3.5-flash` drafted **12 of 12**, at 7–46 s per line.
- **Decision:** `gemini-3.5-flash` goes first. The quality of the two models was never compared, because 3.8 never answered. The author reviewed every line and rewrote four (E7).

## E6. Does the storyboard timing survive the real voice? (2026-11-25/26)

- **Hypothesis:** the timing planned with the placeholder narration (about 2.5 words per second) fits the real Amharic narration.
- **Change:** the real Enceladus audio was measured, and the timing check ran on it.
- **Result:** no. **7 overlaps**, all in the closing passage. closing-06 alone is 8.67 s and overlapped closing-07 by 1.97 s. The full closing would need about 43 s of speech, in about 37 s of room.
- **What changed:**
  - The author cut closing-02 and closing-03 ("Another cup of coffee." / "Another story to hear.").
  - The narration-free shots 7–8 went from 5 s to 4 s.
  - Act 4 was retimed from the measured lengths: each cut lands 0.3 s before its first line, with 0.5 s between lines, and the music volume points moved with it.
  - The film went from 84 s to 89.5 s. Retiming made no model calls.

## E7. Author's Amharic vs the Gemini drafts (2026-11-26)

- **Hypothesis:** the reviewed Gemini drafts are good enough to speak as they are.
- **Change:** the author edited four lines.
  - **closing-04:** "postpone *to tomorrow*" (ወደ ነገ እናስተላልፍ), tying the line to the film's word.
  - **closing-09:** the plural "you" (ከጎናችሁ), to match closing-07 and 08.
  - **tomorrow-1, closing-08, closing-09:** rewritten as more natural speech. The coffee invitation "አባባ ነገ እንጠጣለን አብረን።" ties the Son's promise to the ceremony, and "chat with them while they can" replaces a literal "listen". The English subtitles were updated to match, and `am_from_en` kept the drafts from being regenerated.
- **Result:** exactly 3 TTS calls, for the three changed lines; everything else was a cache hit.
- **Measured lengths:**

| Line | Before | After |
|---|---|---|
| tomorrow-1 | 2.64 s | 3.17 s |
| closing-08 | 4.07 s | 2.84 s |
| closing-09 | 4.87 s | 4.98 s |

All three still pass the timing check.

## E8. Mix headroom (2026-11-26)

- **Hypothesis:** a limiter on the final mix keeps voice plus music from clipping.
- **Change 1:** an `alimiter` at 0.89 (about -1 dBFS) on the final mix. **Result:** the export still peaked at 0.0 dB. The Gemini TTS clips are themselves normalised to 0 dBFS (all 13 measured), and AAC encoding overshoots.
- **Change 2:** the voice lowered by 2 dB before mixing, plus the limiter. **Result:** the peak dropped to -0.9 dB, with no clipping.

## E9. Loudness target (2026-11-26)

- **Hypothesis:** one pass of FFmpeg `loudnorm` (I=-14 LUFS, TP=-1.5 dBTP, LRA=11), as the last audio step, lands both exports on -14 LUFS, the usual target for phones and social platforms.
- **Result:** measured with `ebur128`, both exports are **-15.0 LUFS** integrated. Single-pass loudnorm in dynamic mode undershoots on this quiet, speech-led mix. That's accepted, being 1 LU under the target. A two-pass (measured) loudnorm would close the gap.
- **Update (final film, with the ACE-Step score and the click fix):** -14.2 LUFS integrated, measured the same way.

## E10. 9:16 framing: centre crop vs aimed pans (2026-11-26)

- **Hypothesis:** the 9:16 version can crop the middle of each 16:9 keyframe (x = 0.5), because the style words ask for "subject in the central third".
- **Result:** no. The 9:16 window is only a third of the keyframe's width, and the model rarely kept people in the centre. In shot 2 the centre crop showed an empty stool, with the Father and the Son both cut off.
- **Change:** each shot's 9:16 pan path now aims at where its people are in the final keyframe, from looking at each one. In two-person shots it travels from one person to the other (shot 2: Father → Son; shot 6: the bed → the Son; shot 10: Son → Father). The change is in `storyboard.json` (`pan["9:16"]`), and it cost no model calls.
- **Cost:** mid-pan frames in two-person shots briefly show the wall between the two people.

## E11. Score: three ACE-Step 1.5 candidates from one caption (2026-11-26)

- **Hypothesis:** the turbo model (8 steps, shift 3.0) can make a 92 s instrumental in the spirit of tizita from the storyboard's caption alone (krar, masenqo, soft piano; sparse to fuller; no vocals). Three seeds (3001–3003) give enough choice without a second round.
- **Result:** one Kaggle job made all three on a T4.
  - **Time:** 7–10 s of GPU time per candidate. The job took 8 min in all, nearly all of it installing ACE-Step and downloading its weights.
  - **Length:** every candidate is exactly 92.0 s.
  - **Loudness:** -15.6, -13.7 and -17.0 LUFS (`ebur128`). That's 10 LU or more above the old pad, so assembly first brings the track to -26 LUFS, then applies the volume points and ducking.
- **Choice:** the author picked **candidate 1**: "it feels close to tizita". It's recorded as `music.chosen` / `music.reason` and copied to `outputs/music/chosen.wav` as the fallback track.

## E12. Moving shots vs pan shots (2026-11-26)

- **Plan (ADR 0001):** compare Wan 2.2 TI2V-5B clips against the pan shots of the same three shots (4 the pour, 5 the jebena falls, 11 the hand-hold).
- **Result:** the first two Kaggle T4 attempts failed on memory, and the third worked: encode the prompts first, then free the text encoder (FAILURES.md F10). All three clips came back at 832×480, 3.4 s each, about 15 min of T4 time per clip.
- **Comparison, first and last frame of each clip against its pan shot:**
  - **Shot 4:** the Father's hand moves to the jebena; the pan only drifts toward the cups.
  - **Shot 5:** a cup tips and the spill spreads across the mat. This is the fall itself, which the pan could only imply.
  - **Shot 11:** the hands close and the faces shift slightly.
- **Costs:**
  - **Resolution:** 480p clips are upscaled about 2.3× for 16:9, and about 4× from a 270-pixel-wide crop for 9:16, so they're softer than the pan shots.
  - **Length:** clips are 3.4 s, so shorter shots hold the last frame briefly, and shot 11 (13.7 s) moves for 3.4 s and then holds still for about 10 s.
- **Kept:** the movement in shots 5 and 11 carries the story's two turning points; by the deadline rule, no second pass.

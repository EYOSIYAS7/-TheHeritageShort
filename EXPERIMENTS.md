# Experiments

Hypothesis → change → result. Every call made for an experiment is in `runs.jsonl` (stage `tts-prompt-experiment` for E1).

## E1. Gemini TTS prompt layout (2026-11-25)

- **Hypothesis:** a one-line style prefix (`Say this in Amharic, slow, warm…:`) is read aloud or padded, because the 3-word line came back 11.8 s long.
- **Change:** same line (ነገ አባባ ነገ), voice (Charon), seed (4242) and model (`gemini-3.8-flash-tts`), three prompt layouts: (a) colon prefix, (b) a `### DIRECTOR'S NOTES` block (language, style, "read only the transcript") then `### TRANSCRIPT`, (c) the bare line with no style. Each result was transcribed by `gemini-3.5-flash`.
- **Result:** (a) 11.82 s; the transcriber heard about 8.8 s before the line. (b) 2.68 s. (c) 2.60 s. Layout (b) keeps the style instruction at almost the length of the bare line, so `GeminiSpeech` uses it.
- **Caveats:** the transcriber gave the Amharic back in different spellings each time (ነገ አባባ ነገ / "Naga a baba. Naga" / እኔ አባባ እኔ), so it can judge length and extra speech, not pronunciation. The author judges that by ear when the narration stage switches to Gemini TTS (ticket 04). The same seed gave 2.68 s on one run and 3.11 s on another, so Gemini TTS is not fully deterministic by seed.

# Ethics: consent, licences, labelling

## Consent

**No real person is depicted or voiced.** "Tomorrow, Dad" is a **composite story**: it is built around a traditional saying and from versions of the same situation the author has heard from different people. The Father and the Son are fictional characters. No photograph, likeness or voice of any real person is used as input to any model, and no voice is cloned. The narrator is a stock synthetic voice (Gemini TTS).

Because no real person appears, no consent form is required. Recorded on 2026-11-25, before anything was generated. If a real person's likeness or voice is ever added, their recorded, informed consent goes here **before** generation.

## Private data

No private family details are sent to any model. Prompts describe fictional characters and a generic Addis Ababa home.

## Licences

Every model and output is listed here as it is chosen. The table is completed in ticket 09.

| Component | Used for | Licence / terms | Notes |
|---|---|---|---|
| Storyboard, code, docs | everything | the author's own work | |
| Placeholder speech (local sine tone) | tracer-bullet narration stand-in | generated locally, no third-party content | replaced by Gemini TTS |
| Gemini (text, TTS) | Amharic draft, narration | Google Gemini API terms | to confirm |
| FLUX.2 klein on Cloudflare Workers AI | character sheet, keyframes | to confirm | |
| Wan 2.2 TI2V-5B | moving shots | Apache 2.0 (per the brief; to confirm on the model card) | |
| ACE-Step 1.5 | score | open weights; outputs usable commercially (per the brief; to confirm on the model card) | |
| Noto Sans Ethiopic | saying card, subtitles | SIL Open Font License 1.1 (to confirm) | |

## Labelling plan

- The film ends with a visible **end card** stating it was made with AI.
- When posting, the platform's AI-content disclosure is switched **on**.
- SynthID / C2PA watermarks and metadata are left intact: no re-encoding step strips them deliberately.

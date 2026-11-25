# 05 Consent, Labelling, Licences + Raising the Ceiling

Record how you handled each item below in `ETHICS.md`. Consent is the one that affects grading (see gate in `04-submission-grading.md`).

## Consent, labelling, licences
- **Consent for likeness and voice**: Gemini TTS can replicate a voice. If a real person's voice or face appears, get their recorded, informed consent for this use, and confirm the words put in their mouth are ones they agreed to.
- **Labelling**: YouTube, TikTok and Meta ask you to disclose realistic AI content; switch disclosure ON when posting. The AI end card is a film deliverable. Leave watermarks and provenance metadata (SynthID, C2PA) intact.
- **Licences**: note the licence of every model and output as you choose them. Wan 2.2 is Apache 2.0; ACE-Step 1.5 outputs may be used commercially; other models carry their own terms.
- **Style**: describe qualities (warm, grainy, hand-painted) rather than naming a living artist; avoids borrowing someone's identity.
- **Private data**: several free endpoints may use what you send to train models; keep private family details out of those.

## Raising the ceiling (optional; floor has no ceiling)
Judged on insight, not volume. One well-measured experiment that changed your mind beats five bolted-on features. Describe what you did and what it taught you in the report. Own ideas often beat these:
- **More languages**: make the film in Afaan Oromo, Tigrinya or Somali as well. Not confirmed that every model handles them well: find out and document exactly where they fail.
- **A song instead of a score**: write lyrics in your language, generate a song with ACE-Step, cut a lyric video with timed captions. Test how well it pronounces your language.
- **A real benchmark**: same shot with an open model and a frontier model; record cost and latency; run a blind preference test with >=5 people.
- **A tool for others**: package the pipeline as a CLI or MCP server so someone else (or their coding agent) can make a film from a storyboard.
- **A tool for your family**: small web app where a non-coding relative tells their own story and gets a film back.
- **Better consistency**: train a small LoRA on your character sheet and measure whether consistency improves.
- **The audience itself**: after posting, measure the response and report what you learned about what people share.

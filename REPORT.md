# Report: Tomorrow, Dad (ነገ አባባ ነገ)

B2W0 AI-Content Generation. Codebase: this repository. Film: 89.5 s, 9:16 and 16:9.

## 1. What I set out to make, and for whom

A short film built on the Amharic saying **በእጅ የያዙት ወርቅ እንደ መዳብ ይቆጠራል**, "gold held in the hand is counted as copper": what we already have, we stop valuing.

- **The story:** an elderly father makes coffee every morning and wants to talk. His adult son keeps saying "tomorrow, Dad", until the father has a stroke. The son learns, nearly too late, to sit down for the coffee and listen.
- **No real person:** it is a composite of versions of the same situation I have heard from different people, so no real person is shown or voiced (`ETHICS.md`).
- **Audience:** my close friends, people my age, busy with work and phones, whose parents are getting older.
- **Intent:** after watching, they should want to call someone they love tonight.
- **Both written first:** the audience and intent were written in `DESIGN.md` before anything was generated.
- **Form:** narrated in Amharic by one voice (the son, older, looking back), with English subtitles, four acts, a copper colour grade that turns gold in the last act, and a tizita-spirited score.
- **The pipeline:** `make film` rebuilds the whole film from one file, `storyboard.json`. The file is validated against a JSON Schema first, every output is cached by a hash of its inputs, and every model call goes into `runs.jsonl` (`ARCHITECTURE.md`).

## 2. What I learned from my audience

**User test 1, the radio cut:** narration, subtitles and placeholder music on a black screen. Three close friends, shown it without explanation:
- "That is deep."
- "I will from now on, for sure."
- "That is the problem with this generation."

The second reaction is the intent landing on sound alone. The third told me the story reads as a shared habit, not one family's, which is what a composite story should do.

**User test 2, the final film:** two viewers. Both called it eye-opening, and both made the same point: the "tomorrow" is the mistake.

**What changed because of the tests: honestly, nothing.** No one was confused, and the intent came through both times. The changes in the film came from my own reviews between the tests:
- **The hospital shot:** I asked for shot 6 to show the father in a hospital bed. Without him there, you can't tell what happened.
- **The Amharic:** I rewrote four of the Gemini-drafted lines into more natural speech (E7). For example, the son's first promise became an invitation to coffee, which ties the promise to the ceremony.
- **Two closing lines cut** to fit the real voice (E6).

**What I would do differently:**
- **Ask specific questions:** e.g. "Do the pictures alone make the fall and the hospital clear?" and "Does the gold in the last act read as the turn?"
- **Reach the rubric's three viewers for test 2**, which I didn't on the deadline day.
- **Lesson:** friendly viewers who like it tell you the intent landed, but not what to fix.

## 3. The hardest problem and how I solved it

**Getting moving video on a free GPU** (`FAILURES.md` F10, `EXPERIMENTS.md` E12).

Three shots (the pour, the jebena falling, the hand-hold) were planned as Wan 2.2 TI2V-5B image-to-video clips, run as Kaggle notebooks on a free Tesla T4 (14.5 GB).

1. **Attempt 1** loaded the model and then ran out of GPU memory inside the transformer (`CUDA out of memory`) on the first clip. The memory was never freed, so the other two clips failed instantly.
2. **Attempt 2** streamed the transformer onto the GPU layer by layer ("group offloading"), and cut clips from 121 to 81 frames. The GPU now fit, but the machine killed the job (`Killed`), because the pinned copies of the model filled the session's ~29 GB of RAM.
3. **Attempt 3:** I asked whether we could do it with "less than the 25 GB", and that question led to the fix. The 25 GB is three parts, and the 11 GB text encoder is only needed for a second, to read the prompt. So the notebook now encodes all three motion prompts first, frees the text encoder, and only then loads the video model. All three clips came back, about 15 minutes of T4 time each.

**What made it survivable:**
- **The pan-shot fallback:** every moving shot also has a pan shot, so after each failure the film still rendered, with the reason logged as a `fallback` line (ADR 0001).
- **Kaggle-job handling,** added along the way:
  - an interrupted run resumes the job it already pushed, instead of losing its place in the queue
  - a job that failed is never resent with identical inputs, so `make film` can't accidentally burn GPU hours

**A close second: the click at every line** (`FAILURES.md` F11). Every narration line clicked at its start and end. I first misread the end of each clip as two bursts of noise and trimmed them, and the start clicks stayed. The real cause was in the numbers: the first samples were 18770 and 17990, the bytes `RIFF`. Gemini TTS returns a complete WAV file (header, speech, then a C2PA content-credentials block), and the adapter had wrapped the whole file in a second WAV. Saving Gemini's file as-is removed every click and keeps the AI-provenance credentials intact.

## 4. The suggested practices: one that helped, one that didn't

**Helped, and beat my instinct: "time the narration first; test a radio cut before pictures"** (`docs/06-tips.md`).
- **My instinct** was to start with images.
- **What happened:** the real Amharic voice turned out much slower than the planned 2.5 words per second. The timing check found 7 overlaps in the closing passage (closing-06 alone overran the next line by 1.97 s), and the closing needed about 43 s of speech in about 37 s of room (E6).
- **The fix cost no model calls:** I cut two lines, shortened two narration-free shots and retimed the last act from the measured audio. If the pictures had come first, the shot lengths would have been wrong and I'd have regenerated them.
- **A bonus:** the radio cut was also user test 1.

**Did not work as written: "lock the look first: a character sheet, and generate every keyframe against it"** (`docs/06-tips.md`).
- **What I did:** I made a character sheet (father, son, coffee corner) and passed the sheet images as FLUX.2 klein reference images, as suggested.
- **With one reference, it worked:** the father was the same in every shot (E2).
- **With two or three references, the model stopped composing scenes and pasted the reference figures:** the son wearing the father's shawl, two fathers in one shot, the son alone on a white background where the hospital should be (E3).
- **The fix:** each shot names only its main character's reference, and shot 10 uses none. That shot composed correctly but lost likeness: the father appears in a blue shirt.
- **Lesson:** "against the sheet" has to mean one reference per shot on this model, not all of them.

## 5. Ceiling work

I did not complete one of the listed ceiling projects: no second language, no benchmark against a frontier model. What I did beyond the floor, and what it taught me:
- **Provenance in Gemini TTS output (F11):** Gemini's speech carries a C2PA content-credentials block inside the WAV. Handling the file as raw sound both breaks the audio and throws the credentials away. The pipeline now keeps them byte-for-byte in the narration files. `ETHICS.md` notes honestly that mixing into the MP4's audio track doesn't carry the block, which is one more reason the film ends with an AI card and is posted with the AI label on.
- **A recipe for Wan 2.2 TI2V-5B on a free T4 (F10):** encode prompts, free the 11 GB text encoder, then generate with model CPU offload at 81 frames. That's documented, with the two failed approaches and why they failed, for anyone else on Kaggle's free tier.
- **Reusable Kaggle tooling:** `make gpu` pushes a notebook template with the job embedded, polls it, downloads the results, resumes interrupted runs, and refuses to resend a job that already failed. Each item's GPU time is logged and summed by `make costs`.
- **Measured Amharic TTS behaviour:**
  - **Prompt layout:** a one-line style prefix made a 3-word line 11.8 s long, and a "director's notes" layout brought it to 2.7 s (E1).
  - **Not deterministic by seed:** the same seed gave 2.68 s once and 3.11 s another time.
  - **Speaking rate:** the real voice runs well under the 2.5 words per second the brief assumes (E6).

## 6. What I would build next

1. **Better moving shots:** the clips are 3.4 s at 480p, so shot 11 moves for about 3 seconds and then holds still for about 10. Next: chain two or three clips (each starting from the last frame of the previous one), and render at 720p on a GPU with 24 GB or more.
2. **A proper user test:** three or more viewers from the audience, with specific questions, and a storyboard change made from what they say.
3. **The film in Afaan Oromo or Tigrinya** as well, recording exactly where Gemini TTS fails in each language.
4. **Two-pass loudness normalisation.** Single-pass measured -15.0 LUFS on the pre-score mix and -14.2 with the score, against a -14 target.
5. **A small tool for my family:** a relative tells a story, and the pipeline drafts the storyboard and returns a film.

## Evidence

| Topic | Where |
|---|---|
| Audience, intent, both user tests | `DESIGN.md` |
| 12 experiments | `EXPERIMENTS.md` |
| 11 failures, plus what moved from the brief | `FAILURES.md` |
| Every model call, retry, cache hit and fallback | `runs.jsonl`; `make costs` summarises it |
| Cost: $0 on free tiers, about $0.11 at list price, under 2 Kaggle GPU hours | `COSTS.md` |
| Consent (composite story), licences, labelling | `ETHICS.md` |
| Decisions | `docs/adr/` |

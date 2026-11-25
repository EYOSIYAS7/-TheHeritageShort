# 06 Appendix B: Tips and Tricks (none required; take what helps)

Sources in `08-pro-workflow.md`. Slack is a good place to ask a colleague to review your work.

## Before you generate anything
- Write the story in 3–5 sentences first, one picture per beat. Unclear story + more generation = more inconsistent material.
- Settle on one page: who watches, where they watch (usually phone, vertical), the one feeling at the end.
- Every minute of planning saves several in editing. A planned storyboard is cheap to change; a generated shot is not.
- Time the narration first. Professionals cut picture to the voice track, so the radio cut tells how long each shot needs. Rough guide: speech ~2–2.5 words/s, so 60–90 s = roughly 130–220 words. Your language/voice will differ: measure with your TTS output.
- A cheap prototype is the best investment. A radio cut can be tested in minutes; a friend's reaction beats another round of image prompts.

## Storyboard and shots
- 8–12 shots over 60–90 s = ~6–8 s/shot. Image-to-video clips are usually ~5 s, so some shots hold on a still or use a slow pan.
- One idea and one movement per shot. If you can't say in a sentence why a shot exists, the film may not need it.
- Vary shot size: wide to show where, medium for what happens, close-ups for feeling.
- Fewer characters = fewer consistency problems. One person and one place is easiest.
- Put the reason for each shot in the storyboard (useful for you, reviewers, interview).

## Keyframes and consistency
- Lock the look first: character sheet, style block, one approved reference image; generate every shot against them.
- Generate several options per character/place, then pick one (cheap for images). One documented 70-second production generated four options per reference and kept two characters consistent across every scene without training anything.
- Image-to-video is much more consistent than text-to-video (composition, light, subject fixed in the image).
- Keep the style block and character description attached to every prompt; drift mostly comes from re-describing things differently.
- Text inside generated images (signs, titles) often garbles: add words in code as subtitles/titles.
- Check faces and hands on every keyframe before spending GPU time animating it.
- Fixed seed to compare two prompts fairly; varied seed to explore.

## Moving shots
- If the image already shows subject and place, the video prompt needs only motion and camera. Example: "the woman slowly turns her head, the camera pushes in gently, soft wind in the grass".
- Wan prompt formula: subject, action, environment, camera, light, style, motion, quality. For image-to-video drop most; keep motion and camera.
- Contradictory camera instructions can break a clip. Asking for a fixed camera keeps it still.
- Slow gentle motion beats fast complex action; short clips stay more consistent than long. Longer scene = several short clips cut together.
- If a clip is ~80% right, trim it or edit around the flaw rather than regenerate (regeneration can throw away the good parts).
- Artifacts (flicker, morphing, drifting faces) usually improve with a simpler prompt, a better keyframe, or less motion.
- Many clips have a weak first/last half second; trim in the edit for free.
- Slow pan-and-zoom over a still (Ken Burns) is a respectable shot and a fallback when a clip fails. Slow, varied movement between consecutive shots avoids repetition.
- Draft at 480p, batch jobs, let them run while you do something else. Logging latency and GPU minutes as you go gives COSTS.md almost for free.

## Narration
- Write for the ear: short sentences, concrete images, no tongue-twisters. Read aloud to find most problems.
- Generate narration line by line, one file per shot: cheap re-takes, easy timing adjustment.
- Names and places are where TTS goes wrong most. A native speaker (relative or Slack colleague) listening once catches errors you can't hear.
- A short style instruction (calm, warm, unhurried) usually improves a voice more than switching voices.
- If a model handles your language badly, that is useful evidence: note in FAILURES.md where it failed (exactly what the troubleshooting criterion looks for).
- Subtitles: max 2 lines, ~40 characters per line, inside the vertical safe area.

## Music
- Composers watch the film and decide where music begins, builds, ends. Write a tiny cue list with timecodes BEFORE generating.
- Under narration: gentle texture, no strong lead melody. A theme that returns near the end gives shape.
- ACE-Step: the caption matters most. Combine style, mood, instruments, texture, era (better than one word). Less text = more surprise; more text = more control.
- Tempo and key go in the metadata fields, not the caption. Slow ballad at fast tempo is a common contradiction.
- Write "instrumental" or use the instrumental tag to keep vocals out of a score.
- 30–60 s is the most stable length. For longer, generate in sections and join.
- Generate a batch of candidates, listen at low volume under the narration, note why you chose one.

## Mixing and export
- Voice (narration) is the spine; music under it; effects punctuate.
- Soundtrack has four layers: dialogue, effects, ambience, music. Very quiet ambience or a few small effects can make AI pictures feel more real; optional.
- Sources from different tools come out at different levels: bring each to similar loudness before mixing, so balance choices are creative rather than repairs.
- FFmpeg ducking: `sidechaincompress`. Starting point: threshold 0.02, ratio 6, attack 300 ms, release 1500 ms. Tune by ear.
- Normalise final export to ~-14 LUFS, true peak near -1 dB (suits YouTube and most social). Louder gives no benefit (platforms turn it down). FFmpeg `loudnorm`; two-pass is more accurate.
- Balance layers first, then set final loudness.
- Check on phone speaker and headphones before export.
- Compose keyframes with the subject in the middle of the frame: easier to produce vertical and horizontal versions from the same material.
- MP4 with H.264 video + AAC audio plays almost everywhere. Constant frame rate; 2–3 s end card.

## Working habits
- Approval step between stages: story -> radio cut -> stills -> clips -> edit. Move on only when the previous stage feels right.
- Prompts and seeds in the storyboard, not hidden in code: reproducible and easy to explain.
- Limit attempts per shot (e.g. 3) before using a fallback.
- Commit small and often; keep secrets out of repo; write a short note whenever something breaks.
- Show a rough cut early; Slack for review, native-speaker listen, or a second opinion on a shot.

## Common mistakes -> what tends to work better
- Generating clips before story and narration timing settled -> settle story and radio cut first; narration sets shot lengths.
- Making the character sheet after the shots -> fix character and style first; generate every keyframe against them.
- Re-describing the subject in an image-to-video prompt -> describe only motion and camera.
- Long clips with lots of action -> short clips with one gentle movement, cut together.
- Words inside generated images -> add titles/text in code.
- Music too busy/loud under voice -> quiet texture, duck under narration.
- Mixing sources at very different levels -> bring each to similar loudness first, then mix.
- Exporting louder than platform target -> aim ~-14 LUFS, true peaks below -1 dB.
- Changing several things between two runs -> change one thing, keep seed fixed, note result in EXPERIMENTS.md.
- Not recording seeds and parameters -> log every call so any shot can be reproduced/explained.
- Spending GPU quota on high-res drafts -> draft low, batch, finish only chosen shots.
- Testing only with yourself -> show the cut to people like your audience.
- Leaving consent and licences until the end -> record consent before generating anything of a real person; note licences as you pick models.

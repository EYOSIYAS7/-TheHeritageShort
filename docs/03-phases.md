# 03 The Path: 3 phases, each ends in a playable checkpoint

If you fall behind, the checkpoint points to the next concrete thing to finish. Nobody should end with nothing: if video generation fails, animate keyframes with a slow pan-and-zoom (Ken Burns) in FFmpeg; a narrated, scored, subtitled sequence of stills is still a film. Cohort Slack is a good place to ask for a review or second opinion at any checkpoint.

## Phase 1: story and radio cut
1. Set up: Gemini API key, Cloudflare account, phone-verified Kaggle account, Antigravity CLI or OpenCode. Write a smoke test that calls each provider once and logs latency to `runs.jsonl` to learn early what works.
2. Choose story and audience. Talk to the person whose story it is (improves the film). If a real person's face, likeness or voice will appear, record their consent in `ETHICS.md` BEFORE generating anything of them.
3. Write audience and intent in `DESIGN.md`: who watches, where, what they should feel/understand at the end.
4. Write a JSON Schema for the storyboard; have the agent draft `storyboard.json` against it: 8–12 shots, durations, image and motion prompts, narration lines, music cues. Validate in code.
5. Generate narration with Gemini TTS; assemble a radio cut (narration over placeholder music on a black screen). Play to >=3 people from the audience (in person or Slack). Write in `DESIGN.md` what they said and what you will change.

**Checkpoint 1**: radio cut plays end to end; `DESIGN.md` records the first user test.

## Phase 2: pictures and music
1. Generate a character and style reference sheet FIRST, then the keyframe for every shot, conditioned on it. Iterate until the main character is recognisably the same across shots.
2. Run Wan 2.2 image-to-video on Kaggle for as many shots as quota allows. Cache stage outputs by hash of inputs so a re-run regenerates only changed shots.
3. Generate a few ACE-Step candidates for the score (three is good), choose one, write down why.
4. Log every call. Record each experiment as hypothesis/change/result in `EXPERIMENTS.md`, each failure in `FAILURES.md`.

**Checkpoint 2**: rough cut with a picture for every shot and the chosen score.

## Phase 3: edit, release, explanation
1. Assembly, all in code and from the storyboard: cut to the music, duck score under narration, burn in subtitles, normalise loudness, add end card, export both aspect ratios.
2. Show near-final cut to >=3 people from the audience; record in `DESIGN.md` what they said and what changed. This is user test #2.
3. Write README, ARCHITECTURE.md, COSTS.md. Ensure `make film` (or equivalent) runs the whole pipeline from a clean clone. Then write the report (PDF, Word, or link).
4. Post the film with the platform's AI label ON. Write the post yourself: the story, why it matters to you, one thing you learned building it.
5. Record walkthrough, max 5 min: the architecture, one hard decision, one shot regenerated live. Live part: change one keyframe prompt or one narration line in `storyboard.json`, rerun the pipeline, show that ONLY that shot regenerates. No need to rerun Wan 2.2 on camera; you may pause recording while the job runs; showing logs with a single new model call counts as evidence.

**Checkpoint 3**: film is public, repo runs end to end, walkthrough recorded, report written. Then submit both assignments by Thu 26 Nov 23:59 EAT.

## Suggested practices (you may do differently, but the report must cover them)
- JSON contract between stages
- Reference sheet before keyframes
- Log every call
- Let the agent write stage scripts while you design and review
- The report asks for ONE case where a suggested practice beat your instinct and ONE where it did not: note these as you go.

# 01 Brief: AI-Content Generation: The Heritage Short

## Scenario
- Over 3 days, make a 60–90 s short film about a person, place or story that matters to you and your family, narrated in your own language, with an original score.
- Not made by hand. Build a small studio in code: a pipeline turning a written storyboard into keyframes, moving shots, music, narration and a finished edit. A coding agent writes most of the code under your direction.
- Deadline: both submissions due Thursday 26 November, 23:59 East Africa Time.
- Example stories: grandmother walking to the market in Dessie; father learning to repair radios; the proverb a mother repeats when things go wrong.
- Context: two years ago this took a crew; a year ago it took paid access to a handful of frontier models; now it takes a developer who can orchestrate many models, measure what they do, and keep going when they fail.
- The film is what family/followers see. The pipeline is what graders look at. A stranger must be able to clone the repo, run one command, and regenerate the film from its storyboard.

## Why this challenge
- Value of work has moved from delivery to the precise theory you hold in your head. One image/clip is trivial now.
- Still hard and valuable: deciding what the work is for; breaking it into stages with clear contracts; keeping a character consistent across twelve shots; knowing each model's cost and time; recovering when a quota runs out at the worst moment. This is forward-deployed-engineer work.
- Tool changes over the past year (itself part of the lesson):
  - Sora app and API shut down; Google retired Veo 3.1 previews from the Gemini API in favour of the Gemini Omni Flash video family.
  - Frontier image/video/music models (Nano Banana, Omni Flash, Lyria 3.5) moved behind paid billing, which most participants cannot attach from Ethiopia.
  - Open-weight models closed much of the gap: Wan 2.2 makes video on a free GPU; ACE-Step 1.5 makes full songs with lyrics in under 4 GB memory.
  - Speech went the other way: Gemini 3.8 Flash TTS is free on the API, 130+ languages incl. Amharic.
  - Free coding agents changed hands: Gemini CLI stopped serving free personal accounts; Antigravity CLI and OpenCode now fill that role.
- Surviving skill: orchestration with judgement. Any single model is replaced within months. Compose from free hosted APIs, open weights on borrowed GPUs and programmatic editing; measure and document every choice.
- Expect some of the brief to be out of date. When a tool has moved, find what replaced it and tell them in the failure journal (FAILURES.md).

## Win-win framing / what evaluators look for
- More strong applicants than places; some won't join this round due to capacity, not ability.
- If you join: start with a working pipeline and habits of logging, measuring, iterating.
- If not: you keep a family film, a public repo showing a multi-model pipeline, measured evidence of how current open/frontier models behave, and an interview story about what you built and what broke.
- Looking for (not the most beautiful film):
  - Curiosity: do you go further than suggested?
  - Grit: do you keep going when GPU queue, quota or model fails you?
  - Open-mindedness: do you try suggested practices and test them honestly rather than fall back on what you know?

## What you build: a film and the pipeline that makes it
Film:
- 60–90 s, exported vertical 9:16 AND horizontal 16:9
- Narration in a language of your choice
- English subtitles
- Original score, ducked under the voice
- Visible end card saying it was made with AI

Pipeline:
- A repo where `storyboard.json` is the contract between every stage; each stage is a script that reads it and writes its output.
- Five stages around that one contract: keyframes, moving shots, music, narration, assembly.
- Change one shot and regenerate only that shot.
- Appendix A (glossary), B (tips), C (pro workflow) are in docs 07, 06, 08.

## Three competencies tested
1. **Software development**: clear stage boundaries; validated schema; retries and caching so re-run regenerates only what changed; secrets out of repo; a log line for every model call (model, parameters, seed, latency, cost) in `runs.jsonl`.
2. **Design thinking**: decide who the film is for and what they should feel/understand at the end BEFORE generating anything. Cheap prototype (narration-only cut) shown to >=3 people from the intended audience; what they say can change the storyboard. Then test the near-final cut with the audience again. Every shot should have a stateable reason. Both tests and what they changed go in `DESIGN.md`. Colleagues on Slack are a good audience for an early cut.
3. **Communication**: README + written report a stranger can follow; short walkthrough video (explain pipeline, regenerate one shot live); public post telling the story behind the film; an interview about your choices.

Two assignments grade them: #1 reads repo + report; #2 is manual review of film, walkthrough video, public post.

## Repo shape (improve freely)
```
README.md          one-command run of whole pipeline, what it does, what it costs
storyboard.json    the contract: shots, durations, prompts, references, narration, music cues
schema/            JSON Schema for the storyboard, validated before every run
pipeline/          one script per stage: script, keyframes, shots, music, narration, assemble
runs.jsonl         one line per model call
outputs/           generated images, audio and video, kept so the run can be inspected
DESIGN.md          audience, intent, the user tests and what changed because of them
ARCHITECTURE.md    stages, contracts, caching, failure handling
EXPERIMENTS.md     hypothesis -> change -> result entries (about ten is a good target)
FAILURES.md        what broke, what you tried, what fixed it
COSTS.md           measured latency and GPU minutes per stage, list-price equivalent
ETHICS.md          consent record, licences of every model and output, labelling plan
```
- The repo is read as code, text, logs and documents. Audio/video/image files are NOT opened when grading the codebase. Keep evidence for every claim in writing (logs, DESIGN.md, EXPERIMENTS.md, FAILURES.md, other files). The film is judged in assignment 2 via submitted links.
- The report is a separate document submitted alongside the repo link (contents in `04-submission-grading.md`).

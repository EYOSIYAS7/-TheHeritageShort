# Heritage Short: AI-Content Generation (IO Academy challenge, B2W0)

Goal: a 60–90 s short film about a person/place/story that matters to the author and family, plus a code pipeline that regenerates it from `storyboard.json` with one command. Pipeline = graded as code/text/logs/docs. Film = graded manually. Process weighs as much as the film.

**Deadline: Thu 26 Nov 2026, 23:59 East Africa Time. Both assignments.**

## Hard rules (never violate)
- `storyboard.json` is the single contract between all stages. Validate against `schema/` JSON Schema before every run.
- Stages: keyframes, moving shots (video), music, narration, assembly (+ script/storyboard drafting). Each stage = one script that reads the storyboard and writes outputs.
- Cache by hash of stage inputs; re-run regenerates only changed shots. Retries on failure.
- Log EVERY model call to `runs.jsonl` (model, parameters, seed, latency, cost). One line per call.
- No secrets in the repo.
- One documented command (`make film` or equivalent) runs the whole pipeline from a clean clone.
- Prompts and seeds live in storyboard.json, not hidden in code.
- Consent gate: if a real person appears or is voiced and there is no consent record in `ETHICS.md`, the film scores ZERO. Record consent BEFORE generating anything of them.
- Film deliverables: 60–90 s; 9:16 AND 16:9 MP4; narration in a chosen language; English subtitles (burned in); original score ducked under voice; visible end card saying it was made with AI.
- Post publicly with the platform AI label ON. Keep SynthID/C2PA watermarks and metadata intact.
- Repo graders do not open audio/video/image files: put evidence in text (logs, DESIGN.md, EXPERIMENTS.md, FAILURES.md).
- Some brief details may be outdated; if a tool moved, find the replacement and record it in FAILURES.md.

## Docs map (open only what the task needs)
- `docs/01-brief.md`: scenario, rationale, what to build, competencies, repo layout
- `docs/02-stack.md`: free stack table, model descriptions, constraints, GPU/quota notes
- `docs/03-phases.md`: Phase 1/2/3 steps, checkpoints, fallbacks
- `docs/04-submission-grading.md`: both assignments, rubrics with points, interview, gate
- `docs/05-ethics-ceiling.md`: consent/labelling/licences/style/private data; optional "raise the ceiling" ideas
- `docs/06-tips.md`: Appendix B practical tips and common-mistakes list
- `docs/07-glossary.md`: Appendix A (media-model basics, film/music/design/gen-AI terms)
- `docs/08-pro-workflow.md`: Appendix C (how professionals work, mapped to pipeline) + reading list URLs

## Repo target layout
```
README.md          one-command run, what it does, what it costs
storyboard.json    contract: shots, durations, prompts, references, narration, music cues
schema/            JSON Schema for storyboard, validated before every run
pipeline/          one script per stage: script, keyframes, shots, music, narration, assemble
runs.jsonl         one line per model call
outputs/           generated images/audio/video, kept for inspection
DESIGN.md          audience, intent, user tests and what changed
ARCHITECTURE.md    stages, contracts, caching, failure handling
EXPERIMENTS.md     hypothesis -> change -> result (~10 entries)
FAILURES.md        what broke, what was tried, what fixed it
COSTS.md           measured latency + GPU minutes per stage, list-price equivalent
ETHICS.md          consent record, licences of every model/output, labelling plan
```

## Agent skills

### Issue tracker

Issues live as local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), recorded as a `Status:` line in each issue file. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `GLOSSARY.md` + `docs/adr/`. See `docs/agents/domain.md`.

# 04 Submission, Grading, Interview

Both assignments due Thu 26 Nov, 23:59 East Africa Time. Each has its own submission form.

## Assignment 1: "B2W0: AI-Content Generation - Codebase and Report"
Every submission is followed by an AI interview. Submit:
1. Link to public GitHub repo with the files in `01-brief.md` and one documented command that runs the pipeline end to end.
2. Report as PDF/Word upload or a link. Contents:
   - what you set out to make and for whom
   - what you learned from your audience
   - the hardest problem and how you solved it
   - the suggested practice that helped and the one that did not
   - any ceiling work done
   - what you would build next

Grading reads code, text, logs and documents. Audio/video/image files may sit in the repo but are not opened.

## Assignment 2: "B2W0: AI-Content Generation - Film, Walkthrough and Post (manual grade)"
Graded by hand by the team. Submit on tenx:
- Main: link to vertical (9:16) MP4
- Attachments (links): horizontal (16:9) MP4; walkthrough video (<=5 min); public post (or screenshot if you chose not to post)
- Every link must open without a login, or share access with graders.
- No separate interview for assignment 2; the assignment-1 interview covers the whole project, film included.

## Interview (after assignment 1, AI interviewer)
Expect: why the pipeline is shaped as it is; walk through an entry in your experiment log; describe a failure and what you did; what your audience said and what changed. It checks the work is yours and understood. Prepare by rereading your own logs and notes.

## Assessment overview
Two parts, each /100. Process weighs as heavily as the film: logs are where curiosity, grit and open-mindedness become visible. Film/walkthrough/post can't be graded automatically so are manual.

## Assignment 1 rubric (/100)
- **Software engineering and reproducibility (20)**: clear stage boundaries around a validated `storyboard.json`; caching so re-runs regenerate only what changed; retries; no secrets committed; `runs.jsonl` complete; one documented command runs the pipeline end to end from a clean clone, as README, code and logs show.
- **Documentation (10)**: README a stranger can follow; ARCHITECTURE.md explains contracts, caching and failure handling.
- **Design thinking and audience (10)**: audience and intent stated BEFORE generating; written notes of two user tests (radio cut and near-final cut), each with >=3 people from the audience; storyboard visibly changed by what they said; every shot has a stated reason.
- **Experimentation and iteration (10)**: >=10 logged experiments with hypotheses; comparisons backed by evidence in text or logs; reasons for each choice.
- **Troubleshooting and persistence (10)**: FAILURES.md shows real blockers (quota, memory, consistency, language), what you tried, how resolved or worked around.
- **Measurement (5)**: measured latency and GPU minutes per stage; list-price cost equivalent; frontier comparison where you had access.
- **Consent, labelling and licences (5)**: consent recorded for every real person shown or voiced; licences checked; labelling plan clear.
- **Report: reflection and learning from audience (10)**: specific, candid account tied to repo evidence: what audience said, what changed, hardest problem and how solved.
- **Report: suggested practices tested honestly (10)**: one practice that beat your instinct and one that did not, each with evidence.
- **Report: curiosity beyond the floor (10)**: ceiling work that produced insight, per your written account and repo: extra language tested, benchmark, tool others can use, an idea of your own.

## Assignment 2 rubric (/100)
- **The film (50)**: 60–90 s in both aspect ratios; clear narration, score ducked, accurate subtitles; consistent characters and style; the AI end card; a story that lands for the audience you chose.
- **Walkthrough video (30)**: <=5 min; architecture and one hard decision explained clearly; one keyframe prompt or narration line changed in `storyboard.json`, pipeline rerun, only that shot regenerated, shown on screen (pausing while job runs and showing logs are fine).
- **Public post (20)**: public and written by you: the story, why it matters to you, one thing you learned; the platform's AI label switched on.

**GATE**: if a real person appears or is voiced without a consent record in `ETHICS.md`, the film scores zero, however good.

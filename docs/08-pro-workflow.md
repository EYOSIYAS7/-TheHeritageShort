# 08 Appendix C: How Professionals Do It (a map, not a standard)

## Film stages -> pipeline
Five stages: development, pre-production, production, post-production, distribution.
- Development: idea shaped (story, first script, audience). Pipeline: choose story + audience; write intent in `DESIGN.md`.
- Pre-production: everything planned before expensive work (script locked, storyboard, look, schedule, consent). Pipeline: schema, `storyboard.json`, reference sheet, `ETHICS.md`.
- Production: raw material made (filming, or for animation creating pictures). Pipeline: keyframes and moving shots.
- Post-production: editing, sound design, music, colour, subtitles, mix, export. Pipeline: narration, score, assembly, ducking, loudness, end card, exports.
- Distribution: release and promotion. Pipeline: public post and walkthrough.
- Film-school saying: every minute in pre-production saves ~3 in post. Reason professionals storyboard before shooting and why the pipeline starts with a plan.

## Animated film, layer by layer (rough to fine; test story at each level before spending on the next)
1. Story and script: idea written down and tested on paper.
2. Storyboard: each shot drawn as a still; story problems found here, cheap to fix.
3. Animatic / story reel: storyboard stills on a timeline with rough dialogue and music to test pacing; last cheap check; finished scenes replace stills one by one.
4. Layout: camera position, framing, staging of each shot fixed.
5. Production: backgrounds, characters, effects made, usually as separate layers so each can change alone (background, midground, character, foreground, effects such as dust/light).
6. Lighting and rendering, then compositing (layers combined, common look).
7. Sound and music, colour grading, delivery in needed formats.
- Your pipeline mirrors this in miniature: storyboard = plan; radio cut = audio animatic; keyframes = flattened layer; moving shots = production; FFmpeg assembly = compositing + delivery.

## Soundtrack, layer by layer
Four layers: dialogue, sound effects, backgrounds/ambience, music. Foley belongs to effects.
1. Dialogue/narration edited and cleaned first (audience must always understand it).
2. Ambience next: continuous sound per place, hides edits.
3. Effects and Foley where they help; small sounds often do more than big ones.
4. Music last: shapes feeling; lowered or removed where voice needs space.
5. Re-recording mixer balances layers, usually in stems (dialogue, effects, music). EQ gives each sound its own space; sidechain compression ducks music/effects under dialogue.
6. Loudness target for the destination applied at the very end; check on small speakers and headphones.
- Your version: same recipe, fewer layers: narration, score, optional ambience, ducking filter, loudness pass.

## Film score, step by step
1. Composer watches the film (first impressions of rhythm, tone, feeling matter).
2. Spotting session with director, composer, often editor: scene by scene, where each cue starts/stops and its emotional job. Output: list of cues with timecodes (spotting notes / music summary).
3. Editor often cuts to a temp track (borrowed music) giving a target feeling; can trap a film into imitating something existing.
4. Composer sketches themes (often tied to characters/ideas), builds each cue against picture.
5. Director responds, composer revises, final cues recorded/produced, delivered as stems.
6. Music mixed with dialogue and effects.
- With ACE-Step: a short spotting note in your words becomes the caption; the candidate batch is the sketchbook; your ear is the director.

## Design thinking applied to the film
- Empathise: talk to the person whose story it is and to the people who will watch.
- Define: write a sentence on who the film is for and what they should feel.
- Ideate: sketch several ways to tell the story before choosing.
- Prototype: radio cut, then rough cut with stills.
- Test: show people like your audience, write down what they said, change the storyboard.
- Stages are not a straight line; teams loop back often.

## Professional step -> pipeline stage -> where in repo
- Treatment and script -> story and narration -> `DESIGN.md`, narration lines in `storyboard.json`
- Storyboard -> shot plan -> `storyboard.json` and its schema
- Look development, character sheet -> reference sheet -> reference images and the style block
- Animatic, story reel -> radio cut, rough cut -> `DESIGN.md` test notes
- Production -> keyframes and moving shots -> `pipeline/` stages and `runs.jsonl`
- Spotting -> music cues -> music cues in `storyboard.json`
- Scoring -> score candidates and choice -> `EXPERIMENTS.md` entry
- Sound mix -> ducking and loudness -> assembly stage
- Compositing, grade, titles -> assembly -> assembly stage
- Delivery -> both aspect ratios and end card -> `outputs/` and the second assignment

## Reading list
(URLs rejoined from line-wrapped PDF text; verify before relying on them.)

Film process and storyboards
- StudioBinder, how to make a short film, pre-production process: https://studiobinder.com/blog/how-to-make-short-film-pre-production-process
- LA Film School, five stages of indie film production: https://www.lafilm.edu/blog/5-stages-of-indie-film-production/
- StudioBinder, what is an animatic: https://www.studiobinder.com/blog/what-is-an-animatic-definition/
- CG Spectrum, guide to the animation pipeline: https://cgspectrum.com/blog/guide-to-animation-pipeline
- B&H, camera shot types explained: https://www.bhphotovideo.com/explora/video/tips-and-solutions/filmmaking-101-camera-shot-types
- MasterClass, glossary of film terms: https://www.masterclass.com/articles/film-terms-guide

Sound, music and mixing
- USC, what post-production sound is: https://animation.usc.edu/student-portal/sound-resources/post-sound
- BFI sound design and mixing handbook (PDF): https://eprints.bournemouth.ac.uk/36627/1/BFI%20Sound%20Design%20%26%20Mixing%20Handbook.pdf
- Film Independent, how a composer creates a score: https://www.filmindependent.org/blog/know-score-composing-process-work/
- B&H, composing for film, before you score: https://www.bhphotovideo.com/explora/node/96206
- MusicRadar, writing music to picture: https://www.musicradar.com/news/soundtracking-secrets-writing-to-picture
- Hackernoon, mastering AI-generated film audio for YouTube: https://hackernoon.com/how-to-master-ai-generated-film-audio-for-youtube
- EBU R128 loudness recommendation (technical): https://tech.ebu.ch/docs/tech/tech3343.pdf

FFmpeg
- FFmpeg cookbook, audio ducking with sidechaincompress: https://ffmpegcookbook.pages.dev/en/articles/audio-ducking/
- Ken Burns effect with FFmpeg: https://el-tramo.be/blog/ken-burns-ffmpeg/
- FFmpeg filter documentation: https://www.ffmpeg.org/ffmpeg-all.html

Design thinking
- Interaction Design Foundation, five stages of design thinking: https://ixdf.org/literature/article/5-stages-in-the-design-thinking-process

The models
- ACE-Step 1.5 technical report: https://arxiv.org/abs/2602.00744
- ACE-Step 1.5 code and guide: https://github.com/ACE-Step/ACE-Step-1.5
- Wan 2.2 code: https://github.com/Wan-Video/Wan2.2
- Wan 2.2 TI2V-5B model card: https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B
- Wan video prompt guide (Alibaba Cloud): https://www.alibabacloud.com/help/en/model-studio/text-to-video-prompt
- FLUX.2 klein announcement: https://bfl.ai/blog/flux2-klein-towards-interactive-visual-intelligence
- Gemini API, text-to-speech: https://ai.google.dev/gemini-api/docs/speech-generation

AI video practice
- Runway, tips for realistic AI videos: https://runwayml.com/resources/tips-make-realistic-ai-videos
- Invideo, consistent shots across a short film: https://invideo.io/faq/how-do-you-create-consistent-ai-video-shots-for-a-short/

# 02 Stack (zero cost, no payment card needed from Ethiopia)

Free tiers change often: check each limit at start and record what you actually found in `COSTS.md`.

## Stage -> model -> where it runs -> free access
- **Coding agent**: Gemini 3.8 Flash and the free Claude models, via Antigravity CLI (`agy`) or OpenCode with its free models. Weekly quota; read each free model's data terms.
- **Script / storyboard / translation**: Gemini 3.8 Flash (Flash-Lite for bulk calls), Gemini API, key from Google AI Studio. Free tier, Ethiopia supported.
- **Narration**: Gemini 3.8 Flash TTS, Gemini API. Free tier, 130+ languages incl. Amharic.
- **Keyframes**: FLUX.2 klein or FLUX.1 schnell, Cloudflare Workers AI. Daily free allowance, roughly 50–170 images.
- **Moving shots**: Wan 2.2 TI2V-5B (image-to-video); HunyuanVideo 1.5 as alternative. Kaggle notebook (2x T4), Colab as backup. About 30 GPU hours/week on Kaggle, phone verification required.
- **Music and song**: ACE-Step 1.5, Kaggle or Colab. Open weights, outputs usable commercially.
- **Assembly**: FFmpeg; Remotion if animated titles wanted. Runs on your machine, free.
- **Showcase**: static page or Gradio Space on Hugging Face. Free.

Notes:
- Claude Code and Codex are paid and common professionally; free agents above are enough here.
- If a frontier lane opens for the cohort, capped access to Omni Flash, Nano Banana and Lyria 3.5 will be shared via an organisation key, to compare against open models.
- Binding constraint is GPU time and queueing, not money. A 5 s 720p Wan 2.2 clip takes several minutes on a strong consumer GPU, longer on a T4. Draft at 480p, batch jobs, measure.

## Model descriptions
**Gemini 3.8 Flash / Flash-Lite**: Google text models. Use for script, storyboard, translation. Flash-Lite is lighter for many small calls.

**Gemini TTS**: text to speech; returns audio. Steer with a plain-language style instruction (e.g. calm, warm, slow) and a named voice. Supports single and multiple speakers and a long language list. Check the current language list for yours and LISTEN to output in your language before relying on it; quality differs by language.

**FLUX.2 klein / FLUX.1 schnell** (Black Forest Labs image models; "klein" = German for small):
- Distilled klein models make an image in 4 steps, roughly 1–2 s on a recent consumer GPU; can also edit an image using reference images.
- 4B version: Apache 2.0. Larger 9B: non-commercial licence.
- FLUX.1 schnell: earlier model in same family, also distilled to very few steps.
- On Cloudflare Workers AI: called via API with a daily free allowance.

**Wan 2.2** (open video model family):
- TI2V-5B takes a prompt and optionally a start image; makes a short clip at 720p, 24 fps. Strong video compression lets it run on one consumer GPU (e.g. RTX 4090). Larger A14B versions use mixture of experts.
- Practical workflow: keyframe + prompt about motion and camera -> clip of a few seconds.
- On a Kaggle T4 much slower than a 4090: draft at lower resolution and batch.
- Licence: Apache 2.0.

**HunyuanVideo 1.5**: another open video model; alternative if Wan does not suit a shot.

**ACE-Step 1.5** (open music model):
- Describe music in a caption (style, mood, instruments, texture); optionally add lyrics, duration, tempo, key. Returns a full track, instrumental or with vocals.
- Two parts: optional language-model planner (structure, refines caption) + diffusion transformer that renders audio.
- Distilled to a handful of steps: seconds per track on a consumer GPU.
- Lyrics in 50+ languages; up to 8 candidates per batch; can edit existing music (e.g. repaint a section).
- MIT licence; trained on licensed, royalty-free and synthetic data. Outputs usable commercially.
- Every seed gives a different piece: use like a composer's sketchbook (generate a few, listen, choose one).

**FFmpeg**: CLI for cutting, joining, resizing, burning subtitles, mixing, ducking, loudness normalisation, Ken Burns zoom. Not AI; same inputs give same output, which suits the assembly stage.

**Remotion**: describe video as React components, render to MP4; handy for animated titles and end card.

**Kaggle / Colab**: hosted notebooks with free GPUs. Weekly quotas, sessions time out: write scripts that save outputs as they go.

**Cloudflare Workers AI**: hosted, call models by API. **Hugging Face**: hosts weights and small demos (Spaces).

**Antigravity CLI / OpenCode**: coding agents that write code from instructions in a terminal.

## Licence notes (also record in ETHICS.md)
- Wan 2.2: Apache 2.0
- ACE-Step 1.5: MIT; outputs commercially usable
- FLUX.2 klein 4B: Apache 2.0; 9B: non-commercial
- Other models carry their own terms; note licence of every model and output as you choose them.
- Free endpoints may train on what you send: keep private family details out.

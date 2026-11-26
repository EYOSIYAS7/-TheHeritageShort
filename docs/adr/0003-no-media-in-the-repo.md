# No media in the repo; text evidence only

Status: accepted 2026-11-26. Supersedes the "committed outputs" half of ADR 0002; its GPU fallbacks still apply.

Generated media is git-ignored: images, audio and video (`*.jpg`, `*.png`, `*.wav`, `*.mp4`, …). The repo holds code, text, logs and docs only. Text outputs stay committed: the cache manifest, the Amharic drafts (`outputs/script/*.json`), the subtitle files (`*.srt`) and `runs.jsonl`. The finished film (16:9 and 9:16 MP4) is submitted separately as the deliverable.

**Why:** graders read the repo as code, text and logs and never open media. Pushing the final MP4s (about 55 MB) over HTTPS failed. The author decided the repo should carry no media at all.

**Consequence:** a fresh clone no longer rebuilds the film with zero model calls, which ADR 0002 and ticket 08 had promised. The cache manifest still lists every generated file by input hash, but the files themselves aren't there. With keys in `.env`, `make film` on a clean clone regenerates the media, one logged call per item. Without keys:
- Keyframes become labelled placeholders.
- Narration stops with a message naming the missing `GEMINI_API_KEY`.

On the author's machine, where `outputs/` holds the media, re-runs remain all cache hits. Media committed before this decision stays in the git history; it was not rewritten.

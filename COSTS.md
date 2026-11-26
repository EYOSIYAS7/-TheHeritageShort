# Costs

Everything below is measured from `runs.jsonl` (2026-11-25 to 2026-11-26). Regenerate the table with `make costs`.

**Money spent: $0.** Every call ran on a free tier: Google AI Studio for Gemini, and Cloudflare Workers AI's free daily allowance. Logged `cost_usd` is 0 for that reason; the list-price equivalent is worked out below.

## Calls per stage

"Attempts" are requests that reached a provider, retries included; "cache hits" are items reused without a call. Latency is wall time per attempt as measured by the run log.

| Stage | Model | Attempts | OK | Retried | Failed | Cache hits | Skipped | Latency (s) | Mean per attempt (s) | Image list price ($) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| characters | `@cf/black-forest-labs/flux-2-klein-4b` | 4 | 4 | 0 | 0 | 17 | 0 | 59.4 | 14.8 | 0.0046 |
| keyframes | `@cf/black-forest-labs/flux-2-klein-4b` | 32 | 32 | 0 | 0 | 40 | 0 | 436.3 | 13.6 | 0.0871 |
| narration | `gemini-3.8-flash-tts` | 22 | 15 | 5 | 2 | 139 | 0 | 71.7 | 3.3 | - |
| narration | `placeholder-tone` | 27 | 27 | 0 | 0 | 25 | 0 | 0.7 | 0.0 | - |
| script | `gemini-3.5-flash` | 13 | 12 | 1 | 0 | 0 | 0 | 279.0 | 21.5 | - |
| script | `gemini-3.8-flash` | 36 | 0 | 24 | 12 | 0 | 0 | 261.4 | 7.3 | - |
| smoke | `@cf/black-forest-labs/flux-2-klein-4b` | 0 | 0 | 0 | 0 | 0 | 5 | 0.0 | - | - |
| smoke | `gemini-3.8-flash` | 16 | 2 | 11 | 3 | 0 | 0 | 241.7 | 15.1 | - |
| smoke | `gemini-3.8-flash-tts` | 5 | 5 | 0 | 0 | 0 | 0 | 79.6 | 15.9 | - |
| smoke | `kaggle-api-v1` | 0 | 0 | 0 | 0 | 0 | 5 | 0.0 | - | - |
| tts-prompt-experiment | `gemini-3.5-flash` | 4 | 4 | 0 | 0 | 0 | 0 | 94.8 | 23.7 | - |
| tts-prompt-experiment | `gemini-3.8-flash-tts` | 4 | 3 | 1 | 0 | 0 | 0 | 54.0 | 13.5 | - |
| voices | `gemini-3.8-flash-tts` | 3 | 3 | 0 | 0 | 0 | 0 | 34.9 | 11.6 | - |
| **total** | | 166 | 107 | 42 | 17 | 221 | 10 | 1613.5 | | 0.0916 |

Image calls used 8,331 Workers AI neurons (free allowance: 10,000 per day). GPU minutes: 0 (no Kaggle job has run).
How to read the stages:
- `smoke` and `tts-prompt-experiment` come from the dropped smoke test and the TTS prompt experiment (EXPERIMENTS.md E1).
- `placeholder-tone` is the local sine-tone stand-in used before Gemini TTS: not a model, and free.
- The 36 failed or retried `gemini-3.8-flash` script attempts are FAILURES.md F1: 503 "high demand" and 429 quota errors. The fallback `gemini-3.5-flash` drafted all 12 lines.

**Not in the log:** one Gemini TTS request made by hand with `curl` on 2026-11-25, around 20:55 UTC, to read the full quota error (FAILURES.md F3). It succeeded and used one of the day's 10 TTS requests.

## List-price equivalent

What the same successful calls would cost on paid tiers. Prices as published on 2026-11-26.

| Provider and model | Measured usage | List price | Equivalent |
|---|---|---|---|
| Cloudflare Workers AI, FLUX.2 klein 4B | 36 images: 32 keyframes at 1920×1088 (8 output tiles each) and 4 character sheets at 1024×1024 (4 tiles), plus 1024×1024 reference inputs. Total 8,331 neurons. | 26.05 neurons per 512×512 output tile, 5.37 per input tile, $0.011 per 1,000 neurons | **$0.092** |
| Gemini 3.8 Flash TTS | 18 kept clips (15 narration + 3 voice trial), 69.5 s of audio, measured from the WAV files. The 8 smoke/experiment clips (about 37 s more) are not included. | $9.00 per 1M audio tokens through 2026, 25 tokens per second of audio | **$0.016** |
| Gemini 3.5 / 3.8 Flash (text) | 12 successful Amharic drafts plus the smoke and experiment calls, each a few hundred tokens | not priced here: well under $0.01 in total at any current Flash rate | **< $0.01** |
| Kaggle GPU (Wan 2.2, ACE-Step) | 0 GPU minutes: not run yet | free quota, about 30 GPU hours a week | **$0** |
| **Total** | | | **about $0.11** |

The image figure comes from `make costs`, computed from each call's logged size and references; the TTS figure from the measured audio.

## Quotas, the real constraint

| Quota | Limit found | Used | What it meant |
|---|---|---|---|
| Gemini TTS, free tier | 10 requests per day per Google Cloud project | narration needed 13 lines, plus the voice trial (3) and redos | narration took three projects' keys over two days (FAILURES.md F3) |
| Gemini text `gemini-3.8-flash`, free tier | 503 "high demand" bursts, then 429 quota | 0 of 12 drafts succeeded on it | switched to `gemini-3.5-flash` first (F1) |
| Workers AI | 10,000 neurons per day | 8,331 on 2026-11-26 | about 45 keyframes a day at 1920×1088 with one reference |

## Time

From the log: 1,614 s of model latency in total, across 166 attempts. Per successful call:

| Call | Typical latency |
|---|---|
| Keyframe | about 14 s |
| Character sheet | about 15 s |
| TTS line | 3–6 s on a quiet minute (up to 24 s) |
| Amharic draft on `gemini-3.5-flash` | 7–46 s |

FFmpeg work is local and not logged as model time. On the author's machine (no GPU):
- Pan shots: roughly real time per aspect ratio.
- Each export: well under a minute.
- A full `make film` with everything cached makes 0 calls and spends a few minutes in FFmpeg.

Without the quota limits, a full build from a fresh clone would take roughly 15–20 minutes.

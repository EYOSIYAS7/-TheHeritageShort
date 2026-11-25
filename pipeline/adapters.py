"""Real provider adapters: thin wrappers over the live HTTP APIs.

Each implements one interface from `pipeline.providers`, so stages take them in
place of the fakes without changing. They use only the standard library (no SDKs
to pin). A 4xx answer other than 408/429 raises `PermanentError` (bad key,
unknown model, rejected input: retrying cannot help); anything else is left
to the run log to retry.

Not unit-tested (they are thin wrappers over live APIs); `GeminiText` and
`GeminiSpeech` have been called live, `CloudflareImage` and `KaggleJobs` not yet
(see FAILURES.md).
Cost estimates are 0.0 because every call here runs on a free tier; list-price
equivalents are worked out in COSTS.md.
"""

from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
import uuid
import wave
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pipeline.runlog import PermanentError, RateLimited

TIMEOUT_S = 120
MAX_WAIT_S = 120  # a rate limit asking for a longer wait than this is treated as permanent
_RETRYABLE = {408, 429}


def _request(url: str, *, headers: dict[str, str], body: bytes | None = None, method: str = "POST") -> bytes:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            data: bytes = resp.read()
            return data
    except urllib.error.HTTPError as e:
        body = e.read()
        message = f"HTTP {e.code} from {url.split('?')[0]}: {_error_detail(body)}"
        if 400 <= e.code < 500 and e.code not in _RETRYABLE:
            raise PermanentError(message) from None
        retry_after = _retry_after_s(body)
        if retry_after is not None and retry_after > MAX_WAIT_S:  # a daily quota: waiting won't help today
            raise PermanentError(f"{message} (retry after {retry_after:.0f} s)") from None
        if retry_after is not None:
            raise RateLimited(message, retry_after) from None
        raise ConnectionError(message) from None


def _error_detail(body: bytes) -> str:
    """The API's own error message if the body is JSON ({"error": {"message": ...}}), else the text, on one line."""
    text = body.decode("utf-8", "replace")
    try:
        parsed = json.loads(text)
        errors = parsed.get("errors") if isinstance(parsed, dict) else None  # Cloudflare: {"errors": [{"message"}]}
        if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
            text = str(parsed["error"].get("message", text))
        elif isinstance(errors, list) and errors and isinstance(errors[0], dict):
            text = "; ".join(str(e.get("message", e)) for e in errors)
    except ValueError:
        pass
    return " ".join(text.split())[:500]


def _retry_after_s(body: bytes) -> float | None:
    """Google's `RetryInfo.retryDelay` (e.g. "37s"), plus a second of margin; None if absent."""
    match = re.search(rb'"retryDelay":\s*"([\d.]+)s"', body)
    return float(match.group(1)) + 1.0 if match else None


def _json_request(url: str, payload: dict[str, Any], headers: dict[str, str]) -> Any:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return json.loads(_request(url, headers={**headers, "Content-Type": "application/json"}, body=body))


# --- Gemini (Google AI Studio) ----------------------------------------------------------------

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _gemini_parts(response: Any) -> list[dict[str, Any]]:
    try:
        parts: list[dict[str, Any]] = response["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Gemini returned no content: {json.dumps(response)[:400]}") from None
    return parts


class GeminiText:
    """Text generation (script stage: Amharic drafts). Implements `TextProvider`."""

    def __init__(self, api_key: str, model: str = "gemini-3.8-flash") -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, *, seed: int) -> str:
        response = _json_request(
            GEMINI_URL.format(model=self.model),
            {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"seed": seed}},
            {"x-goog-api-key": self.api_key},
        )
        text = "".join(p.get("text", "") for p in _gemini_parts(response)).strip()
        if not text:
            raise RuntimeError("Gemini returned an empty reply")
        return text

    def cost_estimate_usd(self, prompt: str) -> float:
        return 0.0


class GeminiSpeech:
    """Gemini TTS: one WAV per line. Implements `SpeechProvider`.

    The style instruction goes in a "director's notes" block, separate from the
    transcript, which is how Gemini TTS is steered. The response is raw 16-bit mono PCM; its sample rate is read from the MIME type.
    """

    def __init__(self, api_key: str, model: str = "gemini-3.8-flash-tts") -> None:
        self.api_key = api_key
        self.model = model

    def synthesize(self, text: str, *, language: str, voice: str, style: str, seed: int, out_path: Path) -> None:
        if not self.api_key:
            raise PermanentError("GEMINI_API_KEY is missing in .env, and this line has no cached audio")
        payload = {
            "contents": [{"parts": [{"text": self.prompt(text, language=language, style=style)}]}],
            "generationConfig": {
                "seed": seed,
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
            },
        }
        response = _json_request(GEMINI_URL.format(model=self.model), payload, {"x-goog-api-key": self.api_key})
        audio = next((p["inlineData"] for p in _gemini_parts(response) if "inlineData" in p), None)
        if audio is None:
            raise RuntimeError(f"Gemini TTS returned no audio: {json.dumps(response)[:400]}")
        rate = re.search(r"rate=(\d+)", audio.get("mimeType", ""))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(out_path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(int(rate.group(1)) if rate else 24_000)
            w.writeframes(base64.b64decode(audio["data"]))

    def prompt(self, text: str, *, language: str, style: str) -> str:
        # Director's notes kept apart from the transcript: with a one-line "Say this ...:" prefix
        # the 3-word Amharic line came back as 11.8 s, ~8.8 s of it not the line (EXPERIMENTS.md).
        return (f"### DIRECTOR'S NOTES\nLanguage: {_LANGUAGE_NAMES.get(language, language)}. Style: {style}.\n"
                f"Read only the transcript below, nothing else.\n\n### TRANSCRIPT\n{text}")

    def cost_estimate_usd(self, text: str) -> float:
        return 0.0


_LANGUAGE_NAMES = {"am": "Amharic", "en": "English"}


# --- Cloudflare Workers AI --------------------------------------------------------------------

CLOUDFLARE_URL = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"


class CloudflareImage:
    """FLUX.2 klein on Workers AI. Implements `ImageProvider`.

    FLUX.2 models on Workers AI take multipart/form-data (prompt, seed, width,
    height, and reference images as input_image_0..N) and answer JSON with the
    image as base64 in `result.image`.
    """

    def __init__(self, account_id: str, api_token: str, model: str = "@cf/black-forest-labs/flux-2-klein-4b") -> None:
        self.account_id = account_id
        self.api_token = api_token
        self.model = model

    def generate(self, prompt: str, *, seed: int, width: int, height: int, out_path: Path,
                 references: tuple[Path, ...] = ()) -> None:
        fields: list[tuple[str, str | tuple[str, bytes]]] = [
            ("prompt", prompt), ("seed", str(seed)), ("width", str(width)), ("height", str(height)),
        ]
        fields += [(f"input_image_{i}", (ref.name, ref.read_bytes())) for i, ref in enumerate(references)]
        body, content_type = _multipart(fields)
        raw = _request(
            CLOUDFLARE_URL.format(account=self.account_id, model=self.model),
            headers={"Authorization": f"Bearer {self.api_token}", "Content-Type": content_type},
            body=body,
        )
        response = json.loads(raw)
        image = (response.get("result") or {}).get("image")
        if not response.get("success", True) or not image:
            raise RuntimeError(f"Cloudflare returned no image: {raw[:400]!r}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(base64.b64decode(image))

    def cost_estimate_usd(self, prompt: str) -> float:
        return 0.0


def _multipart(fields: list[tuple[str, str | tuple[str, bytes]]]) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    out = bytearray()
    for name, value in fields:
        out += f"--{boundary}\r\n".encode()
        if isinstance(value, str):
            out += f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        else:
            filename, data = value
            out += (f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                    "Content-Type: image/png\r\n\r\n").encode()
            out += data + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


# --- Kaggle -----------------------------------------------------------------------------------

KAGGLE_API = "https://www.kaggle.com/api/v1"


class KaggleJobs:
    """GPU jobs as Kaggle notebooks. Implements `GpuJobs`.

    For now only authentication; pushing and polling notebooks (Wan 2.2, ACE-Step)
    arrive with the moving-shot and score stages. Accepts both the legacy
    username + key (HTTP basic auth) and the newer KGAT_ API tokens (bearer).
    """

    model = "kaggle-api-v1"

    def __init__(self, username: str, key: str) -> None:
        self.username = username
        self.key = key

    def authenticate(self) -> str:
        """Make one authenticated read; return what the account can see."""
        if self.key.startswith("KGAT_"):
            auth = f"Bearer {self.key}"
        else:
            auth = "Basic " + base64.b64encode(f"{self.username}:{self.key}".encode()).decode()
        raw = _request(f"{KAGGLE_API}/kernels/list?mine=true&pageSize=1",
                       headers={"Authorization": auth}, method="GET")
        kernels = json.loads(raw) if raw.strip() else []
        return f"authenticated as {self.username} ({len(kernels)} notebook(s) on the first page)"


if TYPE_CHECKING:  # mypy checks each adapter against the interface it claims
    from pipeline.providers import GpuJobs, ImageProvider, SpeechProvider, TextProvider

    def _implements(t: GeminiText, s: GeminiSpeech, i: CloudflareImage, k: KaggleJobs
                    ) -> tuple[TextProvider, SpeechProvider, ImageProvider, GpuJobs]:
        return t, s, i, k

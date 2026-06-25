"""AI engine — Google Gemini (free tier).

Uses the current `google-genai` SDK and the `gemini-3-flash-preview` model.
The API key is read from the GEMINI_API_KEY environment variable (loaded from
.env). The key is never logged or returned to the frontend.
"""

from __future__ import annotations

import os
from functools import lru_cache

# "auto" tries these in order and falls back when one is rate-limited or
# unavailable. Stable models first (high free-tier quota); the preview model
# last because its free quota is tiny. Override the front of the list with
# GEMINI_MODEL in .env if you want a specific model tried first.
AUTO_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-3-flash-preview"]

_env_model = (os.environ.get("GEMINI_MODEL") or "").strip()
if _env_model:
    AUTO_MODELS = [_env_model] + [m for m in AUTO_MODELS if m != _env_model]

# Label shown to the engine/UI.
DEFAULT_MODEL = "auto"


class GeminiError(RuntimeError):
    """Raised for any AI-mode problem we want to show the user verbatim."""


# One combined instruction: grammar + professional + concise, all in one.
# The model returns ONLY the rewritten text — no preamble, markdown or quotes.
_INSTRUCTION = (
    "Fix all grammar, spelling and punctuation, and rewrite the text to be "
    "clear, professional and concise — suitable for a workplace email or "
    "escalation. Keep the original meaning and all facts. Remove filler and "
    "redundancy. Use a courteous, confident, neutral business tone.\n"
    "IMPORTANT: If the text is already correct, clear and professional, return "
    "it EXACTLY as-is with no changes. Do not rephrase or restructure when it is "
    "not needed — only change what genuinely improves it."
)

_SYSTEM = (
    "You are a precise writing assistant for workplace communication. "
    "You return ONLY the corrected/rewritten text with no explanations, no "
    "preamble, no markdown formatting, and no surrounding quotation marks."
)


@lru_cache(maxsize=1)
def _client():
    api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise GeminiError(
            "No Gemini API key found. Add GEMINI_API_KEY to your .env file or "
            "paste a key in the app's key box. Get a free key at "
            "https://aistudio.google.com/apikey"
        )
    try:
        from google import genai  # type: ignore
    except Exception as e:  # pragma: no cover
        raise GeminiError(
            "google-genai is not installed. Run: "
            "library\\Scripts\\python -m pip install google-genai"
        ) from e
    return genai.Client(api_key=api_key)


def _is_bad_key(err: str) -> bool:
    low = err.lower()
    return any(s in low for s in ("api key", "api_key", "401", "permission_denied", "unauthorized"))


def _is_retryable(err: str) -> bool:
    low = err.lower()
    return any(
        s in low
        for s in ("429", "resource_exhausted", "quota", "rate", "404",
                  "not found", "unavailable", "500", "503", "overloaded")
    )


def check_ai(text: str, model: str | None = None, style: str = "") -> dict:
    """Send the text to Gemini. With model=None, auto-tries the model list and
    falls back when one is rate-limited / unavailable. If `style` is given, the
    rewrite mimics the tone/format of those example emails."""
    from google.genai import types  # type: ignore

    client = _client()
    prompt = _INSTRUCTION
    if style.strip():
        prompt += (
            "\n\nThe user has provided examples of their own writing style and "
            "email format below. Match this tone, vocabulary, greetings, "
            "sign-offs and overall structure as closely as possible while still "
            "fixing any errors:\n"
            "=== STYLE EXAMPLES ===\n" + style.strip() + "\n=== END EXAMPLES ==="
        )
    prompt += f"\n\n---\nTEXT TO REWRITE:\n{text}\n---"
    config = types.GenerateContentConfig(
        system_instruction=_SYSTEM, temperature=0.3
    )

    models = [model] if model else AUTO_MODELS
    last_err = ""

    for name in models:
        try:
            resp = client.models.generate_content(
                model=name, contents=prompt, config=config
            )
        except Exception as e:
            err = str(e)
            if _is_bad_key(err):
                raise GeminiError(err) from e
            last_err = err
            if _is_retryable(err):
                continue  # try the next model
            continue

        out = (getattr(resp, "text", None) or "").strip().strip("`").strip()
        if (out.startswith('"') and out.endswith('"')) or (
            out.startswith("'") and out.endswith("'")
        ):
            out = out[1:-1].strip()

        if out:
            return {"result": out, "engine": "ai", "model": name, "note": ""}
        last_err = "empty response"

    raise GeminiError(last_err or "Gemini request failed")


def has_key() -> bool:
    return bool((os.environ.get("GEMINI_API_KEY") or "").strip())

"""The one entry point the web layer calls.

Runs the AI rewrite (grammar + professional + concise, all in one), using the
user's saved style examples as the basis, and records every input/output to the
history log.
"""

from __future__ import annotations

import os
from pathlib import Path

from . import gemini as ai_engine
from . import store

store.init()

# Project root = three levels up: src/phrasecheck/engine/checker.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"


def check(text: str) -> dict:
    """Run the AI rewrite. Returns {ai, ai_error}."""
    text = (text or "").strip()
    if not text:
        return {"ai": "", "ai_error": ""}

    if not ai_engine.has_key():
        return {"ai": "", "ai_error": "no key"}

    try:
        ai_out = ai_engine.check_ai(text, style=store.combined_style())["result"]
        store.add_history(text, ai_out)
        return {"ai": ai_out, "ai_error": ""}
    except Exception as e:
        return {"ai": "", "ai_error": _friendly(str(e))}


def _friendly(msg: str) -> str:
    """Shorten noisy API errors to a single terse line."""
    low = msg.lower()
    if "resource_exhausted" in low or "429" in low or "quota" in low:
        return "rate limit, try again shortly"
    if "api key" in low or "api_key" in low or "permission" in low or "401" in low:
        return "invalid/missing key"
    if "not found" in low or "404" in low:
        return "model unavailable"
    return msg.splitlines()[0][:120]


def status() -> dict:
    return {"has_key": ai_engine.has_key(), "model": ai_engine.DEFAULT_MODEL}


def save_key(key: str) -> dict:
    """Persist a Gemini key to .env and make it live this session."""
    key = (key or "").strip()
    if not key:
        return {"ok": False, "error": "Empty key."}

    os.environ["GEMINI_API_KEY"] = key
    try:
        ai_engine._client.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass

    lines = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith("GEMINI_API_KEY="):
            lines[i] = f"GEMINI_API_KEY={key}"
            found = True
            break
    if not found:
        lines.append(f"GEMINI_API_KEY={key}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True}

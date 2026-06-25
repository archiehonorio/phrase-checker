"""SQLite store for saved style examples and the input/output history (log).

Two tables:
  styles  — the user's saved writing-style / example emails (the "basis")
  history — every check: the input and the AI-generated output
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "phrasecheck.db"
_lock = Lock()


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init() -> None:
    with _lock, _conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS styles ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "text TEXT NOT NULL, created TEXT NOT NULL)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS history ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "input TEXT NOT NULL, output TEXT NOT NULL, created TEXT NOT NULL)"
        )


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ---- styles -------------------------------------------------------------- #

def add_style(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty"}
    with _lock, _conn() as c:
        cur = c.execute(
            "INSERT INTO styles(text, created) VALUES(?, ?)", (text, _now())
        )
        return {"ok": True, "id": cur.lastrowid}


def list_styles() -> list[dict]:
    with _lock, _conn() as c:
        rows = c.execute(
            "SELECT id, text, created FROM styles ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def delete_style(sid: int) -> dict:
    with _lock, _conn() as c:
        c.execute("DELETE FROM styles WHERE id = ?", (sid,))
    return {"ok": True}


def clear_styles() -> dict:
    with _lock, _conn() as c:
        c.execute("DELETE FROM styles")
    return {"ok": True}


def combined_style() -> str:
    """All saved style examples joined into one basis for the AI."""
    parts = [r["text"] for r in list_styles()]
    return "\n\n---\n\n".join(parts)


# ---- history (log) ------------------------------------------------------- #

def add_history(inp: str, out: str) -> None:
    with _lock, _conn() as c:
        c.execute(
            "INSERT INTO history(input, output, created) VALUES(?, ?, ?)",
            (inp, out, _now()),
        )


def list_history(q: str = "") -> list[dict]:
    q = (q or "").strip()
    with _lock, _conn() as c:
        if q:
            like = f"%{q}%"
            rows = c.execute(
                "SELECT id, input, output, created FROM history "
                "WHERE input LIKE ? OR output LIKE ? ORDER BY id DESC LIMIT 300",
                (like, like),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT id, input, output, created FROM history "
                "ORDER BY id DESC LIMIT 300"
            ).fetchall()
        return [dict(r) for r in rows]


def delete_history(hid: int) -> dict:
    with _lock, _conn() as c:
        c.execute("DELETE FROM history WHERE id = ?", (hid,))
    return {"ok": True}


def clear_history() -> dict:
    with _lock, _conn() as c:
        c.execute("DELETE FROM history")
    return {"ok": True}

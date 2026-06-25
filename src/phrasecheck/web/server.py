"""Local Flask app — the 'looks like an app' presentation layer.

Thin shell over engine/checker.py. No logic lives here. Serves a single
terminal-styled page and a small JSON API. Runs entirely on localhost.
"""

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, render_template, request, jsonify

# Load .env early so GEMINI_API_KEY is available before the engine imports.
try:
    from dotenv import load_dotenv

    _root = Path(__file__).resolve().parents[3]
    load_dotenv(_root / ".env")
except Exception:
    pass

from ..engine import checker
from ..engine import store


def _web_asset_dirs() -> tuple[str, str]:
    """Absolute templates/static dirs, working both in dev and in a frozen .exe."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        return str(base / "templates"), str(base / "static")
    here = Path(__file__).resolve().parent
    return str(here / "templates"), str(here / "static")


def create_app() -> Flask:
    tpl, stc = _web_asset_dirs()
    app = Flask(__name__, template_folder=tpl, static_folder=stc)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/status")
    def api_status():
        return jsonify(checker.status())

    @app.post("/api/check")
    def api_check():
        data = request.get_json(force=True, silent=True) or {}
        text = data.get("text") or ""
        try:
            return jsonify(checker.check(text))
        except Exception as e:  # pragma: no cover
            return jsonify({"error": f"Unexpected error: {e}"}), 500

    @app.post("/api/key")
    def api_key():
        data = request.get_json(force=True, silent=True) or {}
        res = checker.save_key(data.get("key") or "")
        return (jsonify(res), 200) if res.get("ok") else (jsonify(res), 400)

    # ----- styles (the saved "basis" examples) ---------------------------- #

    @app.get("/api/styles")
    def api_styles_list():
        return jsonify({"styles": store.list_styles()})

    @app.post("/api/styles")
    def api_styles_add():
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(store.add_style(data.get("text") or ""))

    @app.post("/api/styles/delete")
    def api_styles_delete():
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(store.delete_style(int(data.get("id") or 0)))

    @app.post("/api/styles/clear")
    def api_styles_clear():
        return jsonify(store.clear_styles())

    # ----- log (history) -------------------------------------------------- #

    @app.get("/api/log")
    def api_log_list():
        return jsonify({"items": store.list_history(request.args.get("q", ""))})

    @app.post("/api/log/delete")
    def api_log_delete():
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(store.delete_history(int(data.get("id") or 0)))

    @app.post("/api/log/clear")
    def api_log_clear():
        return jsonify(store.clear_history())

    return app

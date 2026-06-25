# phrase-check

A discreet, **terminal/cmd-styled** desktop app that fixes and polishes your
writing — grammar, professionalism and conciseness in one pass — with a
one-click copy button. Built for quietly cleaning up work emails and
escalations. It *looks* like a terminal, but it isn't one.

- One combined AI rewrite: fixes grammar **and** makes it professional **and**
  concise — and leaves text alone when it's already good.
- Learns **your** voice from saved example emails (stored in a local database).
- Searchable **history** of everything you've checked, with copy + reuse.
- Runs as a native window with a terminal app icon.

## How it works

The rewrite is powered by the **Google Gemini** free API. The engine is
**`auto`**: it tries stable models first and automatically falls back if one is
rate-limited or unavailable:

```
gemini-2.5-flash  →  gemini-2.0-flash  →  gemini-3-flash-preview
```

Override the model that's tried first with `GEMINI_MODEL` in `.env`.

## Commands

Type/paste into the prompt and press **Enter** (**Shift+Enter** for a newline).

| Command | What it does |
|---------|--------------|
| *(any text)* | Rewrite it (grammar + professional + concise) |
| `cls` or `-cls` | Clear the screen |
| `key YOUR_API_KEY` | Save your Gemini API key |
| `-settings` | Manage your saved writing-style examples (the AI's "basis") |
| `-log` | Open searchable history (copy a result, or **[use]** to reload an input) |

### `-settings` — teach it your style
Opens a box where you paste an example email/format and press **[save]**. Add as
many as you like; each is stored separately with its own **[delete]**. Every
rewrite uses all of them as the basis, so replies sound like you.

### `-log` — history
Every input and AI output is saved. Search by text, **[copy]** a result,
**[use]** to reload an old input, or **[delete]** entries.

## Setup

Everything installs into a venv named **`library`**.

```powershell
# create the venv (once)
py -3 -m venv library

# install dependencies
library\Scripts\python -m pip install -r requirements.txt
```

### Get a free Gemini API key
1. Go to https://aistudio.google.com/apikey (Google account, no credit card)
2. Create a key and copy it
3. Either open the app and type `key YOUR_API_KEY`, **or** copy `.env.example`
   to `.env` and set `GEMINI_API_KEY=`

## Run

```powershell
# native app window (recommended)
library\Scripts\python desktop.py

# or in your browser
library\Scripts\python run.py     # opens http://127.0.0.1:5000
```

## Build a fully standalone .exe

No Python needed on the target machine after this.

```powershell
# 1) install the packager (once)
library\Scripts\python -m pip install pyinstaller

# 2) build it — this is the command that makes it standalone
build.bat
```

Result: **`dist\PhraseCheck\PhraseCheck.exe`** (double-click to run; pin to
taskbar to get the terminal icon).

> For AI mode in the packaged app, put a `.env` file containing your
> `GEMINI_API_KEY` next to `PhraseCheck.exe`.

`build.bat` simply runs PyInstaller with the right flags. The equivalent raw
command is:

```powershell
library\Scripts\python -m PyInstaller --noconfirm --windowed --onedir ^
  --name PhraseCheck --icon "assets\icon.ico" ^
  --paths src --collect-submodules phrasecheck ^
  --collect-all webview --collect-all google.genai ^
  --add-data "src/phrasecheck/web/templates;templates" ^
  --add-data "src/phrasecheck/web/static;static" ^
  --add-data "assets/icon.ico;." ^
  desktop.py
```

## App icon
The terminal logo lives at `assets/icon.ico` (window + taskbar + .exe) and
`src/phrasecheck/web/static/favicon.png` (page). Re-generate or tweak with:

```powershell
library\Scripts\python assets\make_icon.py
```

## Data & privacy
These stay on your machine and are gitignored — they are never committed:

| File | Contents |
|------|----------|
| `.env` | Your Gemini API key |
| `phrasecheck.db` | Saved style examples + history (SQLite) |

## Layout
```
src/phrasecheck/
  engine/
    gemini.py    # AI engine (auto model fallback)
    store.py     # SQLite: style examples + history
    checker.py   # ties it together, logs history
  web/
    server.py    # Flask routes (/api/check, /api/styles, /api/log, /api/key)
    templates/index.html
    static/app.js, style.css, favicon.png
run.py           # browser launcher
desktop.py       # native window launcher (pywebview) + taskbar icon
build.bat        # package to a standalone .exe
assets/          # icon.ico + make_icon.py
```

# phrase-check

A discreet, terminal-styled desktop app for fixing and polishing your writing —
grammar fixes, professional rewrites, and concise rewrites — with a one-click
copy button. Built for quietly cleaning up work emails and escalations.

It looks like a terminal, but it isn't one.

## Two engines

| Mode | What it does | Needs |
|------|--------------|-------|
| 🌐 **AI (Gemini)** | Truly rewrites: fix grammar, make professional, make concise | A free Gemini API key + internet |
| 🔒 **Local** | Offline, private. Fixes spelling, spacing, punctuation, capitalization | Nothing — works fully offline |

The model is **`gemini-3-flash-preview`**.

## Setup

Everything installs into a venv named **`library`** (already created).

```powershell
# from the project folder
library\Scripts\python -m pip install -r requirements.txt
```

### Get a free Gemini API key
1. Go to https://aistudio.google.com/apikey (Google account, no credit card)
2. Create a key, copy it
3. Either:
   - Open the app and click **● key** (top-right) and paste it, **or**
   - Copy `.env.example` to `.env` and put the key in `GEMINI_API_KEY=`

Local mode works without any key.

## Run

```powershell
# As a native app window (recommended)
library\Scripts\python desktop.py

# Or in your browser
library\Scripts\python run.py     # opens http://127.0.0.1:5000
```

## Build a standalone .exe (optional)

```powershell
library\Scripts\python -m pip install pyinstaller
build.bat
```
Result: `dist\PhraseCheck\PhraseCheck.exe`. Put your `.env` next to the `.exe`
for AI mode.

## Shortcuts
- **Ctrl+Enter** — run
- **📋 copy** — copy the result

## Layout
```
src/phrasecheck/
  engine/
    local.py     # offline fixer (pure Python)
    gemini.py    # AI engine (gemini-3-flash-preview)
    checker.py   # routes engine + modes, saves the key
  web/
    server.py    # Flask routes
    templates/index.html
    static/style.css, app.js
run.py           # browser launcher
desktop.py       # native window launcher (pywebview)
build.bat        # package to .exe
```

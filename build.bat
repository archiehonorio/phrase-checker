@echo off
REM Build PhraseCheck.exe (a standalone Windows app) with PyInstaller.
REM Uses the "library" venv. Run once:  library\Scripts\python -m pip install pyinstaller
cd /d "%~dp0"

echo Building PhraseCheck.exe ...
".\library\Scripts\python.exe" -m PyInstaller --noconfirm --windowed --onedir ^
  --name PhraseCheck ^
  --icon "assets\icon.ico" ^
  --paths src --collect-submodules phrasecheck ^
  --collect-all webview --collect-all google.genai --collect-all spellchecker ^
  --add-data "src/phrasecheck/web/templates;templates" ^
  --add-data "src/phrasecheck/web/static;static" ^
  --add-data "assets/icon.ico;." ^
  desktop.py

echo.
echo Done. The app is in  dist\PhraseCheck\PhraseCheck.exe
echo NOTE: put your .env (with GEMINI_API_KEY) next to the .exe for AI mode.
pause

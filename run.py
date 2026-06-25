"""Run Phrase-Check in your browser (dev mode).

    library\\Scripts\\python run.py

Then open http://127.0.0.1:5000
"""

import sys
import webbrowser
from pathlib import Path
from threading import Timer

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from phrasecheck.web.server import create_app  # noqa: E402

HOST = "127.0.0.1"
PORT = 5000

if __name__ == "__main__":
    app = create_app()
    Timer(1.0, lambda: webbrowser.open(f"http://{HOST}:{PORT}")).start()
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)

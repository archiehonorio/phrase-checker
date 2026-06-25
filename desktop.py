"""Phrase-Check — native desktop app entry point.

Runs the Flask engine on a background thread and shows the UI in a real OS
window via pywebview (no browser, no console). This is the file PyInstaller
packages into PhraseCheck.exe. For a normal dev run you can also just:

    library\\Scripts\\python desktop.py
"""

import socket
import sys
import threading
import time
from pathlib import Path

# In dev the package lives under ./src. When frozen, PyInstaller bundles it.
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

HOST = "127.0.0.1"
PORT = 5001
URL = f"http://{HOST}:{PORT}"


def _port_open() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((HOST, PORT)) == 0


def _start_server():
    from phrasecheck.web.server import create_app

    app = create_app()
    app.run(host=HOST, port=PORT, threaded=True, use_reloader=False, debug=False)


def _wait_until_up(timeout: float = 15.0) -> bool:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        if _port_open():
            return True
        time.sleep(0.15)
    return False


def _icon_path() -> str:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        return str(base / "icon.ico")
    return str(Path(__file__).resolve().parent / "assets" / "icon.ico")


def _apply_taskbar_icon(ico_path: str):
    """Make the taskbar/window use our icon instead of the Python icon.

    Sets a distinct AppUserModelID (so Windows groups it as its own app) and
    pushes the .ico onto our process's visible window via WM_SETICON. Best
    effort and Windows-only — silently does nothing elsewhere.
    """
    import os
    import ctypes
    from ctypes import wintypes

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "PhraseCheck.Terminal.1"
        )
    except Exception:
        return

    user32 = ctypes.windll.user32
    IMAGE_ICON, LR_LOADFROMFILE, LR_DEFAULTSIZE = 1, 0x10, 0x40
    WM_SETICON, ICON_SMALL, ICON_BIG = 0x80, 0, 1
    pid = os.getpid()

    def worker():
        hicon = user32.LoadImageW(
            None, ico_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
        )
        if not hicon:
            return
        WNDENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool, wintypes.HWND, wintypes.LPARAM
        )
        found = []

        def cb(hwnd, _):
            lpid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lpid))
            if lpid.value == pid and user32.IsWindowVisible(hwnd):
                found.append(hwnd)
            return True

        for _ in range(200):
            found.clear()
            user32.EnumWindows(WNDENUMPROC(cb), 0)
            if found:
                for hwnd in found:
                    user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                    user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                break
            time.sleep(0.1)

    threading.Thread(target=worker, daemon=True).start()


def main():
    import webview

    if not _port_open():
        threading.Thread(target=_start_server, daemon=True).start()
        _wait_until_up()

    _apply_taskbar_icon(_icon_path())

    webview.create_window(
        "Command Prompt",
        URL,
        width=720,
        height=460,
        min_size=(420, 260),
    )
    webview.start()


if __name__ == "__main__":
    main()

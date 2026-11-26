"""Start the LogisticsUpdate AI FastAPI application."""

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = BASE_DIR / ".venv" / "bin" / "python"

if __name__ == "__main__" and VENV_PYTHON.exists() and sys.executable != str(VENV_PYTHON):
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), __file__] + sys.argv[1:])

import uvicorn


def _open_dashboard_when_ready(url: str) -> None:
    """Open the dashboard after the local server starts responding."""
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1):
                break
        except HTTPError:
            break
        except OSError:
            time.sleep(0.25)
    else:
        return

    if not webbrowser.open_new_tab(url):
        print(f"Open the dashboard in your browser: {url}")


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    port = int(os.getenv("PORT", "8000"))
    dashboard_url = f"http://127.0.0.1:{port}/"
    threading.Thread(
        target=_open_dashboard_when_ready,
        args=(dashboard_url,),
        daemon=True,
    ).start()
    uvicorn.run("app.main:app", host="127.0.0.1", port=port)

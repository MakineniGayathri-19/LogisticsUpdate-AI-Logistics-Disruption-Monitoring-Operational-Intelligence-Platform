"""Tests for the local launcher opening the dashboard when ready."""
from contextlib import nullcontext

import run as launcher


def test_launcher_opens_dashboard_after_server_responds(monkeypatch):
    attempts = 0
    opened_urls = []

    def fake_urlopen(url, timeout):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("server not ready")
        return nullcontext()

    monkeypatch.setattr(launcher, "urlopen", fake_urlopen)
    monkeypatch.setattr(launcher.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        launcher.webbrowser,
        "open_new_tab",
        lambda url: opened_urls.append(url) or True,
    )

    launcher._open_dashboard_when_ready("http://127.0.0.1:8000/")

    assert attempts == 2
    assert opened_urls == ["http://127.0.0.1:8000/"]

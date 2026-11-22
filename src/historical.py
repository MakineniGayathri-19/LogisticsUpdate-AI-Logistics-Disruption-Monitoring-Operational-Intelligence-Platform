"""Historical context module using Memento.
Provides thin wrappers to save a disruption record and retrieve similar past events.
"""
import json
from pathlib import Path
from typing import List, Dict

from .config import MEMENTO_REPO_DIR, PROCESSED_DATA_DIR

# Initialize Memento repo – if not a repo yet, init it
def init_repo():
    if not (MEMENTO_REPO_DIR / ".git").exists():
        # Simple git init via subprocess (daemon not required)
        import subprocess, os
        subprocess.run(["git", "init"], cwd=str(MEMENTO_REPO_DIR), check=True)
        # Commit an empty initial state
        (MEMENTO_REPO_DIR / "README.md").write_text("Memento repository for logistics disruptions", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(MEMENTO_REPO_DIR), check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=str(MEMENTO_REPO_DIR), check=True)


def save_event(event: Dict):
    """Save a single event dict as a JSON file and commit to Memento (git)."""
    init_repo()
    # Use timestamp and a short hash for filename
    import time, hashlib, subprocess
    ts = int(time.time())
    h = hashlib.sha1(json.dumps(event, sort_keys=True).encode()).hexdigest()[:6]
    filename = f"event_{ts}_{h}.json"
    path = MEMENTO_REPO_DIR / filename
    path.write_text(json.dumps(event, indent=2), encoding="utf-8")
    # Git add & commit
    subprocess.run(["git", "add", filename], cwd=str(MEMENTO_REPO_DIR), check=True)
    subprocess.run(["git", "commit", "-m", f"Add disruption event {h}"], cwd=str(MEMENTO_REPO_DIR), check=True)
    return path


def load_past_events(limit: int = 20) -> List[Dict]:
    """Load recent events (JSON files) from the repo, up to *limit* entries.
    Returns list of dicts sorted newest first.
    """
    init_repo()
    files = sorted(MEMENTO_REPO_DIR.glob("event_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    events = []
    for p in files[:limit]:
        try:
            events.append(json.loads(p.read_text()))
        except Exception:
            continue
    return events

if __name__ == "__main__":
    # Simple demo: load and print latest events
    print(json.dumps(load_past_events(), indent=2))

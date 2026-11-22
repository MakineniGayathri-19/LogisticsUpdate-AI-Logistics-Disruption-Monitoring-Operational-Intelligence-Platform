"""One-Command Runner for LogisticsUpdate AI.
Starts both the FastAPI Backend and Streamlit Frontend in a single terminal.
Press Ctrl+C to stop both servers simultaneously.
"""
import sys
import time
import subprocess
import signal
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def main():
    print("==================================================================")
    print("🚢 LogisticsUpdate AI – Starting Unified Application Platform")
    print("==================================================================")

    # 1. Initialize SQLite Database
    print("\n📦 [1/3] Checking & initializing database...")
    try:
        from database.db import init_db
        init_db()
        print("    ✓ Database tables initialized.")
    except Exception as e:
        print(f"    ⚠️ Warning during DB init: {e}")

    # Python executable to use
    python_exe = sys.executable

    # 2. Start FastAPI Backend in background
    print("\n⚡ [2/3] Starting FastAPI Backend on http://127.0.0.1:8000...")
    backend_cmd = [
        python_exe, "-m", "uvicorn", "app.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--log-level", "warning"
    ]
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(BASE_DIR))

    # Give backend a moment to boot
    time.sleep(2)

    # 3. Start Streamlit Frontend
    print("🖥️ [3/3] Starting Streamlit Frontend on http://localhost:8501...")
    frontend_cmd = [
        python_exe, "-m", "streamlit", "run", "app/frontend.py",
        "--server.headless", "false",
        "--browser.serverAddress", "localhost",
        "--server.port", "8501"
    ]

    print("\n" + "="*66)
    print("✅ All services active!")
    print("👉 Browser opening at: http://localhost:8501")
    print("👉 API Documentation:   http://127.0.0.1:8000/docs")
    print("👉 Press Ctrl+C in this terminal anytime to stop both servers.")
    print("="*66 + "\n")

    frontend_proc = None
    try:
        frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(BASE_DIR))
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down LogisticsUpdate AI...")
    finally:
        if frontend_proc and frontend_proc.poll() is None:
            frontend_proc.terminate()
        if backend_proc and backend_proc.poll() is None:
            backend_proc.terminate()
        print("✓ All servers cleanly stopped. Goodbye!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""NexusQuant single-command dev launcher.

Starts the Python backend (FastAPI, port 8004) and the Next.js frontend (port 3000)
together, streaming both logs with prefixes. Ctrl+C stops both cleanly.

    python run.py

The backend seeds a demo NSE universe through the real SPEC-004 pipeline and runs a gentle
live feed, so the UI is populated the moment it loads.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
BACKEND_PORT = os.environ.get("NEXUS_BACKEND_PORT", "8004")
FRONTEND_PORT = os.environ.get("NEXUS_FRONTEND_PORT", "3000")

# Make stdout tolerant of non-ASCII log lines from the child processes on Windows.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:
    pass

# ANSI colours render poorly in legacy Windows consoles — disable there.
if os.name == "nt":
    RESET = CYAN = MAGENTA = ""
else:
    RESET, CYAN, MAGENTA = "\033[0m", "\033[36m", "\033[35m"


def venv_python() -> str:
    """Prefer the project virtualenv interpreter so backend deps are importable."""
    candidates = [
        ROOT / ".venv" / "Scripts" / "python.exe",  # Windows
        ROOT / ".venv" / "bin" / "python",          # POSIX
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return sys.executable


def stream(proc: subprocess.Popen, prefix: str, color: str) -> None:
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(f"{color}{prefix}{RESET} {line.rstrip()}\n")
        sys.stdout.flush()


def start_backend() -> subprocess.Popen:
    env = {**os.environ, "PYTHONUNBUFFERED": "1", "NEXUS_LIVE_FEED": os.environ.get("NEXUS_LIVE_FEED", "1")}
    cmd = [
        venv_python(), "-m", "uvicorn", "main:app",
        "--app-dir", "apps/backend", "--port", BACKEND_PORT, "--reload",
    ]
    return subprocess.Popen(
        cmd, cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )


def start_frontend() -> subprocess.Popen:
    npm = shutil.which("npm") or "npm"
    if not (FRONTEND / "node_modules").exists():
        print(f"{MAGENTA}[web]{RESET} installing dependencies (first run)…")
        subprocess.run([npm, "install"], cwd=FRONTEND, shell=(os.name == "nt"), check=True)
    env = {**os.environ, "BACKEND_URL": f"http://localhost:{BACKEND_PORT}"}
    return subprocess.Popen(
        [npm, "run", "dev"], cwd=FRONTEND, env=env, shell=(os.name == "nt"),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )


def main() -> None:
    print("=" * 62)
    print("  NexusQuant - starting backend + frontend")
    print(f"  API   -> http://localhost:{BACKEND_PORT}      (docs: /docs)")
    print(f"  App   -> http://localhost:{FRONTEND_PORT}")
    print("  Ctrl+C to stop both.")
    print("=" * 62)

    backend = start_backend()
    frontend = start_frontend()
    procs = [backend, frontend]

    threads = [
        threading.Thread(target=stream, args=(backend, "[api]", CYAN), daemon=True),
        threading.Thread(target=stream, args=(frontend, "[web]", MAGENTA), daemon=True),
    ]
    for t in threads:
        t.start()

    def shutdown(*_a) -> None:
        for p in procs:
            if p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    try:
        while True:
            for p in procs:
                code = p.poll()
                if code is not None:
                    print(f"\nProcess exited with code {code}; shutting down the other.")
                    shutdown()
            for t in threads:
                t.join(timeout=0.4)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()

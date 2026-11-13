#!/usr/bin/env python3
"""SentinelAgent one-command launcher (Windows, macOS, Linux). Standard library only.

    python run.py setup          create backend/.venv, install backend + frontend dependencies
    python run.py                start backend (http://127.0.0.1:8000) and dashboard (http://127.0.0.1:5173)
    python run.py test           run the backend test suite
    python run.py experiment     run all four configurations on all splits and write reports/
    python run.py detector-eval  evaluate detectors on data/detector (add --pretrained for the model)
    python run.py ml-setup       optional: install CPU torch + transformers for the pretrained detector
    python run.py check          print what is installed and what is missing

Extra arguments after experiment / detector-eval / test are passed through, e.g.
    python run.py experiment --splits final_test --review-policy approve_all
"""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV = BACKEND / ".venv"
WINDOWS = os.name == "nt"
VENV_PYTHON = VENV / ("Scripts/python.exe" if WINDOWS else "bin/python")
MIN_PYTHON = (3, 11)


def say(message: str) -> None:
    print(f"[sentinelagent] {message}", flush=True)


def fail(message: str) -> None:
    say(f"ERROR: {message}")
    sys.exit(1)


def npm() -> str:
    found = shutil.which("npm.cmd" if WINDOWS else "npm") or shutil.which("npm")
    if not found:
        fail("npm not found. Install Node.js 20 or newer from https://nodejs.org and reopen the terminal.")
    return found


def run(cmd: list[str], cwd: Path) -> None:
    say(f"$ {' '.join(str(part) for part in cmd)}  (in {cwd.relative_to(ROOT) if cwd != ROOT else '.'})")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        fail(f"command failed with exit code {result.returncode}")


def backend_ready() -> bool:
    if not VENV_PYTHON.exists():
        return False
    return subprocess.run([str(VENV_PYTHON), "-c", "import fastapi, uvicorn, pydantic, pytest"], capture_output=True).returncode == 0


def frontend_ready() -> bool:
    return (FRONTEND / "node_modules" / ".bin").exists()


def setup() -> None:
    if sys.version_info < MIN_PYTHON:
        fail(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required, found {sys.version.split()[0]}")
    if not VENV_PYTHON.exists():
        say("creating backend/.venv")
        venv.EnvBuilder(with_pip=True).create(VENV)
    run([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip", "--quiet"], BACKEND)
    run([str(VENV_PYTHON), "-m", "pip", "install", "-r", "requirements-lock.txt", "--quiet"], BACKEND)
    run([npm(), "ci" if (FRONTEND / "package-lock.json").exists() else "install", "--no-audit", "--no-fund"], FRONTEND)
    say("setup complete. Next: python run.py")


def ensure_setup() -> None:
    if not backend_ready() or not frontend_ready():
        say("dependencies missing; running setup first")
        setup()


def _interrupt(signum, frame):  # noqa: ARG001
    raise KeyboardInterrupt


def start() -> None:
    ensure_setup()
    # Ctrl+C and editor "terminate task" (SIGTERM) both stop the two servers cleanly,
    # even if the shell started us with SIGINT ignored.
    signal.signal(signal.SIGINT, _interrupt)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _interrupt)
    say("starting backend on http://127.0.0.1:8000 (API docs at /docs)")
    group = {} if WINDOWS else {"start_new_session": True}  # own process group, so the whole tree can be stopped
    backend = subprocess.Popen([str(VENV_PYTHON), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"], cwd=BACKEND, **group)
    time.sleep(1.5)
    say("starting dashboard on http://127.0.0.1:5173")
    frontend = subprocess.Popen([npm(), "run", "dev"], cwd=FRONTEND, **group)
    say("press Ctrl+C to stop both")
    processes = [backend, frontend]
    try:
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
        say("a process exited; stopping the other")
    except KeyboardInterrupt:
        say("stopping")
    finally:
        for process in processes:
            if process.poll() is None:
                if WINDOWS:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
                else:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                if WINDOWS:
                    process.kill()
                else:
                    os.killpg(process.pid, signal.SIGKILL)


def backend_module(module: str, extra: list[str]) -> None:
    ensure_backend()
    run([str(VENV_PYTHON), "-m", module, *extra], BACKEND)


def ensure_backend() -> None:
    if not backend_ready():
        say("backend dependencies missing; running setup first")
        setup()


def ml_setup() -> None:
    ensure_backend()
    run([str(VENV_PYTHON), "-m", "pip", "install", "torch", "--index-url", "https://download.pytorch.org/whl/cpu"], BACKEND)
    run([str(VENV_PYTHON), "-m", "pip", "install", "-r", "requirements-ml.txt"], BACKEND)
    say("pretrained detector installed. Evaluate it: python run.py detector-eval --pretrained")
    say("Use it in experiments: set SENTINELAGENT_DETECTOR=pretrained, then python run.py experiment")


def check() -> None:
    say(f"python {sys.version.split()[0]} ({'ok' if sys.version_info >= MIN_PYTHON else 'too old'})")
    say(f"backend venv: {'ready' if backend_ready() else 'missing (python run.py setup)'}")
    say(f"npm: {shutil.which('npm') or 'missing'}")
    say(f"frontend node_modules: {'ready' if frontend_ready() else 'missing (python run.py setup)'}")
    if VENV_PYTHON.exists():
        has_ml = subprocess.run([str(VENV_PYTHON), "-c", "import transformers, torch"], capture_output=True).returncode == 0
        say(f"pretrained detector packages: {'installed' if has_ml else 'not installed (optional: python run.py ml-setup)'}")
    say(f"active detector: {os.environ.get('SENTINELAGENT_DETECTOR', 'keyword')}")


def main() -> None:
    command, extra = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("start", [])
    actions = {
        "setup": setup,
        "start": start,
        "test": lambda: backend_module("pytest", ["tests", "-q", *extra]),
        "experiment": lambda: backend_module("app.experiment_cli", extra),
        "detector-eval": lambda: backend_module("app.detector_eval", extra),
        "freeze-check": lambda: backend_module("app.freeze", extra),
        "ml-setup": ml_setup,
        "check": check,
    }
    if command in {"-h", "--help", "help"}:
        print(__doc__)
        return
    if command not in actions:
        print(__doc__)
        fail(f"unknown command '{command}'")
    actions[command]()


if __name__ == "__main__":
    main()

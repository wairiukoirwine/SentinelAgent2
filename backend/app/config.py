from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SCENARIO_FILE = DATA_DIR / "scenarios" / "scenarios.json"
DEFAULT_DB_PATH = DATA_DIR / "sentinelagent.sqlite3"
CONFIGURATIONS = {
    "baseline": {"name": "A · Baseline / No Gateway", "detector": False, "gateway": False},
    "content_only": {"name": "B · Content Check Only", "detector": True, "gateway": False},
    "gateway_only": {"name": "C · Policy Gateway Only", "detector": False, "gateway": True},
    "combined": {"name": "D · Combined Controls", "detector": True, "gateway": True},
}


def database_path() -> Path:
    configured = os.environ.get("SENTINELAGENT_DB")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_DB_PATH

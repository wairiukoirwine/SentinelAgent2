"""Final-test freeze: a SHA-256 fingerprint of the reserved final_test scenarios.

The fingerprint is recorded in data/scenarios/final_test_freeze.json before any
threshold or rule tuning. A test fails if final_test scenarios change afterwards,
so any change is visible and must be re-justified (see TECHNICAL_DECISIONS.md).
Run `python -m app.freeze --write` only when the team deliberately re-freezes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date

from .config import DATA_DIR, SCENARIO_FILE

FREEZE_FILE = DATA_DIR / "scenarios" / "final_test_freeze.json"


def final_test_fingerprint() -> tuple[str, int]:
    items = sorted((item for item in json.loads(SCENARIO_FILE.read_text(encoding="utf-8")) if item["split"] == "final_test"),
                   key=lambda item: item["scenario_id"])
    canonical = json.dumps(items, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest(), len(items)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="record a new freeze (deliberate re-freeze only)")
    args = parser.parse_args()
    digest, count = final_test_fingerprint()
    if args.write:
        FREEZE_FILE.write_text(json.dumps({"sha256": digest, "scenario_count": count, "frozen_on": date.today().isoformat(),
                                           "note": "Recorded before detector threshold selection and before any v2 experiment run."}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sha256": digest, "scenario_count": count}))


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path

from .models import Scenario
from .security import is_synthetic_recipient


def load_scenarios(path: Path) -> dict[str, Scenario]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    scenarios = [Scenario.model_validate(item) for item in raw]
    ids = [scenario.scenario_id for scenario in scenarios]
    if len(ids) != len(set(ids)):
        raise ValueError("Scenario identifiers must be unique")
    if any(not is_synthetic_recipient(recipient) for item in scenarios for recipient in item.approved_recipients):
        raise ValueError("Only synthetic example.test recipients are permitted")
    return {scenario.scenario_id: scenario for scenario in scenarios}

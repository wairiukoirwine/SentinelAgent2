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
    for item in scenarios:
        target = item.attack_target_recipient
        if target is None:
            if item.attack_goal is not None:
                raise ValueError(f"{item.scenario_id}: attack_goal requires attack_target_recipient")
            continue
        if not item.is_attack:
            raise ValueError(f"{item.scenario_id}: attack_target_recipient is only valid on attack scenarios")
        if not is_synthetic_recipient(target):
            raise ValueError(f"{item.scenario_id}: attack target must be a synthetic example.test address")
        goal = item.attack_goal or "exfiltrate_to_target"
        allowlisted = target in item.approved_recipients
        if goal == "exfiltrate_to_target" and allowlisted:
            raise ValueError(f"{item.scenario_id}: exfiltration target must not be on the allowlist")
        if goal == "leak_via_allowed_channel" and not allowlisted:
            raise ValueError(f"{item.scenario_id}: allowed-channel leak target must be an approved recipient")
    return {scenario.scenario_id: scenario for scenario in scenarios}

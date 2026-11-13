"""Experiment reviewer policies (TD-004 follow-up) and peak-memory measurement."""
from __future__ import annotations

import pytest

from app.config import SCENARIO_FILE
from app.database import Database
from app.engine import SimulationEngine, run_experiment
from app.scenarios import load_scenarios


@pytest.fixture
def engine(tmp_path):
    return SimulationEngine(Database(tmp_path / "policy.sqlite3"), load_scenarios(SCENARIO_FILE))


def _rows(engine, policy, ids):
    selected = [engine.scenarios[item] for item in ids]
    experiment = run_experiment(engine, selected, ["gateway_only"], review_policy=policy)
    with engine.database.connect() as connection:
        import json
        stored = json.loads(connection.execute("SELECT results_json FROM experiments WHERE experiment_id=?", (experiment["experiment_id"],)).fetchone()[0])
    return {row["scenario"]["scenario_id"]: row for row in stored["results"]}, experiment


def test_pending_policy_leaves_review_unexecuted(engine):
    rows, _ = _rows(engine, "pending", ["val_review_internal"])
    assert rows["val_review_internal"]["control_decision"] == "REVIEW"
    assert rows["val_review_internal"]["mock_execution"] is None
    assert rows["val_review_internal"]["approval_status"] == "pending"


def test_approve_all_executes_reviews_including_leaks(engine):
    rows, _ = _rows(engine, "approve_all", ["val_review_internal", "val_leak_allowed_channel"])
    assert rows["val_review_internal"]["task_completed"] is True
    assert rows["val_leak_allowed_channel"]["unsafe_execution"] is True  # careless reviewer lets the leak out


def test_reject_all_never_executes_reviews(engine):
    rows, experiment = _rows(engine, "reject_all", ["val_review_internal", "val_leak_allowed_channel"])
    assert all(row["mock_execution"] is None for row in rows.values())
    assert all(row["approval_status"] == "rejected" for row in rows.values())
    assert experiment["review_policy"] == "reject_all"


def test_peak_memory_is_measured(engine):
    _, experiment = _rows(engine, "pending", ["val_normal_summary"])
    aggregate = next(iter(experiment["aggregates"].values()))
    assert aggregate["peak_memory_mb"] is not None and aggregate["peak_memory_mb"] > 0


def test_unknown_policy_rejected(engine):
    with pytest.raises(ValueError):
        run_experiment(engine, [engine.scenarios["val_normal_summary"]], ["baseline"], review_policy="maybe")

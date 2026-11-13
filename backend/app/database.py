from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    run_id TEXT PRIMARY KEY, scenario_id TEXT NOT NULL, configuration_id TEXT NOT NULL,
                    status TEXT NOT NULL, result_json TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS proposed_actions (
                    action_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES simulation_runs(run_id),
                    payload_json TEXT NOT NULL, gateway_json TEXT, status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id TEXT PRIMARY KEY, action_id TEXT NOT NULL UNIQUE REFERENCES proposed_actions(action_id),
                    approved INTEGER NOT NULL, reviewer TEXT NOT NULL, recorded_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS mock_executions (
                    execution_id TEXT PRIMARY KEY, action_id TEXT NOT NULL UNIQUE REFERENCES proposed_actions(action_id),
                    payload_json TEXT NOT NULL, executed_at TEXT NOT NULL, simulated INTEGER NOT NULL CHECK(simulated = 1)
                );
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY, configuration_ids_json TEXT NOT NULL,
                    splits_json TEXT NOT NULL, results_json TEXT NOT NULL, metrics_json TEXT NOT NULL,
                    started_at TEXT NOT NULL, finished_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES simulation_runs(run_id),
                    scenario_id TEXT NOT NULL, configuration_id TEXT NOT NULL, event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL, event_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS audit_run_idx ON audit_events(run_id);
                CREATE INDEX IF NOT EXISTS audit_scenario_idx ON audit_events(scenario_id);
                CREATE INDEX IF NOT EXISTS audit_type_idx ON audit_events(event_type);
                """
            )


def encode(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def decode(value: str) -> Any:
    return json.loads(value)

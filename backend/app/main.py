from __future__ import annotations

import csv
import io
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import __version__
from .config import CONFIGURATIONS, SCENARIO_FILE, database_path
from .database import Database, decode, encode
from .detectors import detector_status
from .engine import SimulationEngine, run_experiment
from .metrics import summarize
from .models import ApprovalRequest, ExperimentRequest, Scenario, SimulateRequest
from .scenarios import load_scenarios


def create_app(db_path: str | Path | None = None, scenario_file: str | Path | None = None) -> FastAPI:
    scenarios = load_scenarios(Path(scenario_file or SCENARIO_FILE))
    database = Database(db_path or database_path())
    engine = SimulationEngine(database, scenarios)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        database.initialize()
        yield

    app = FastAPI(title="SentinelAgent Local Prototype", version=__version__, description="Synthetic, local-only prompt-injection security research simulator.", lifespan=lifespan)
    app.state.database = database
    app.state.scenarios = scenarios
    app.state.engine = engine
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    @app.get("/health")
    def health():
        return {"status": "ok", "version": __version__, "storage": "sqlite", "mock_tools_only": True, "detector": detector_status()}

    @app.get("/api/configurations")
    def configurations():
        return [{"configuration_id": key, **value} for key, value in CONFIGURATIONS.items()]

    @app.get("/api/overview")
    def overview():
        with database.connect() as connection:
            simulation_count = connection.execute("SELECT COUNT(*) AS count FROM simulation_runs").fetchone()["count"]
            experiment_count = connection.execute("SELECT COUNT(*) AS count FROM experiments").fetchone()["count"]
            pending_count = connection.execute("SELECT COUNT(*) AS count FROM proposed_actions WHERE status='pending'").fetchone()["count"]
            decision_rows = connection.execute("SELECT event_json FROM audit_events WHERE event_type='gateway_evaluated'").fetchall()
            run_rows = connection.execute("SELECT result_json FROM simulation_runs").fetchall()
        decisions = {"ALLOW": 0, "BLOCK": 0, "REVIEW": 0}
        for row in decision_rows:
            event = decode(row["event_json"])
            decision = event.get("detail", {}).get("decision")
            if decision in decisions:
                decisions[decision] += 1
        unsafe_count = sum(bool(decode(row["result_json"]).get("unsafe_execution")) for row in run_rows)
        return {"scenario_count": len(scenarios), "simulation_run_count": simulation_count,
                "experiment_count": experiment_count, "pending_approval_count": pending_count,
                "unsafe_execution_count": unsafe_count, "gateway_decision_counts": decisions}

    @app.get("/api/scenarios")
    def list_scenarios(category: str | None = None, split: str | None = None):
        rows = list(scenarios.values())
        return [item.model_dump() for item in rows if (category is None or item.category == category) and (split is None or item.split == split)]

    @app.get("/api/scenarios/{scenario_id}")
    def get_scenario(scenario_id: str):
        item = scenarios.get(scenario_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Scenario not found")
        return item.model_dump()

    @app.post("/api/simulate")
    def simulate(request: SimulateRequest):
        try:
            return engine.simulate(request.scenario_id, request.configuration_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc).strip("'")) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Simulation failed safely: {type(exc).__name__}") from exc

    @app.get("/api/approvals/pending")
    def pending_approvals():
        with database.connect() as connection:
            rows = connection.execute("SELECT action_id, run_id, payload_json, gateway_json FROM proposed_actions WHERE status='pending' ORDER BY rowid DESC").fetchall()
        return [{"action_id": row["action_id"], "run_id": row["run_id"], "action": decode(row["payload_json"]), "gateway": decode(row["gateway_json"] or "{}") } for row in rows]

    @app.post("/api/approvals/{action_id}")
    def decide_approval(action_id: str, request: ApprovalRequest):
        try:
            return engine.approve(action_id, request.approved, request.reviewer)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc).strip("'")) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/experiments/run")
    def experiments_run(request: ExperimentRequest):
        if len(set(request.configuration_ids)) != len(request.configuration_ids):
            raise HTTPException(status_code=422, detail="Configuration identifiers must be unique")
        selected = list(scenarios.values())
        if request.scenario_ids is not None:
            missing = sorted(set(request.scenario_ids) - set(scenarios))
            if missing:
                raise HTTPException(status_code=404, detail=f"Unknown scenario identifier: {missing[0]}")
            selected = [scenarios[item] for item in request.scenario_ids]
        selected = [item for item in selected if item.split in request.splits]
        if not selected:
            raise HTTPException(status_code=422, detail="Selection contains no scenarios")
        result = run_experiment(engine, selected, request.configuration_ids, review_policy=request.review_policy)
        return result

    @app.get("/api/experiments")
    def experiments_list():
        with database.connect() as connection:
            rows = connection.execute("SELECT experiment_id, configuration_ids_json, splits_json, metrics_json, started_at, finished_at FROM experiments ORDER BY started_at DESC").fetchall()
        items = []
        for row in rows:
            aggregates = decode(row["metrics_json"])
            first = next(iter(aggregates.values()), {})
            items.append({"experiment_id": row["experiment_id"], "configuration_ids": decode(row["configuration_ids_json"]), "splits": decode(row["splits_json"]),
                          "review_policy": first.get("review_policy", "pending"), "metrics_version": first.get("metrics_version", "1"),
                          "started_at": row["started_at"], "finished_at": row["finished_at"]})
        return items

    @app.get("/api/experiments/{experiment_id}")
    def experiment_detail(experiment_id: str):
        with database.connect() as connection:
            row = connection.execute("SELECT * FROM experiments WHERE experiment_id=?", (experiment_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return {"experiment_id": row["experiment_id"], "configuration_ids": decode(row["configuration_ids_json"]), "splits": decode(row["splits_json"]), "started_at": row["started_at"], "finished_at": row["finished_at"], **decode(row["results_json"]), "aggregates": decode(row["metrics_json"])}

    @app.get("/api/analytics")
    def analytics():
        with database.connect() as connection:
            rows = connection.execute("SELECT experiment_id, metrics_json FROM experiments ORDER BY started_at DESC").fetchall()
        return [{"experiment_id": row["experiment_id"], **decode(row["metrics_json"])} for row in rows]

    @app.get("/api/audit-logs")
    def audit_logs(query: str | None = None, run_id: str | None = None, scenario_id: str | None = None,
                   event_type: str | None = None, configuration_id: str | None = None,
                   limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
        clauses, params = [], []
        for column, value in (("run_id", run_id), ("scenario_id", scenario_id), ("event_type", event_type), ("configuration_id", configuration_id)):
            if value:
                clauses.append(f"{column}=?")
                params.append(value)
        if query:
            clauses.append("event_json LIKE ?")
            params.append(f"%{query}%")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with database.connect() as connection:
            rows = connection.execute(f"SELECT event_json FROM audit_events{where} ORDER BY timestamp DESC LIMIT ? OFFSET ?", (*params, limit, offset)).fetchall()
            count = connection.execute(f"SELECT COUNT(*) AS count FROM audit_events{where}", params).fetchone()["count"]
        return {"items": [decode(row["event_json"]) for row in rows], "total": count, "limit": limit, "offset": offset}

    @app.get("/api/exports/experiments/{experiment_id}")
    def export_experiment(experiment_id: str):
        with database.connect() as connection:
            row = connection.execute("SELECT results_json FROM experiments WHERE experiment_id=?", (experiment_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        results = decode(row["results_json"])["results"]
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(["run_id", "scenario_id", "split", "category", "configuration_id", "expected_detector_label", "observed_detector_label", "detector_method", "detector_score", "detector_threshold", "gateway_decision", "control_decision", "mock_executed", "unsafe_execution", "task_completed", "decision_latency_ms", "cpu_time_ms"])
        for item in results:
            detector = item.get("detector_result") or {}
            writer.writerow([item["run_id"], item["scenario"]["scenario_id"], item["scenario"]["split"], item["scenario"]["category"], item["configuration_id"], item["scenario"]["expected_detector_label"], detector.get("label", "disabled"), detector.get("method", "disabled"), detector.get("score", ""), detector.get("threshold", ""), item.get("gateway_result", {}).get("decision") if item.get("gateway_result") else "not_enabled", item.get("control_decision") or "unprotected", bool(item.get("mock_execution")), item["unsafe_execution"], item["task_completed"], item["decision_latency_ms"], item["cpu_time_ms"]])
        filename = f"sentinelagent-{experiment_id}.csv"
        return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    return app


app = create_app()

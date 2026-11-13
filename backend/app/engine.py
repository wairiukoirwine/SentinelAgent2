from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from .config import CONFIGURATIONS
from .database import Database, decode, encode
from .metrics import is_attack_success, summarize
from .models import DetectorResult, GatewayResult, Scenario, SimulationResult
from .agent import read_instructions, task_email_request
from .security import check_content, evaluate_gateway, evaluate_read, is_synthetic_recipient


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SimulationEngine:
    def __init__(self, database: Database, scenarios: dict[str, Scenario]):
        self.database = database
        self.scenarios = scenarios

    def simulate(self, scenario_id: str, configuration_id: str) -> dict[str, Any]:
        if scenario_id not in self.scenarios:
            raise KeyError("Scenario not found")
        if configuration_id not in CONFIGURATIONS:
            raise ValueError("Unknown experiment configuration")
        scenario = self.scenarios[scenario_id]
        config = CONFIGURATIONS[configuration_id]
        run_id = new_id("run")
        started = utc_now()
        start_cpu = time.process_time()
        decision_start = time.perf_counter_ns()
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO simulation_runs VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_id, scenario_id, configuration_id, "running", "{}", started, started),
            )

        self._audit(run_id, scenario, configuration_id, "simulation_started", {"configuration": config["name"]})
        read_call = {"tool_name": "read_document", "document_id": scenario.document_id, "run_id": run_id}
        self._audit(run_id, scenario, configuration_id, "document_read_requested", {"document_id": scenario.document_id})
        read_gateway = None
        if config["gateway"]:
            try:
                read_gateway = evaluate_read(read_call, scenario)
            except Exception as exc:  # fail closed
                read_gateway = GatewayResult(decision="BLOCK", reason_code="gateway_failure", reason=f"Read gate failed ({type(exc).__name__}).", policy_rule_id="FAIL-CLOSED", approval_required=False, approval_status="not_required", execution_permitted=False)
            self._audit(run_id, scenario, configuration_id, "read_gateway_evaluated", read_gateway.model_dump())
        document = None
        if read_gateway is None or read_gateway.execution_permitted:
            document = self._read_document(read_call["document_id"])
            self._audit(run_id, scenario, configuration_id, "document_read_completed", {"document_trust": "untrusted", "characters": len(document)})

        detector = None
        if config["detector"] and document is not None:
            try:
                if not callable(check_content):
                    raise RuntimeError("Detector is unavailable")
                detector = check_content(document)
            except Exception as exc:
                detector = DetectorResult(score=0, is_suspicious=True, label="suspicious", reason="Detector failed; protected execution fails closed.", error=type(exc).__name__)
                self._audit(run_id, scenario, configuration_id, "detector_failed", {"error": type(exc).__name__})
        if detector is not None:
            self._audit(run_id, scenario, configuration_id, "detector_evaluated", detector.model_dump())
        action = self._propose_action(scenario, document, run_id) if document is not None else None
        action_id = action["action_id"] if action else None
        if action:
            self._audit(run_id, scenario, configuration_id, "action_proposed", self._action_summary(action))

        gateway = None
        control_decision = None
        execute = False
        if action is not None:
            if config["gateway"]:
                try:
                    if not callable(evaluate_gateway):
                        raise RuntimeError("Gateway is unavailable")
                    gateway = evaluate_gateway(action, scenario, detector, config["detector"])
                except Exception as exc:
                    gateway = GatewayResult(decision="BLOCK", reason_code="gateway_failure", reason=f"Gateway failed ({type(exc).__name__}); protected execution is denied.", policy_rule_id="FAIL-CLOSED", approval_required=False, approval_status="not_required", execution_permitted=False)
                    self._audit(run_id, scenario, configuration_id, "gateway_failed", {"error": type(exc).__name__})
                control_decision = gateway.decision
                execute = gateway.execution_permitted
                self._audit(run_id, scenario, configuration_id, "gateway_evaluated", gateway.model_dump())
                if gateway.decision == "REVIEW":
                    self._audit(run_id, scenario, configuration_id, "approval_requested", {"action_id": action_id, "status": "pending"})
            elif config["detector"]:
                if detector is None or detector.error or detector.is_suspicious:
                    control_decision = "BLOCK"
                    self._audit(run_id, scenario, configuration_id, "content_control_blocked", {"reason": "Content-only configuration blocks suspicious or unavailable detector output."})
                else:
                    control_decision = "ALLOW"
                    execute = True
                    self._audit(run_id, scenario, configuration_id, "content_control_passed", {"reason": "Content-only configuration found no configured lexical indicator."})
            else:
                execute = True
                self._audit(run_id, scenario, configuration_id, "baseline_unprotected", {"reason": "Baseline is intentionally unprotected and isolated to mock tools."})
        elif config["gateway"] and config["detector"] and detector is None:
            control_decision = "BLOCK"

        decision_latency_ms = (time.perf_counter_ns() - decision_start) / 1_000_000
        if action:
            with self.database.connect() as connection:
                connection.execute(
                    "INSERT INTO proposed_actions(action_id, run_id, payload_json, gateway_json, status) VALUES (?, ?, ?, ?, ?)",
                    (action_id, run_id, encode(action), encode(gateway.model_dump()) if gateway else None,
                     "pending" if gateway and gateway.decision == "REVIEW" else "proposed"),
                )
        if action and execute:
            self._audit(run_id, scenario, configuration_id, "mock_execution_attempted", {"action_id": action_id, "tool_name": "send_email"})
        execution = self._mock_send_email(action) if action and execute else None
        if action:
            status = "executed" if execution else ("pending" if gateway and gateway.decision == "REVIEW" else "blocked")
            with self.database.connect() as connection:
                connection.execute("UPDATE proposed_actions SET status=? WHERE action_id=?", (status, action_id))
            if execution:
                self._audit(run_id, scenario, configuration_id, "mock_execution_completed", execution)

        task_completed = bool(execution) if scenario.task_requires_action else (action is None or scenario.is_attack)
        unsafe = is_attack_success(scenario, execution)
        result = SimulationResult(
            run_id=run_id,
            scenario=scenario,
            configuration_id=configuration_id,
            configuration_name=config["name"],
            read_gateway_result=read_gateway,
            detector_result=detector,
            proposed_action=action,
            gateway_result=gateway,
            control_decision=control_decision,
            mock_execution=execution,
            approval_status=gateway.approval_status if gateway else ("not_required" if execution else "not_applicable"),
            task_completed=task_completed,
            unsafe_execution=unsafe,
            decision_latency_ms=round(decision_latency_ms, 6),
            cpu_time_ms=round((time.process_time() - start_cpu) * 1000, 6),
        ).model_dump(mode="json")
        self._audit(run_id, scenario, configuration_id, "simulation_completed", {"task_completed": task_completed, "unsafe_execution": unsafe})
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE simulation_runs SET status=?, result_json=?, finished_at=? WHERE run_id=?",
                ("completed", encode(result), utc_now(), run_id),
            )
        return result

    def approve(self, action_id: str, approved: bool, reviewer: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM proposed_actions WHERE action_id=?", (action_id,)).fetchone()
            if row is None:
                raise KeyError("Review action not found")
            if row["status"] != "pending":
                raise ValueError("Action is no longer pending review")
            gateway = decode(row["gateway_json"] or "{}")
            if gateway.get("decision") != "REVIEW" or gateway.get("approval_status") != "pending":
                raise ValueError("Action does not have a pending REVIEW decision")
            try:
                connection.execute(
                    "INSERT INTO approvals VALUES (?, ?, ?, ?, ?)",
                    (new_id("approval"), action_id, int(approved), reviewer, utc_now()),
                )
            except Exception as exc:
                raise ValueError("An approval decision has already been recorded") from exc
            connection.execute("UPDATE proposed_actions SET status='processing' WHERE action_id=?", (action_id,))
            payload = decode(row["payload_json"])
            result_row = connection.execute("SELECT result_json FROM simulation_runs WHERE run_id=?", (row["run_id"],)).fetchone()
            result = decode(result_row["result_json"])
            scenario = self.scenarios[result["scenario"]["scenario_id"]]
            status = "approved" if approved else "rejected"
            gateway["approval_status"] = status
            gateway["execution_permitted"] = bool(approved)
            result["approval_status"] = status
            result["gateway_result"] = gateway
        self._audit(row["run_id"], scenario, result["configuration_id"], "approval_recorded", {"action_id": action_id, "approved": approved, "reviewer": reviewer, "simulated_reviewer": True})
        if approved:
            self._audit(row["run_id"], scenario, result["configuration_id"], "mock_execution_attempted", {"action_id": action_id, "tool_name": "send_email"})
        execution = self._mock_send_email(payload) if approved else None
        result["mock_execution"] = execution
        result["task_completed"] = bool(execution) if scenario.task_requires_action else (not scenario.is_attack)
        result["unsafe_execution"] = is_attack_success(scenario, execution)
        with self.database.connect() as connection:
            connection.execute("UPDATE proposed_actions SET status=?, gateway_json=? WHERE action_id=?", ("executed" if approved else "rejected", encode(gateway), action_id))
            connection.execute("UPDATE simulation_runs SET result_json=?, finished_at=? WHERE run_id=?", (encode(result), utc_now(), row["run_id"]))
        if execution:
            self._audit(row["run_id"], scenario, result["configuration_id"], "mock_execution_completed", execution)
        return {"action_id": action_id, "approved": approved, "approval_status": status, "execution": execution, "run_id": row["run_id"]}

    def _read_document(self, document_id: str) -> str:
        for scenario in self.scenarios.values():
            if scenario.document_id == document_id:
                return scenario.document_content
        raise KeyError("Document not found in the synthetic scenario store")

    def _propose_action(self, scenario: Scenario, document: str, run_id: str) -> dict[str, Any] | None:
        """Turn the agent's reading of the document plus the trusted task into at most one proposal.

        A document redirect instruction wins over the user's own request (worst-case
        gullible agent). The trusted task only authorises addresses it names itself.
        """
        instructions = read_instructions(document)
        task_addresses = task_email_request(scenario.user_task)
        if instructions.redirect_recipient:
            recipient = instructions.redirect_recipient
            source = "untrusted_document"
        elif task_addresses:
            recipient = task_addresses[0]
            source = "trusted_user_task"
        else:
            return None
        injected_disclosure = instructions.disclosure_requested
        return {
            "action_id": new_id("action"),
            "run_id": run_id,
            "scenario_id": scenario.scenario_id,
            "tool_name": "send_email",
            "recipient": recipient,
            "subject": f"Synthetic summary: {scenario.name}",
            "body": "Synthetic demonstration payload." + (" Includes content the document asked to disclose." if injected_disclosure else ""),
            "body_scope": "summary_with_injected_disclosure" if injected_disclosure else "summary",
            "data_label": scenario.data_label,
            "user_task": scenario.user_task,
            "approved_recipients": list(scenario.approved_recipients),
            "source": source,
            "agent_evidence": list(instructions.evidence),
            "user_task_authorized": recipient.lower() in task_addresses,
        }

    def _mock_send_email(self, action: dict[str, Any]) -> dict[str, Any]:
        if action.get("tool_name") != "send_email" or not isinstance(action.get("recipient"), str):
            raise ValueError("Unknown or malformed mock-tool action")
        recipient = action["recipient"]
        if not is_synthetic_recipient(recipient):
            raise ValueError("Only synthetically addressed mock emails are accepted")
        execution = {"execution_id": new_id("mock"), "action_id": action["action_id"], "tool_name": "send_email", "recipient": recipient, "data_label": action["data_label"], "body_scope": action.get("body_scope", "summary"), "simulated": True, "network_used": False, "result": "Recorded locally; no email was sent."}
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO mock_executions VALUES (?, ?, ?, ?, 1)",
                (execution["execution_id"], action["action_id"], encode(execution), utc_now()),
            )
        return execution

    def _audit(self, run_id: str, scenario: Scenario, config_id: str, event_type: str, detail: dict[str, Any]) -> None:
        event = {"event_id": new_id("event"), "run_id": run_id, "scenario_id": scenario.scenario_id,
                 "timestamp": utc_now(), "event_type": event_type, "configuration_id": config_id,
                 "detail": detail}
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?, ?)",
                (event["event_id"], run_id, scenario.scenario_id, config_id, event_type, event["timestamp"], encode(event)),
            )

    @staticmethod
    def _action_summary(action: dict) -> dict:
        return {key: action[key] for key in ("action_id", "tool_name", "recipient", "data_label", "body_scope", "source", "user_task_authorized") if key in action}


def run_experiment(engine: SimulationEngine, scenarios: list[Scenario], configuration_ids: list[str]) -> dict[str, Any]:
    experiment_id = new_id("experiment")
    started = utc_now()
    results: list[dict] = []
    aggregates: dict[str, dict] = {}
    for configuration_id in configuration_ids:
        for split in ("development", "validation", "final_test"):
            selected = [scenario for scenario in scenarios if scenario.split == split]
            if not selected:
                continue
            rows = [engine.simulate(scenario.scenario_id, configuration_id) for scenario in selected]
            results.extend(rows)
            aggregates[f"{configuration_id}:{split}"] = {"configuration_id": configuration_id, "split": split, **summarize(rows)}
    finished = utc_now()
    with engine.database.connect() as connection:
        connection.execute(
            "INSERT INTO experiments VALUES (?, ?, ?, ?, ?, ?, ?)",
            (experiment_id, encode(configuration_ids), encode(sorted({scenario.split for scenario in scenarios})),
             encode({"results": results, "aggregates": aggregates}), encode(aggregates), started, finished),
        )
    return {"experiment_id": experiment_id, "configuration_ids": configuration_ids,
            "scenario_count": len(results), "started_at": started, "finished_at": finished,
            "aggregates": aggregates}

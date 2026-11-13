from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ConfigurationId = Literal["baseline", "content_only", "gateway_only", "combined"]
Decision = Literal["ALLOW", "BLOCK", "REVIEW"]


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    name: str
    category: str
    split: Literal["development", "validation", "final_test"]
    user_task: str
    document_id: str
    document_content: str
    document_trust: Literal["untrusted"] = "untrusted"
    data_label: Literal["public", "internal", "confidential"]
    approved_recipients: list[str]
    expected_detector_label: Literal["suspicious", "benign"]
    expected_gateway_decision: Decision | None = None
    expected_safe_outcome: str
    description: str
    tags: list[str] = Field(default_factory=list)
    is_attack: bool = False
    task_requires_action: bool = False
    # Trusted ground-truth label written by the scenario author (never parsed from
    # the document). The recipient the injected instruction tries to reach.
    # None for non-attacks and for attacks that request no tool action.
    attack_target_recipient: str | None = None
    # Trusted label: what the attacker wants. exfiltrate_to_target = mail reaches the
    # target address; leak_via_allowed_channel = injected disclosure rides inside an
    # email the user really asked for (target is then an approved recipient).
    attack_goal: Literal["exfiltrate_to_target", "leak_via_allowed_channel"] | None = None


class SimulateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    configuration_id: ConfigurationId


class ExperimentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    configuration_ids: list[ConfigurationId] = Field(min_length=1, max_length=4)
    splits: list[Literal["development", "validation", "final_test"]] = Field(default_factory=lambda: ["development"])
    scenario_ids: list[str] | None = None


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: bool
    reviewer: str = Field(min_length=1, max_length=80)


class DetectorResult(BaseModel):
    detector_name: str = "keyword-baseline"
    detector_version: str = "1.0"
    method: str = "transparent lexical rule set"
    score: float = Field(ge=0, le=1)
    is_suspicious: bool
    label: Literal["suspicious", "benign"]
    threshold: float = 0.75
    reason: str
    error: str | None = None


class GatewayResult(BaseModel):
    decision: Decision
    reason_code: str
    reason: str
    policy_rule_id: str
    approval_required: bool
    approval_status: Literal["not_required", "pending", "approved", "rejected"]
    execution_permitted: bool


class SimulationResult(BaseModel):
    run_id: str
    scenario: Scenario
    configuration_id: ConfigurationId
    configuration_name: str
    read_gateway_result: GatewayResult | None = None
    detector_result: DetectorResult | None
    proposed_action: dict[str, Any] | None
    gateway_result: GatewayResult | None
    control_decision: Decision | None
    mock_execution: dict[str, Any] | None
    approval_status: str
    task_completed: bool
    unsafe_execution: bool
    decision_latency_ms: float
    cpu_time_ms: float
    error: str | None = None


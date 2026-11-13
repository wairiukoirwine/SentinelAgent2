export type ConfigurationId = "baseline" | "content_only" | "gateway_only" | "combined";
export type Split = "development" | "validation" | "final_test";

export interface Scenario {
  scenario_id: string;
  name: string;
  category: string;
  split: Split;
  user_task: string;
  document_id: string;
  document_content: string;
  document_trust: "untrusted";
  data_label: "public" | "internal" | "confidential";
  approved_recipients: string[];
  expected_detector_label: "suspicious" | "benign";
  expected_gateway_decision: "ALLOW" | "BLOCK" | "REVIEW" | null;
  expected_safe_outcome: string;
  description: string;
  is_attack: boolean;
  task_requires_action: boolean;
  /** Trusted label: recipient the injection targets. Absent on older data. */
  attack_target_recipient?: string | null;
  attack_goal?: "exfiltrate_to_target" | "leak_via_allowed_channel" | null;
}

export interface Aggregate {
  configuration_id: ConfigurationId;
  split: Split;
  scenario_count: number;
  attack_trials: number;
  normal_trials: number;
  attack_success_rate: Metric;
  normal_task_completion_rate: Metric;
  false_block_rate: Metric;
  review_count: number;
  review_policy?: ReviewPolicy;
  /** Metrics v2 fields; optional because experiments stored before v2 lack them. */
  metrics_version?: string;
  non_action_attack_trials?: number;
  action_normal_trials?: number;
  normal_review_rate?: Metric;
  normal_pending_review_count?: number;
  attack_review_count?: number;
  average_decision_latency_ms: number | null;
  p95_decision_latency_ms: number | null;
  cpu_time_ms_total: number;
  peak_memory_mb: number | null;
  decision_counts: Record<string, number>;
}

export interface Metric {
  value: number | null;
  numerator: number;
  denominator: number;
}

export interface Simulation {
  run_id: string;
  scenario: Scenario;
  configuration_id: ConfigurationId;
  configuration_name: string;
  read_gateway_result?: GatewayResult | null;
  detector_result: { detector_name?: string; label: string; score: number; threshold?: number; reason: string; is_suspicious: boolean; error?: string } | null;
  proposed_action: { action_id: string; tool_name?: string; recipient: string; data_label: string; source: string; body_scope?: string; agent_evidence?: string[]; user_task_authorized: boolean } | null;
  gateway_result: GatewayResult | null;
  control_decision: string | null;
  mock_execution: { simulated: boolean; network_used: boolean; recipient: string; result: string } | null;
  approval_status: string;
  task_completed: boolean;
  unsafe_execution: boolean;
  decision_latency_ms: number;
  cpu_time_ms: number;
  review_policy?: ReviewPolicy;
  peak_memory_mb?: number | null;
}

export interface GatewayResult {
  decision: string;
  reason_code: string;
  reason: string;
  policy_rule_id: string;
  approval_status: string;
}

export type ReviewPolicy = "pending" | "approve_all" | "reject_all";

export interface ExperimentSummary {
  experiment_id: string;
  configuration_ids: ConfigurationId[];
  splits: Split[];
  review_policy: ReviewPolicy;
  metrics_version: string;
  started_at: string;
  finished_at: string;
}

export interface ExperimentDetail extends ExperimentSummary {
  results: Simulation[];
  aggregates: Record<string, Aggregate>;
}

export interface AuditEvent {
  event_id: string;
  run_id: string;
  scenario_id: string;
  timestamp: string;
  event_type: string;
  configuration_id: string;
  detail: Record<string, unknown>;
}

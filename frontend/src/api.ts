import type { Aggregate, AuditEvent, ConfigurationId, ExperimentDetail, ExperimentSummary, ReviewPolicy, Scenario, Simulation, Split } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export interface OverviewStats {
  scenario_count: number;
  simulation_run_count: number;
  experiment_count: number;
  pending_approval_count: number;
  unsafe_execution_count: number;
  gateway_decision_counts: { ALLOW: number; BLOCK: number; REVIEW: number };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; version: string; mock_tools_only: boolean; detector?: { active: string; threshold: number } }>("/health"),
  overview: () => request<OverviewStats>("/api/overview"),
  scenarios: (split?: string) => request<Scenario[]>(`/api/scenarios${split ? `?split=${encodeURIComponent(split)}` : ""}`),
  analytics: () => request<Array<{ experiment_id: string; [key: string]: Aggregate | string }>>("/api/analytics"),
  audits: (query = "") => request<{ items: AuditEvent[]; total: number }>(`/api/audit-logs?limit=100${query ? `&query=${encodeURIComponent(query)}` : ""}`),
  pending: () => request<Array<{ action_id: string; run_id: string; action: Simulation["proposed_action"]; gateway: Simulation["gateway_result"] }>>("/api/approvals/pending"),
  simulate: (scenario_id: string, configuration_id: ConfigurationId) => request<Simulation>("/api/simulate", { method: "POST", body: JSON.stringify({ scenario_id, configuration_id }) }),
  approve: (action_id: string, approved: boolean) => request<{ execution: Simulation["mock_execution"] }>(`/api/approvals/${action_id}`, { method: "POST", body: JSON.stringify({ approved, reviewer: "Local simulated reviewer" }) }),
  runExperiment: (configuration_ids: ConfigurationId[], splits: Split[], review_policy: ReviewPolicy = "pending") => request<{ experiment_id: string; scenario_count: number; aggregates: Record<string, Aggregate> }>("/api/experiments/run", { method: "POST", body: JSON.stringify({ configuration_ids, splits, review_policy }) }),
  experiments: () => request<ExperimentSummary[]>("/api/experiments"),
  experiment: (id: string) => request<ExperimentDetail>(`/api/experiments/${encodeURIComponent(id)}`),
  exportExperiment: async (id: string) => {
    const response = await fetch(`${API_URL}/api/exports/experiments/${id}`);
    if (!response.ok) throw new Error("CSV export failed");
    const blob = await response.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `sentinelagent-${id}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  },
};

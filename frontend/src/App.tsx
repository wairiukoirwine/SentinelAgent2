import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity, ArrowDownToLine, BookOpenText, Check, ChevronDown, CircleHelp, ClipboardList,
  FileSearch, FlaskConical, Gauge, LayoutDashboard, LockKeyhole, Mail, Menu, Play,
  RefreshCw, Search, ShieldAlert, ShieldCheck, ShieldX, TriangleAlert, X,
} from "lucide-react";
import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "./api";
import type { OverviewStats } from "./api";
import type { Aggregate, AuditEvent, ConfigurationId, Scenario, Simulation, Split } from "./types";

type Page = "Overview" | "Agent Simulator" | "Scenario Lab" | "Gateway Monitor" | "Experiments" | "Audit Logs";
const navItems: { title: Page; icon: typeof LayoutDashboard; caption: string }[] = [
  { title: "Overview", icon: LayoutDashboard, caption: "Research snapshot" },
  { title: "Agent Simulator", icon: Activity, caption: "Run a synthetic case" },
  { title: "Scenario Lab", icon: BookOpenText, caption: "Explore the corpus" },
  { title: "Gateway Monitor", icon: LockKeyhole, caption: "Review protected actions" },
  { title: "Experiments", icon: FlaskConical, caption: "Compare controls" },
  { title: "Audit Logs", icon: ClipboardList, caption: "Trace every decision" },
];
const configNames: Record<ConfigurationId, string> = {
  baseline: "A · Baseline / No Gateway",
  content_only: "B · Content Check Only",
  gateway_only: "C · Policy Gateway Only",
  combined: "D · Combined Controls",
};
const allConfigs = Object.keys(configNames) as ConfigurationId[];
const splitNames: Record<Split, string> = { development: "Development", validation: "Validation", final_test: "Final test" };

function App() {
  const [page, setPage] = useState<Page>("Overview");
  const [health, setHealth] = useState<{ status: string; version: string; mock_tools_only: boolean } | null>(null);
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [analytics, setAnalytics] = useState<Array<{ experiment_id: string; [key: string]: Aggregate | string }>>([]);
  const [audits, setAudits] = useState<AuditEvent[]>([]);
  const [pending, setPending] = useState<Array<{ action_id: string; run_id: string; action: Simulation["proposed_action"]; gateway: Simulation["gateway_result"] }>>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setError("");
    try {
      const [healthResult, overviewResult, scenarioResult, analyticsResult, auditResult, pendingResult] = await Promise.all([
        api.health(), api.overview(), api.scenarios(), api.analytics(), api.audits(), api.pending(),
      ]);
      setHealth(healthResult);
      setOverview(overviewResult);
      setScenarios(scenarioResult);
      setAnalytics(analyticsResult);
      setAudits(auditResult.items);
      setPending(pendingResult);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to connect to the local API.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  return (
    <div className="app-frame">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark"><ShieldCheck size={23} /></div>
          <div><strong>SentinelAgent</strong><span>LOCAL RESEARCH LAB</span></div>
        </div>
        <div className="workspace-label">WORKSPACE <span className="local-pill"><span /> Local only</span></div>
        <nav className="nav-list" aria-label="Main navigation">
          {navItems.map(({ title, icon: Icon, caption }) => (
            <button className={`nav-item ${page === title ? "active" : ""}`} key={title} onClick={() => setPage(title)}>
              <Icon size={17} strokeWidth={1.8} />
              <span className="nav-copy"><strong>{title}</strong><small>{caption}</small></span>
              {title === "Gateway Monitor" && pending.length > 0 && <span className="nav-count">{pending.length}</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="safe-box"><LockKeyhole size={16} /><div><strong>Mock tools only</strong><span>No external email or network calls</span></div><Check size={15} /></div>
          <div className="user-chip"><div className="avatar">SA</div><div><strong>Research workspace</strong><span>Prototype v{health?.version ?? "0.1.0"}</span></div><ChevronDown size={15} /></div>
        </div>
      </aside>

      <main className="main-shell">
        <header className="topbar">
          <div className="breadcrumbs"><span>SentinelAgent</span><span className="crumb-slash">/</span><strong>{page}</strong></div>
          <div className="topbar-right">
            <span className={`system-status ${health?.status === "ok" ? "online" : "offline"}`}><span />{health?.status === "ok" ? "API connected" : "API unavailable"}</span>
            <button className="icon-button" aria-label="Refresh data" onClick={() => void refresh()}><RefreshCw size={16} /></button>
            <div className="top-avatar">SA</div>
          </div>
        </header>
        <div className="content-wrap">
          {error && <div className="alert error-alert"><TriangleAlert size={17} /><span>{error} Start the backend locally and refresh.</span><button onClick={() => void refresh()}>Retry</button></div>}
          {loading ? <div className="loading-state"><span className="spinner" />Connecting to the local research API…</div> : (
            <>
              {page === "Overview" && <Overview health={health} overview={overview} scenarios={scenarios} audits={audits} analytics={analytics} onOpen={setPage} />}
              {page === "Agent Simulator" && <Simulator scenarios={scenarios} onChange={refresh} />}
              {page === "Scenario Lab" && <ScenarioLab scenarios={scenarios} />}
              {page === "Gateway Monitor" && <GatewayMonitor pending={pending} onChange={refresh} />}
              {page === "Experiments" && <Experiments analytics={analytics} onChange={refresh} />}
              {page === "Audit Logs" && <AuditLog initialEvents={audits} />}
            </>
          )}
        </div>
        <footer className="app-footer"><span><LockKeyhole size={13} /> Local synthetic research environment</span><span>DAI034 · Secure AI Applications</span></footer>
      </main>
    </div>
  );
}

function PageTitle({ eyebrow, title, description, actions }: { eyebrow: string; title: string; description: string; actions?: React.ReactNode }) {
  return <div className="page-title-row"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{actions}</div>;
}

function MetricCard({ label, value, sub, icon: Icon, tone = "cyan" }: { label: string; value: string; sub: string; icon: typeof Activity; tone?: string }) {
  return <article className="metric-card"><div className={`metric-icon ${tone}`}><Icon size={17} /></div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-sub">{sub}</div></article>;
}

function Overview({ health, overview, scenarios, audits, analytics, onOpen }: { health: AppPropsHealth; overview: OverviewStats | null; scenarios: Scenario[]; audits: AuditEvent[]; analytics: Array<{ experiment_id: string; [key: string]: Aggregate | string }>; onOpen: (page: Page) => void }) {
  const latest = analytics[0];
  const aggregates = latest ? Object.values(latest).filter((item): item is Aggregate => typeof item === "object" && item !== null && "configuration_id" in item) : [];
  const development = aggregates.filter((item) => item.split === "development");
  const attackRates = development.map((item) => ({ name: item.configuration_id.replace("_", " "), Attack: item.attack_success_rate.value ?? 0, "Normal completion": item.normal_task_completion_rate.value ?? 0 }));
  const runCount = overview?.simulation_run_count ?? 0;
  const finalMetrics = development.find((item) => item.configuration_id === "combined");
  return <>
    <PageTitle eyebrow="CAPSTONE SECURITY RESEARCH" title="Research overview" description="A local, deterministic view of prompt-injection defenses and their measured outcomes." actions={<button className="button secondary" onClick={() => onOpen("Experiments")}><FlaskConical size={16} /> Run experiment</button>} />
    <div className="hero-band"><div className="hero-orbit orbit-one" /><div className="hero-orbit orbit-two" /><div className="hero-content"><span className="hero-kicker"><span className="pulse-dot" /> LOCAL SIMULATION · MOCK TOOLS ONLY</span><h2>Defend the action.<br /><em>Measure the boundary.</em></h2><p>Explore how content checks and a policy gateway change simulated tool execution when documents carry untrusted instructions.</p><button className="button hero-button" onClick={() => onOpen("Agent Simulator")}>Open agent simulator <span>↗</span></button></div><div className="hero-shield"><ShieldCheck size={71} strokeWidth={1.1} /><span>POLICY<br />ENFORCED</span></div></div>
    <div className="metric-grid">
      <MetricCard label="SYNTHETIC SCENARIOS" value={String(scenarios.length)} sub="8 per labelled dataset split" icon={FileSearch} />
      <MetricCard label="SIMULATION RUNS" value={String(runCount)} sub="Persisted in the local audit trail" icon={Activity} tone="blue" />
      <MetricCard label="COMBINED ATTACK SUCCESS" value={finalMetrics ? `${finalMetrics.attack_success_rate.value ?? "—"}%` : "—"} sub={finalMetrics ? `${finalMetrics.attack_success_rate.numerator} of ${finalMetrics.attack_success_rate.denominator} attack trials` : "Run an experiment to calculate"} icon={ShieldX} tone="rose" />
      <MetricCard label="NORMAL TASK COMPLETION" value={finalMetrics ? `${finalMetrics.normal_task_completion_rate.value ?? "—"}%` : "—"} sub={finalMetrics ? `${finalMetrics.normal_task_completion_rate.numerator} of ${finalMetrics.normal_task_completion_rate.denominator} normal trials` : "No experiment results yet"} icon={ShieldCheck} tone="green" />
    </div>
    <div className="dashboard-grid">
      <section className="panel chart-panel"><div className="panel-heading"><div><h3>Control comparison</h3><p>{latest ? `Latest experiment · ${latest.experiment_id}` : "Run an experiment to populate measured results"}</p></div><button className="text-button" onClick={() => onOpen("Experiments")}>View experiments <span>→</span></button></div>{attackRates.length ? <div className="chart-wrap"><ResponsiveContainer width="100%" height={265}><BarChart data={attackRates} margin={{ top: 18, right: 12, bottom: 4, left: 2 }}><CartesianGrid stroke="#1d2937" vertical={false} /><XAxis dataKey="name" tick={{ fill: "#8a98a8", fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis domain={[0, 100]} tick={{ fill: "#68798a", fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={(value) => `${value}%`} /><Tooltip contentStyle={{ background: "#111c29", border: "1px solid #29394b", borderRadius: 10, color: "#e5edf5" }} formatter={(value) => [`${value}%`]} /><Bar dataKey="Attack" fill="#f26c72" radius={[4, 4, 0, 0]} barSize={22} /><Bar dataKey="Normal completion" fill="#36c9bc" radius={[4, 4, 0, 0]} barSize={22} /></BarChart></ResponsiveContainer><div className="chart-legend"><span><i className="legend-attack" /> Attack success rate</span><span><i className="legend-completion" /> Normal completion</span></div></div> : <EmptyState icon={FlaskConical} title="No measured results yet" text="Experiment results will appear here after a run." />}</section>
      <section className="panel status-panel"><div className="panel-heading"><div><h3>System status</h3><p>Prototype health and trust boundaries</p></div><span className="badge badge-green">{health?.status === "ok" ? "Operational" : "Unavailable"}</span></div><div className="status-list"><StatusRow icon={Activity} label="FastAPI service" value={health?.status === "ok" ? "Connected" : "Disconnected"} ok={health?.status === "ok"} /><StatusRow icon={Gauge} label="Local persistence" value="SQLite" ok /><StatusRow icon={Mail} label="Email tool" value="Mock only" ok /><StatusRow icon={ShieldCheck} label="External network actions" value="Disabled" ok /></div><div className="status-note"><CircleHelp size={15} /><span>The agent is a deterministic scenario simulator, not an LLM.</span></div></section>
    </div>
    <section className="panel decision-distribution"><div className="panel-heading"><div><h3>Gateway decision distribution</h3><p>Recorded gateway evaluations from persisted simulation runs</p></div></div><div className="decision-count-grid"><DecisionCount label="ALLOW" count={overview?.gateway_decision_counts.ALLOW ?? 0} tone="green" /><DecisionCount label="BLOCK" count={overview?.gateway_decision_counts.BLOCK ?? 0} tone="rose" /><DecisionCount label="REVIEW" count={overview?.gateway_decision_counts.REVIEW ?? 0} tone="amber" /></div></section>
    <section className="panel activity-panel"><div className="panel-heading"><div><h3>Recent audit activity</h3><p>Backend-confirmed events from this local instance</p></div><button className="text-button" onClick={() => onOpen("Audit Logs")}>Open audit log <span>→</span></button></div>{audits.length ? <div className="activity-list">{audits.slice(0, 5).map((event) => <ActivityRow key={event.event_id} event={event} />)}</div> : <EmptyState icon={ClipboardList} title="The audit trail is empty" text="Simulation and experiment events will be recorded here." />}</section>
  </>;
}

type AppPropsHealth = { status: string; version: string; mock_tools_only: boolean } | null;
function StatusRow({ icon: Icon, label, value, ok }: { icon: typeof Activity; label: string; value: string; ok: boolean }) { return <div className="status-row"><span className="status-row-icon"><Icon size={15} /></span><span>{label}</span><strong>{value}</strong><span className={ok ? "tiny-check" : "tiny-error"}>{ok ? <Check size={13} /> : <X size={13} />}</span></div>; }
function DecisionCount({ label, count, tone }: { label: string; count: number; tone: string }) { return <div className={`decision-count ${tone}`}><span>{label}</span><strong>{count}</strong><small>gateway decisions</small></div>; }

function Simulator({ scenarios, onChange }: { scenarios: Scenario[]; onChange: () => void }) {
  const [scenarioId, setScenarioId] = useState("");
  const [configuration, setConfiguration] = useState<ConfigurationId>("combined");
  const [result, setResult] = useState<Simulation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { if (!scenarioId && scenarios.length) setScenarioId(scenarios[0].scenario_id); }, [scenarios, scenarioId]);
  const selected = scenarios.find((item) => item.scenario_id === scenarioId);
  async function run() {
    if (!selected) return;
    setBusy(true); setError(""); setResult(null);
    try { setResult(await api.simulate(selected.scenario_id, configuration)); onChange(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Simulation failed"); }
    finally { setBusy(false); }
  }
  return <>
    <PageTitle eyebrow="CONTROLLED TOOL EXECUTION" title="Agent simulator" description="Inspect the trusted user task separately from document text, then review the backend’s proposed action and decision." />
    <div className="alert safety-alert"><ShieldCheck size={18} /><div><strong>Simulated actions only</strong><span>send_email writes a local event record. It never contacts a real recipient or email service.</span></div></div>
    <div className="sim-layout">
      <section className="panel sim-input-panel"><div className="panel-heading"><div><h3>Scenario input</h3><p>Scenario labels and policy fields are trusted backend data.</p></div><span className="step-number">01</span></div>
        <label className="field-label" htmlFor="scenario-select">Synthetic scenario</label><select id="scenario-select" className="select-control" value={scenarioId} onChange={(event) => { setScenarioId(event.target.value); setResult(null); }}><option value="" disabled>Select a scenario</option>{scenarios.map((item) => <option value={item.scenario_id} key={item.scenario_id}>[{splitNames[item.split]}] {item.name}</option>)}</select>
        {selected && <><div className="trusted-card"><div className="card-label"><ShieldCheck size={14} /> TRUSTED USER TASK</div><p>{selected.user_task}</p><div className="trust-meta"><span>Data label <strong className={`label-${selected.data_label}`}>{selected.data_label}</strong></span><span>Allowlist <strong>{selected.approved_recipients.join(", ") || "none"}</strong></span></div></div>
          <div className="untrusted-card"><div className="card-label"><TriangleAlert size={14} /> UNTRUSTED DOCUMENT <span className="doc-id">{selected.document_id}</span></div><pre>{selected.document_content}</pre></div></>}
        <label className="field-label" htmlFor="config-select">Experiment configuration</label><select id="config-select" className="select-control" value={configuration} onChange={(event) => setConfiguration(event.target.value as ConfigurationId)}>{allConfigs.map((item) => <option value={item} key={item}>{configNames[item]}</option>)}</select>
        <button className="button primary full-button" onClick={() => void run()} disabled={!selected || busy}>{busy ? <><span className="spinner small" /> Running scenario…</> : <><Play size={16} fill="currentColor" /> Run simulation</>}</button>
        {error && <div className="inline-error">{error}</div>}
      </section>
      <section className="panel sim-result-panel"><div className="panel-heading"><div><h3>Execution trace</h3><p>Results appear after the backend confirms the run</p></div><span className="step-number">02</span></div>
        {result ? <SimulationView result={result} /> : <div className="result-placeholder"><div className="placeholder-icon"><Activity size={25} /></div><h4>Ready to simulate</h4><p>Choose a scenario and configuration. The trace will show detection, gateway policy, approval state, and mock execution outcome.</p><div className="trace-steps"><span><i /> Read untrusted document</span><span><i /> Evaluate configured controls</span><span><i /> Record mock outcome</span></div></div>}
      </section>
    </div>
  </>;
}

function SimulationView({ result }: { result: Simulation }) {
  const decision = result.gateway_result?.decision ?? result.control_decision ?? "UNPROTECTED";
  const tone = decision === "BLOCK" ? "rose" : decision === "REVIEW" ? "amber" : decision === "ALLOW" ? "green" : "slate";
  return <div className="simulation-view"><div className={`decision-banner ${tone}`}><div className="decision-icon">{decision === "BLOCK" ? <ShieldX size={20} /> : decision === "REVIEW" ? <TriangleAlert size={20} /> : decision === "ALLOW" ? <ShieldCheck size={20} /> : <CircleHelp size={20} />}</div><div><span>CONTROL DECISION</span><strong>{decision === "UNPROTECTED" ? "Baseline · unprotected" : decision}</strong></div><span className="decision-time">{result.decision_latency_ms.toFixed(3)} ms</span></div>
    <div className="trace-card"><div className="trace-row"><span className="trace-mark done"><Check size={12} /></span><div><strong>Document read as untrusted</strong><small>{result.scenario.document_id} · {result.scenario.document_content.length} characters</small></div></div>
      <div className="trace-row"><span className={`trace-mark ${result.detector_result?.is_suspicious ? "warn" : result.detector_result ? "done" : "idle"}`}>{result.detector_result ? result.detector_result.is_suspicious ? <TriangleAlert size={12} /> : <Check size={12} /> : <span />}</span><div><strong>Content check {result.detector_result ? `· ${result.detector_result.label}` : "· disabled"}</strong><small>{result.detector_result ? `${result.detector_result.reason}${result.detector_result.error ? ` · ${result.detector_result.error}` : ""}` : "Detector is not enabled for this configuration."}</small></div></div>
      <div className="trace-row"><span className={`trace-mark ${result.proposed_action ? "done" : "idle"}`}>{result.proposed_action ? <Mail size={12} /> : <span />}</span><div><strong>{result.proposed_action ? "Mock action proposed" : "No tool action proposed"}</strong><small>{result.proposed_action ? `${result.proposed_action.recipient} · ${result.proposed_action.data_label} · source: ${result.proposed_action.source}` : "The simulated agent produced no send_email action."}</small></div></div>
      {result.gateway_result && <div className="trace-row"><span className={`trace-mark ${result.gateway_result.decision === "BLOCK" ? "bad" : result.gateway_result.decision === "REVIEW" ? "warn" : "done"}`}>{result.gateway_result.decision === "BLOCK" ? <X size={12} /> : result.gateway_result.decision === "REVIEW" ? <TriangleAlert size={12} /> : <Check size={12} />}</span><div><strong>Gateway · {result.gateway_result.policy_rule_id}</strong><small>{result.gateway_result.reason}</small></div></div>}
      <div className="trace-row last"><span className={`trace-mark ${result.mock_execution ? "done" : "idle"}`}>{result.mock_execution ? <Check size={12} /> : <span />}</span><div><strong>{result.mock_execution ? "Simulated email recorded" : result.approval_status === "pending" ? "Execution waiting for approval" : "No email executed"}</strong><small>{result.mock_execution ? `${result.mock_execution.recipient} · ${result.mock_execution.result}` : "No real email or external network call was made."}</small></div></div></div>
    <div className="result-foot"><span>Run ID <code>{result.run_id}</code></span><span>Task {result.task_completed ? "completed" : "not completed"}</span><span className={result.unsafe_execution ? "text-rose" : "text-green"}>{result.unsafe_execution ? "Unsafe execution" : "No unsafe execution"}</span></div>
  </div>;
}

function ScenarioLab({ scenarios }: { scenarios: Scenario[] }) {
  const [split, setSplit] = useState("all");
  const [category, setCategory] = useState("all");
  const categories = useMemo(() => [...new Set(scenarios.map((item) => item.category))].sort(), [scenarios]);
  const visible = scenarios.filter((item) => (split === "all" || item.split === split) && (category === "all" || item.category === category));
  return <><PageTitle eyebrow="SYNTHETIC DATASET" title="Scenario lab" description="24 labelled synthetic scenarios across separate development, validation, and reserved final-test splits." /><div className="alert info-alert"><BookOpenText size={17} /><div><strong>Final-test split is reserved</strong><span>Thresholds and policy rules should be tuned on development data and checked on validation data. No scenario editor is exposed here.</span></div></div>
    <section className="panel table-panel"><div className="filter-row"><div><span className="result-count">{visible.length} scenarios</span><span className="filter-caption">Synthetic corpus · read only</span></div><div className="filters"><select className="small-select" value={split} onChange={(event) => setSplit(event.target.value)}><option value="all">All splits</option>{Object.keys(splitNames).map((item) => <option key={item} value={item}>{splitNames[item as Split]}</option>)}</select><select className="small-select" value={category} onChange={(event) => setCategory(event.target.value)}><option value="all">All categories</option>{categories.map((item) => <option key={item}>{item}</option>)}</select></div></div>
      <div className="table-scroll"><table><thead><tr><th>Scenario</th><th>Category</th><th>Split</th><th>Data label</th><th>Expected outcome</th><th>Case</th></tr></thead><tbody>{visible.map((item) => <tr key={item.scenario_id}><td><strong>{item.name}</strong><small>{item.scenario_id} · {item.description}</small></td><td><span className="category-pill">{item.category.replaceAll("_", " ")}</span></td><td><SplitBadge split={item.split} /></td><td><span className={`label-${item.data_label}`}>{item.data_label}</span></td><td>{item.expected_gateway_decision ? <DecisionBadge decision={item.expected_gateway_decision} /> : <span className="muted">No tool action</span>}</td><td>{item.is_attack ? <span className="case-attack"><ShieldAlert size={13} /> Attack</span> : <span className="case-normal">Normal</span>}</td></tr>)}</tbody></table></div>
    </section></>;
}

function GatewayMonitor({ pending, onChange }: { pending: Array<{ action_id: string; run_id: string; action: Simulation["proposed_action"]; gateway: Simulation["gateway_result"] }>; onChange: () => void }) {
  const [busyId, setBusyId] = useState("");
  const [message, setMessage] = useState("");
  async function decide(id: string, approved: boolean) {
    setBusyId(id); setMessage("");
    try { const result = await api.approve(id, approved); setMessage(approved ? (result.execution ? "Approval recorded. Simulated execution was recorded locally." : "Approval recorded.") : "Rejection recorded. The action was not executed."); onChange(); }
    catch (cause) { setMessage(cause instanceof Error ? cause.message : "Unable to record review decision."); }
    finally { setBusyId(""); }
  }
  return <><PageTitle eyebrow="POLICY ENFORCEMENT" title="Gateway monitor" description="Review records are separate backend actions. No action runs until a simulated reviewer explicitly approves it." /><div className="alert safety-alert"><LockKeyhole size={18} /><div><strong>Approval is simulated</strong><span>Recorded decisions are local research data. Approving records only a mock email execution.</span></div></div>
    {message && <div className="alert info-alert"><Check size={16} />{message}</div>}
    <section className="panel table-panel"><div className="panel-heading"><div><h3>Pending review queue</h3><p>{pending.length} action{pending.length === 1 ? "" : "s"} waiting for a recorded decision</p></div><span className="badge badge-amber">{pending.length} pending</span></div>
      {pending.length ? <div className="review-list">{pending.map((item) => <article className="review-card" key={item.action_id}><div className="review-card-top"><div className="review-icon"><TriangleAlert size={18} /></div><div className="review-summary"><strong>Review proposed mock email</strong><span>{item.action?.recipient ?? "Missing recipient"} · {item.action?.data_label ?? "unknown label"} data</span></div><span className="badge badge-amber">REVIEW</span></div><div className="review-reason">{item.gateway?.reason}</div><div className="review-meta"><span>Action <code>{item.action_id}</code></span><span>Run <code>{item.run_id}</code></span><span>Policy <code>{item.gateway?.policy_rule_id}</code></span></div><div className="review-actions"><button className="button danger-outline" disabled={busyId === item.action_id} onClick={() => void decide(item.action_id, false)}><X size={15} /> Reject</button><button className="button primary" disabled={busyId === item.action_id} onClick={() => void decide(item.action_id, true)}><Check size={15} /> Approve mock action</button></div></article>)}</div> : <EmptyState icon={ShieldCheck} title="No pending approvals" text="When the gateway returns REVIEW, the action will wait here without executing." />}
    </section><section className="panel info-panel"><div className="info-icon"><LockKeyhole size={17} /></div><div><strong>Enforcement order</strong><p>The gateway evaluates trusted task intent, synthetic recipient allowlists, and trusted data labels. A BLOCK decision prevents execution; REVIEW creates a pending record.</p></div></section>
  </>;
}

function Experiments({ analytics, onChange }: { analytics: Array<{ experiment_id: string; [key: string]: Aggregate | string }>; onChange: () => void }) {
  const [configs, setConfigs] = useState<ConfigurationId[]>(allConfigs);
  const [splits, setSplits] = useState<Split[]>(["development"]);
  const [result, setResult] = useState<{ experiment_id: string; scenario_count: number; aggregates: Record<string, Aggregate> } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const latest = result ?? (analytics[0] ? { experiment_id: analytics[0].experiment_id, scenario_count: 0, aggregates: Object.fromEntries(Object.entries(analytics[0]).filter((entry): entry is [string, Aggregate] => typeof entry[1] === "object" && entry[1] !== null && "configuration_id" in entry[1])) } : null);
  function toggleConfig(config: ConfigurationId) { setConfigs((items) => items.includes(config) ? items.filter((item) => item !== config) : [...items, config]); }
  function toggleSplit(split: Split) { setSplits((items) => items.includes(split) ? items.filter((item) => item !== split) : [...items, split]); }
  async function run() {
    if (!configs.length || !splits.length) { setError("Choose at least one configuration and split."); return; }
    setBusy(true); setError("");
    try { const data = await api.runExperiment(configs, splits); setResult(data); onChange(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Experiment failed"); }
    finally { setBusy(false); }
  }
  const rows = latest ? Object.values(latest.aggregates).filter((item) => splits.includes(item.split)) : [];
  const chartData = rows.map((item) => ({ name: `${item.configuration_id.replaceAll("_", " ")} · ${item.split.replace("_", " ")}`, ASR: item.attack_success_rate.value ?? 0, Completion: item.normal_task_completion_rate.value ?? 0 }));
  return <><PageTitle eyebrow="REPRODUCIBLE EVALUATION" title="Experiment centre" description="Run the same labelled scenarios under independent detector and gateway settings. Every run is stored without overwriting previous results." />
    <div className="experiment-controls panel"><div className="control-group"><div className="control-title">Configurations <small>choose one or more</small></div><div className="choice-grid">{allConfigs.map((config) => <label className={`choice-card ${configs.includes(config) ? "selected" : ""}`} key={config}><input type="checkbox" checked={configs.includes(config)} onChange={() => toggleConfig(config)} /><span className="fake-check">{configs.includes(config) && <Check size={12} />}</span><span><strong>{configNames[config].split(" · ")[0]}</strong><small>{configNames[config].split(" · ").slice(1).join(" · ")}</small></span></label>)}</div></div>
      <div className="control-group split-group"><div className="control-title">Dataset splits <small>final-test remains reserved for reporting</small></div><div className="split-choices">{Object.entries(splitNames).map(([id, name]) => <label className="split-choice" key={id}><input type="checkbox" checked={splits.includes(id as Split)} onChange={() => toggleSplit(id as Split)} /> <span>{name}</span></label>)}</div></div>
      <div className="experiment-run"><div><strong>Local, synchronous experiment</strong><small>No model calls, cloud services, or real email.</small></div><button className="button primary" disabled={busy} onClick={() => void run()}>{busy ? <><span className="spinner small" /> Running…</> : <><Play size={15} fill="currentColor" /> Run experiment</>}</button></div>{error && <div className="inline-error">{error}</div>}
    </div>
    {latest ? <><div className="panel-heading standalone-heading"><div><h3>Measured comparison</h3><p>Experiment <code>{latest.experiment_id}</code> · {result ? `${result.scenario_count} scenario runs` : "previously stored results"}</p></div><button className="button secondary" onClick={() => void api.exportExperiment(latest.experiment_id)}><ArrowDownToLine size={15} /> Export raw CSV</button></div>
      <section className="panel chart-panel experiment-chart"><div className="panel-heading"><div><h3>Security and utility rates</h3><p>Percentages show the metric value; tables show numerator and denominator.</p></div></div>{chartData.length ? <ResponsiveContainer width="100%" height={280}><BarChart data={chartData} margin={{ top: 12, right: 18, bottom: 48, left: 0 }}><CartesianGrid stroke="#1d2937" vertical={false} /><XAxis dataKey="name" tick={{ fill: "#8998a7", fontSize: 10 }} interval={0} angle={-16} textAnchor="end" axisLine={false} tickLine={false} /><YAxis domain={[0, 100]} tick={{ fill: "#68798a", fontSize: 10 }} tickFormatter={(value) => `${value}%`} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ background: "#111c29", border: "1px solid #29394b", borderRadius: 10, color: "#e5edf5" }} formatter={(value) => [`${value}%`]} /><Bar dataKey="ASR" fill="#f26c72" radius={[4, 4, 0, 0]} /><Bar dataKey="Completion" fill="#36c9bc" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer> : <EmptyState icon={FlaskConical} title="No selected split results" text="Choose a split and run the experiment." />}</section>
      <section className="panel table-panel metrics-table"><div className="table-scroll"><table><thead><tr><th>Configuration / split</th><th>Scenarios</th><th>Attack success</th><th>Normal completion</th><th>False blocks</th><th>Reviews</th><th>Mean / P95 latency</th><th>CPU ms</th></tr></thead><tbody>{rows.map((item) => <tr key={`${item.configuration_id}-${item.split}`}><td><strong>{configNames[item.configuration_id]}</strong><small>{splitNames[item.split]}</small></td><td>{item.scenario_count}</td><td><MetricCell metric={item.attack_success_rate} tone="rose" /></td><td><MetricCell metric={item.normal_task_completion_rate} tone="green" /></td><td><MetricCell metric={item.false_block_rate} /></td><td><span className="badge badge-amber">{item.review_count}</span></td><td>{item.average_decision_latency_ms ?? "—"} / {item.p95_decision_latency_ms ?? "—"}</td><td>{item.cpu_time_ms_total.toFixed(3)}</td></tr>)}</tbody></table></div></section>
    </> : <section className="panel empty-experiment"><EmptyState icon={FlaskConical} title="No experiments recorded" text="Choose configurations and run a local experiment to generate stored measurements." /></section>}
  </>;
}

function AuditLog({ initialEvents }: { initialEvents: AuditEvent[] }) {
  const [query, setQuery] = useState("");
  const [events, setEvents] = useState(initialEvents);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { setEvents(initialEvents); }, [initialEvents]);
  async function search() {
    setBusy(true); setError("");
    try { setEvents((await api.audits(query)).items); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Search failed"); }
    finally { setBusy(false); }
  }
  return <><PageTitle eyebrow="TRACEABILITY" title="Audit logs" description="Chronological backend records distinguish proposed actions from mock executions and review decisions." />
    <section className="panel table-panel"><div className="audit-search-row"><div className="search-field"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search event detail, run ID, scenario…" onKeyDown={(event) => { if (event.key === "Enter") void search(); }} /><button onClick={() => void search()} disabled={busy}>{busy ? "Searching" : "Search"}</button></div><span className="result-count">{events.length} events shown</span></div>{error && <div className="inline-error">{error}</div>}
      {events.length ? <div className="audit-table">{events.map((event) => <ActivityRow key={event.event_id} event={event} detailed />)}</div> : <EmptyState icon={ClipboardList} title="No matching audit events" text="Run a simulation or experiment to populate this view." />}</section>
  </>;
}

function ActivityRow({ event, detailed = false }: { event: AuditEvent; detailed?: boolean }) {
  const icon = event.event_type.includes("blocked") || event.event_type.includes("failed") ? <ShieldX size={15} /> : event.event_type.includes("approval") ? <TriangleAlert size={15} /> : event.event_type.includes("execution") ? <Mail size={15} /> : <Activity size={15} />;
  const tone = event.event_type.includes("blocked") || event.event_type.includes("failed") ? "rose" : event.event_type.includes("approval") ? "amber" : event.event_type.includes("execution") ? "green" : "blue";
  return <div className={`activity-row ${detailed ? "detailed" : ""}`}><span className={`activity-icon ${tone}`}>{icon}</span><div className="activity-description"><strong>{event.event_type.replaceAll("_", " ")}</strong><small>{event.scenario_id} · {event.configuration_id} · {event.run_id}</small>{detailed && <pre>{JSON.stringify(event.detail, null, 2)}</pre>}</div><time>{new Date(event.timestamp).toLocaleString()}</time></div>;
}

function EmptyState({ icon: Icon, title, text }: { icon: typeof Activity; title: string; text: string }) { return <div className="empty-state"><div><Icon size={22} /></div><strong>{title}</strong><span>{text}</span></div>; }
function SplitBadge({ split }: { split: Split }) { return <span className={`split-badge ${split}`}>{splitNames[split]}</span>; }
function DecisionBadge({ decision }: { decision: string }) { return <span className={`decision-badge ${decision.toLowerCase()}`}>{decision}</span>; }
function MetricCell({ metric, tone }: { metric: { value: number | null; numerator: number; denominator: number }; tone?: string }) { return <span className={`metric-cell ${tone ?? ""}`}>{metric.value === null ? "n/a" : `${metric.value}%`}<small>({metric.numerator}/{metric.denominator})</small></span>; }

export default App;

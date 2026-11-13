# System architecture

Owner: Irwine (design lead). The data-flow diagram is in `docs/architecture.md`; trust rules are in `docs/safety_model.md`. This file maps the logical components to the actual code and lists the known gaps against the proposal.

## Components → code (verified 13 Nov 2026)

| Logical component (spec §5) | Implementation | Notes |
|---|---|---|
| React frontend | `frontend/src/App.tsx`, `api.ts`, `types.ts` | Single-file app; pages: Overview, Agent Simulator, Scenario Lab, Gateway Monitor, Experiments, Audit Log |
| FastAPI API layer | `backend/app/main.py` (`create_app`) | REST endpoints; see `docs/integration_contracts.md` |
| Scenario manager | `backend/app/scenarios.py` + `data/scenarios/scenarios.json` | Validates IDs, synthetic recipients, attack-target labels |
| Simulated agent | `agent.py` (`read_instructions`, `task_email_request`) + `_propose_action` in `engine.py` | Worst-case gullible reader (TD-005) |
| Mock tools + executor | `_read_document`, `_mock_send_email` in `engine.py` | SQLite only; no network; `read_document` gated in C/D (TD-006) |
| Content detector | `check_content` in `detectors.py` (re-exported by `security.py`) | Keyword default; pretrained adapter via `SENTINELAGENT_DETECTOR` (TD-010) |
| Policy gateway | `evaluate_gateway`, `evaluate_read` in `security.py` | Rules POL-001…011, fail-closed |
| Approval | `SimulationEngine.approve` + `POST /api/approvals/{id}` | One recorded decision per action |
| Experiment runner | `run_experiment` in `engine.py`, CLI `experiment_cli.py` | Review policies, peak memory, CSV/JSON, `reports/evaluation_report.md` |
| Metrics | `metrics.py` (`summarize`, `is_attack_success`) | Definitions v2, incl. allowed-channel leak goal |
| Detector evaluation | `detector_eval.py` + `data/detector/*.jsonl` | Objective iii report |
| Final-test freeze | `freeze.py` + `data/scenarios/final_test_freeze.json` | TD-008 |
| Launcher | `run.py` (repo root) | Setup/start/test/experiment on any OS |
| Audit logger | `SimulationEngine._audit` → `audit_events` table | Stores summaries, not message bodies |
| Persistence | `database.py` (SQLite) | Path from `SENTINELAGENT_DB` or `data/sentinelagent.sqlite3` |

## Enforcement point

In configurations C and D the only path from a proposed action to `_mock_send_email` runs through `evaluate_gateway`. Exceptions, missing detector output (when required), or malformed actions produce BLOCK. REVIEW persists the action as `pending`, and only `approve()` with `approved=true` can execute it.

## Gaps status (13 Nov 2026)

- **G1 `read_document` not gated** — closed (TD-006).
- **G2 Agent realism** — closed for this study's purpose (TD-005); it remains a simulation, not an LLM.
- **G3 No pretrained detector** — adapter, text sets and evaluation done (TD-010); the real model run is pending on a machine with internet.
- **G4 Scenario coverage** — closed: 54 scenarios, 10 action attacks per split (TD-007).
- **G5 Code layout** — kept flat; modules map one-to-one to owners (see `CLAUDE.md`).

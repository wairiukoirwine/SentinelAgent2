# System architecture

Owner: Irwine (design lead). The data-flow diagram is in `docs/architecture.md`; trust rules are in `docs/safety_model.md`. This file maps the logical components to the actual code and lists the known gaps against the proposal.

## Components → code (verified 13 Nov 2026)

| Logical component (spec §5) | Implementation | Notes |
|---|---|---|
| React frontend | `frontend/src/App.tsx`, `api.ts`, `types.ts` | Single-file app; pages: Overview, Agent Simulator, Scenario Lab, Gateway Monitor, Experiments, Audit Log |
| FastAPI API layer | `backend/app/main.py` (`create_app`) | REST endpoints; see `docs/integration_contracts.md` |
| Scenario manager | `backend/app/scenarios.py` + `data/scenarios/scenarios.json` | Validates IDs, synthetic recipients, attack-target labels |
| Simulated agent | `SimulationEngine.simulate` / `_propose_action` in `engine.py` | Deterministic; see gap G2 |
| Mock tools + executor | `_read_document`, `_mock_send_email` in `engine.py` | SQLite only; no network |
| Content detector | `check_content` in `security.py` | Keyword baseline; see gap G3 |
| Policy gateway | `evaluate_gateway` in `security.py` | Rules POL-001…009, fail-closed |
| Approval | `SimulationEngine.approve` + `POST /api/approvals/{id}` | One recorded decision per action |
| Experiment runner | `run_experiment` in `engine.py`, CLI `experiment_cli.py` | Writes SQLite, CSV, JSON, `reports/evaluation_report.md` |
| Metrics | `metrics.py` (`summarize`, `is_attack_success`) | Definitions v2 |
| Audit logger | `SimulationEngine._audit` → `audit_events` table | Stores summaries, not message bodies |
| Persistence | `database.py` (SQLite) | Path from `SENTINELAGENT_DB` or `data/sentinelagent.sqlite3` |

## Enforcement point

In configurations C and D the only path from a proposed action to `_mock_send_email` runs through `evaluate_gateway`. Exceptions, missing detector output (when required), or malformed actions produce BLOCK. REVIEW persists the action as `pending`, and only `approve()` with `approved=true` can execute it.

## Known gaps (tracked in `DEVELOPMENT_ROADMAP.md`)

- **G1 `read_document` is not gated.** The proposal says every proposed tool call passes the gateway. (Step 3)
- **G2 Agent realism.** Injection succeeds only through a literal `ACTION: SEND_EMAIL TO x` line, so reworded attacks cannot succeed even in baseline. (Step 3)
- **G3 No pretrained detector.** Only the keyword baseline exists. (Step 5)
- **G4 Scenario coverage.** 2–3 action attacks per split, almost all with obvious keywords. (Step 4)
- **G5 Code layout** is flat rather than the spec §6 tree. Acceptable for now; restructure only if it helps per-member ownership.

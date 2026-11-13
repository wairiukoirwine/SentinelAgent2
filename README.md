# SentinelAgent

SentinelAgent is a local research prototype for studying indirect prompt injection in a deterministic simulated agent. It reads only synthetic scenario documents, proposes at most one structured `send_email` action, applies independently switchable controls, and records mock execution and audit results in SQLite.

The prototype does not call an LLM, email provider, network tool, or cloud service. The detector is a transparent keyword/phrase heuristic; its score is an uncalibrated lexical indicator, not a probability.

## Requirements

- Python 3.11 or later (the build was attempted in the supplied Python 3.14 environment; see `BUILD_STATUS.md` for the verified result).
- Node.js and npm for the React/Vite dashboard.
- Windows PowerShell commands are shown below. Equivalent Python and npm commands work on other platforms.

## Install

From this directory:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-lock.txt
cd frontend
npm ci
cd ..
```

## Run locally

Start the backend in one terminal:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the dashboard in another terminal:

```powershell
cd frontend
npm run dev
```

Open the local address printed by Vite (normally `http://127.0.0.1:5173`). API documentation is available at `http://127.0.0.1:8000/docs`.

PowerShell helpers are also provided under `scripts/`.

## Tests and experiments

Run the automated backend and security tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q --basetemp .pytest-tmp --junitxml ..\reports\test_evidence\pytest-results.xml
```

Run the reproducible four-configuration experiment across all three splits:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.experiment_cli
```

Experiment rows and summaries are written to `data/exports/`; SQLite records are stored in `data/sentinelagent.sqlite3`, or wherever the `SENTINELAGENT_DB` environment variable points. The experiment command can be limited to a split or configurations, for example:

```powershell
.\.venv\Scripts\python.exe -m app.experiment_cli --splits development --configurations combined gateway_only
```

The API also supports synchronous experiments and CSV export. The dashboard reads actual API and SQLite results; empty states remain visible until you run a simulation or experiment.

## Four configurations

| ID | Detector | Gateway | Behavior |
|---|---:|---:|---|
| `baseline` | Off | Off | Intentionally unprotected comparison; mock tools only. |
| `content_only` | On | Off | A suspicious or failed detector result blocks mock tool execution; there is no policy gateway. |
| `gateway_only` | Off | On | Trusted task, recipient, tool, and data-label rules decide ALLOW, BLOCK, or REVIEW. |
| `combined` | On | On | Detector result is passed to the enforcing policy gateway. |

## Safety and research boundaries

- Scenario documents are labelled untrusted and cannot supply trusted policy, labels, tasks, or allowlists.
- Only `read_document` from the scenario store and the local mock `send_email` action are available to the simulated agent.
- All recipient addresses use the reserved synthetic `example.test` domain.
- The gateway checks the trusted user task, recipient allowlist, and data label. REVIEW requires a separate recorded decision; rejection never executes.
- The baseline is deliberately unprotected but remains confined to the SQLite mock event store.
- Development and validation may support implementation and rule checks. Keep the `final_test` split reserved from tuning.

## Project map

- `backend/app/`: API, scenario contracts, deterministic agent, detector, gateway, SQLite persistence, and experiment runner.
- `backend/tests/`: unit, integration, API, and security-boundary tests.
- `frontend/src/`: React dashboard and backend API client.
- `data/scenarios/`: 24 synthetic scenarios, split 8/8/8. Attack scenarios carry a trusted `attack_target_recipient` label used for attack-success scoring.
- `docs/`: architecture, contracts, safety, and evaluation protocol.
- `reports/`: evaluation output, limitations, and demonstration notes.
- `PROJECT_SPEC.txt`: complete source outline included with the deliverable.
- `PROJECT_CONTEXT.md`, `SYSTEM_ARCHITECTURE.md`, `DEVELOPMENT_ROADMAP.md`, `TECHNICAL_DECISIONS.md`, `DEVELOPMENT_LOG.md`: project control docs. Start with `PROJECT_CONTEXT.md`.

## Documentation

Read `docs/architecture.md`, `docs/safety_model.md`, and `docs/experiment_protocol.md` before adapting the policy or reporting results. Actual test and experiment outcomes are recorded in `BUILD_STATUS.md` and `reports/evaluation_report.md` after commands are run.

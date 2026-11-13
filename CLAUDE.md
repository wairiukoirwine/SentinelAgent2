# SentinelAgent — guide for Claude Code

DAI034 capstone (AIU, Track C). A policy-enforced security gateway against indirect prompt injection in a **simulated** document-reading agent. Read `PROJECT_CONTEXT.md` first; it names the sources of truth (approved proposal > `PROJECT_SPEC.txt` > repo docs).

## Commands (run from the repo root)

```bash
python run.py setup          # first time: backend/.venv + npm ci
python run.py                # backend :8000 + dashboard :5173
python run.py test           # pytest (must stay green)
python run.py experiment     # four configurations x three splits -> reports/evaluation_report.md
python run.py detector-eval  # keyword vs pretrained on data/detector -> reports/detector_report.md
python run.py check          # environment status
```
On macOS/Linux use `python3` if `python` is missing. Frontend only: `cd frontend && npm run build` (type-checks).

## Map

- `backend/app/agent.py` — simulated gullible agent (how injected text is understood). Owner: Teddy.
- `backend/app/security.py` — policy gateway `evaluate_gateway` (POL-001…009) and read gate `evaluate_read` (POL-010/011). Owner: Teddy.
- `backend/app/detectors.py` — `check_content(text)`: keyword baseline + pretrained adapter. Owner: Benedict.
- `backend/app/engine.py` — simulation, approvals, `run_experiment` (review policies, memory).
- `backend/app/metrics.py` — metric definitions v2 (`is_attack_success`, `summarize`).
- `data/scenarios/scenarios.json` — 54 labelled scenarios. Owner: Irwine. `data/detector/*.jsonl` — detector text sets.
- `frontend/src/App.tsx` — dashboard. Owner: Irwine.

## Rules that must not be broken

1. **Mock tools only.** No real email, SMTP, network calls, LLM APIs or personal data. Recipients must be `@example.test` addresses (the loader enforces this).
2. **Fail closed.** In protected configurations any gateway/detector error, missing field or unknown tool is BLOCK. Never turn an exception into ALLOW.
3. **Untrusted document text never sets trusted fields** (task, allowlist, data label, attack labels).
4. **Never tune on `final_test`.** It is frozen (`data/scenarios/final_test_freeze.json`); `tests/test_metrics_v2.py::test_final_test_split_is_frozen` fails if it changes. Re-freezing needs a written reason in `TECHNICAL_DECISIONS.md` and `python -m app.freeze --write`.
5. **Never invent results.** Report numbers only from a real run; say when something was not run (for example the pretrained model).
6. Metric definitions are v2 (`docs/experiment_protocol.md`). Changing them needs a new TD entry and a `metrics_version` bump.
7. After any change: run `python run.py test`, `npm run build` for frontend changes, then add an entry to `DEVELOPMENT_LOG.md`. Update `DEVELOPMENT_ROADMAP.md` / `TECHNICAL_DECISIONS.md` when relevant.

## Conventions

Python 3.11+, type hints, Pydantic models in `models.py`, small modules, docstrings that explain *why*. Every new attack scenario needs `attack_target_recipient` (and `attack_goal` for allowed-channel leaks). Commit per member branch (`teddy/dev`, `irwine/dev`, `benedict/dev`) and merge to `main`.

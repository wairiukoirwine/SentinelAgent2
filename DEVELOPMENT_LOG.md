# Development log

Newest first. Each entry: what changed, why, and what was actually verified.

## 2026-11-13 — Steps 3–8: agent, scenarios v2, detectors, review policies, dashboard, launcher

**Changed**
- **Step 3 (TD-005, TD-006):** `backend/app/agent.py` — worst-case gullible simulated agent (misspelling, spacing, leetspeak, base64, zero-width, Swahili/French; quoted/negated/inflected text ignored; allowed-channel disclosure). `read_document` gated in C/D (POL-010/011).
- **Step 4 (TD-007, TD-008):** 30 new scenarios (54 in total, 18 per split, 10 action attacks per split); `attack_goal` label; `final_unapproved_public` detector label corrected; final-test freeze by SHA-256 with a guarding test.
- **Step 5 (TD-010):** `backend/app/detectors.py` (keyword + pretrained adapter, fail-closed, labelled fallback), `data/detector/` 40 + 40 text sets, `app/detector_eval.py`, `requirements-ml.txt`.
- **Step 6 (TD-009):** reviewer policies (`pending` / `approve_all` / `reject_all`), tracemalloc peak memory, richer CSV, sensitivity runs and per-attack-type tables in the evaluation report.
- **Step 7:** dashboard per-scenario results table, reviewer selector, stored-experiment picker, v2 columns, agent evidence in the simulator, favicon.
- **Step 8 (TD-011):** `run.py` launcher (process-group shutdown on Ctrl+C / SIGTERM), `.vscode/`, `CLAUDE.md`, `.claude/settings.json`, `pytest.ini`, pinned frontend versions, docs and README rewritten, screenshots, canonical results in `reports/results/`.

**Verified**
- 57 tests pass on Python 3.13 (dev venv) and on Python 3.11 from a fresh clone with `python run.py setup` (installs from `requirements-lock.txt`).
- `npm ci` + `npm run build` pass; all six dashboard pages load against the live API with no console errors (Chrome via Playwright).
- `python run.py` starts both servers (health 200, dashboard 200, 54 scenarios) and SIGTERM stops both process trees.
- Canonical run `experiment_34c8615a58e1` (216 trials). Final test: attack success A 10/10, B 7/10, C 1/10, D 1/10; the remaining success is the allowed-channel leak. A fresh-clone rerun gives identical rates.
- Keyword detector on the detector test set: precision 100%, recall 10% (2/20).

**Not verified**
- Pretrained classifier: Hugging Face unreachable from the build sandbox; adapter tested with a stand-in pipeline only.
- Windows-specific `run.py` branches (`npm.cmd`, `Scripts\python.exe`, `taskkill`) were not executed; the Linux and macOS code path was.

## 2026-11-13 — Steps 1–2: project docs, roles, metrics v2

**Changed**
- Imported the received prototype into git (`main`, baseline commit) without the bundled Windows `.venv`, `node_modules`, build output or SQLite data.
- Added `PROJECT_CONTEXT.md`, `SYSTEM_ARCHITECTURE.md`, `DEVELOPMENT_ROADMAP.md`, `TECHNICAL_DECISIONS.md`, and this log.
- `docs/team_contributions.md` rewritten to the proposal's roles (TD-001).
- Metrics v2 (TD-002, TD-003): new trusted scenario field `attack_target_recipient` (set on 8 action attacks); `metrics.is_attack_success()` is now the single definition used by `simulate()` and `approve()`; `summarize()` uses action-attack and action-normal denominators and adds review metrics.
- `create_app()` and `experiment_cli` now honour `SENTINELAGENT_DB` (they ignored it before).
- Report generator, `docs/experiment_protocol.md`, `docs/data_dictionary.md`, `BUILD_STATUS.md` and frontend types updated for v2.
- Created member branches `teddy/dev`, `irwine/dev`, `benedict/dev` from `main`.

**Verified**
- `pytest`: 23 passed (14 existing, unchanged, plus 9 new in `tests/test_metrics_v2.py`).
- `npm run build`: passed.
- Full experiment `experiment_11ef358658a0`, 96 rows. Final-test attack success: baseline 3/3, content-only 1/3, gateway-only 0/3, combined 0/3.

**Finding.** Under v2 the detector misses `val_ambiguous_action` and `final_unapproved_public` (benign-looking text that redirects to an unapproved address), and the gateway blocks both. This is the first evidence in the corpus that the gateway adds protection beyond the detector. With 2–3 action attacks per split it is not yet a meaningful result; step 4 is what will make it one.

**Not changed:** `PROJECT_SPEC.txt` (supplied reference), gateway rules, detector, agent logic, dashboard UI.

## 2026-11-12 — Received prototype

Initial prototype built before this log existed. See `BUILD_STATUS.md` (12 Nov entries) and `docs/decisions.md`.

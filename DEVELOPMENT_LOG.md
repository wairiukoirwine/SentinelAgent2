# Development log

Newest first. Each entry: what changed, why, and what was actually verified.

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

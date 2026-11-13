# Technical decisions

Decisions inherited from the received prototype (deterministic agent, keyword detector, Configuration B behaviour, REVIEW, SQLite, styling) are recorded in `docs/decisions.md` and remain in force unless superseded here.

## TD-001 — The approved proposal governs team roles (13 Nov 2026)

**Context.** `PROJECT_SPEC.txt` §3 assigns Irwine to the policy gateway and Teddy to scenarios and the dashboard. The approved proposal (Table P.1) assigns Teddy to the agent, gateway and integration, Irwine to architecture, scenarios and dashboard, and Benedict to detection.
**Decision.** Follow the proposal. `PROJECT_SPEC.txt` is kept unmodified as a supplied reference; this record documents the override.
**Consequence.** `docs/team_contributions.md` rewritten; member branches named accordingly.

## TD-002 — Metric definitions v2 (13 Nov 2026)

**Context.** v1 counted an attack as successful only when confidential data reached an unapproved recipient. In baseline, `final_unapproved_public` delivered to the attacker's address and was not counted. Non-action attacks (which can never execute) sat in the attack-success denominator, and summary-only normal tasks (which can never be blocked) sat in the false-block denominator. Together these understated baseline risk and hid the one case where the detector misses and only the gateway stops the attack.
**Decision.** Attack success = the labelled attack target received a mock email, over action attacks only. False-block and review rates use action-normal tasks as the denominator. Add `normal_review_rate`, `normal_pending_review_count`, `attack_review_count`, `metrics_version`. Full definitions are in `docs/experiment_protocol.md`.
**Consequence.** Experiments stored before this change are v1 and not comparable; the 12 Nov results in the old `BUILD_STATUS.md` are superseded. Frontend types accept both.

## TD-003 — Attack target is a trusted author label (13 Nov 2026)

**Context.** Success must be judged against the attacker's goal, but the goal must not be read from untrusted document text at evaluation time.
**Decision.** Add `attack_target_recipient` to the scenario schema, set by the scenario author. The loader rejects it on non-attacks and on non-`example.test` addresses. A test checks that each target appears in its document and is not allowlisted.
**Consequence.** Every new attack scenario (step 4) must set this field, or leave it null if it requests no action.

## TD-004 — Unresolved REVIEW counts as not completed (interim, 13 Nov 2026)

**Context.** Experiment runs never call the approval endpoint, so REVIEW actions stay pending.
**Decision.** Until step 6, a pending REVIEW on a normal task counts as not completed and is reported separately via `normal_review_rate`. It is not a false block.
**Superseded by TD-009** (13 Nov 2026): `pending` is now the named default reviewer policy, with `approve_all` / `reject_all` sensitivity runs.

## TD-005 — The simulated agent is a worst-case gullible reader (13 Nov 2026)

**Context.** The received agent followed only a literal `ACTION: SEND_EMAIL TO x` line, so a reworded attack could never succeed even without defences, and evasion could not be studied.
**Decision.** `backend/app/agent.py` models an LLM that understands and obeys injected send instructions after normalising misspellings (edit distance 1 for verbs of 5+ letters), spaced or dotted letters, leetspeak, zero-width characters, base64 segments, and Swahili/French verbs. It ignores quoted text, negated sentences and inflected verbs ("sent", "included"). A document redirect overrides the user's own request. A separate "disclosure" instruction (include/attach + sensitive term) adds injected content to an email the user asked for.
**Rationale.** The gateway is meant for the case where the model is fooled, so the simulation assumes the model is fooled whenever it can read the instruction. Every rule is visible and tested (`tests/test_agent.py`).
**Limitation.** It is not a real LLM; real models are sometimes more and sometimes less gullible.

## TD-006 — read_document passes the gateway (13 Nov 2026)

**Decision.** In configurations C and D, `read_document` is checked by `evaluate_read`: only the trusted scenario's document ID is allowed (POL-011); anything else is BLOCK (POL-010). The decision is stored as `read_gateway_result`. Baseline and content-only read directly, as before.

## TD-007 — Scenario set v2 and the allowed-channel leak goal (13 Nov 2026)

**Decision.** Added 30 scenarios (10 per split, 54 in total): evasive redirects (misspelling, spacing, leetspeak, base64, Swahili, French), paraphrased redirects, classic keyword attacks, allowed-channel leaks, benign keyword look-alikes, authorised confidential emails, and authorised emails whose documents contain trigger words. Splits share attack types but use different wording. New trusted field `attack_goal` (`exfiltrate_to_target` | `leak_via_allowed_channel`). The loader checks that exfiltration targets are not allowlisted and that leak targets are.
**Label correction.** `final_unapproved_public` contains an injected `ACTION` line, so its ground-truth detector label is now `suspicious` (it was `benign`). This changes detector agreement counts only, not attack success.

## TD-008 — Final-test freeze (13 Nov 2026)

**Decision.** `app/freeze.py` records a SHA-256 fingerprint of the 18 final-test scenarios in `data/scenarios/final_test_freeze.json`, written before keyword threshold selection on the v2 set and before any v2 experiment. A test fails if the split changes. Re-freezing needs a reason recorded here.

## TD-009 — Experiment reviewer policies and peak memory (13 Nov 2026)

**Decision.** `run_experiment(review_policy=...)`: `pending` (default; nobody reviews), `approve_all`, `reject_all`. Decisions go through the normal approval path with reviewer `experiment-policy:<name>`. The CLI adds `approve_all` / `reject_all` final-test runs for C and D to the report. Peak memory is measured per trial with `tracemalloc` (Python allocations only); the reported value is the maximum within the group. Latency includes tracemalloc overhead equally in every setup; `--no-memory` gives clean latency.

## TD-010 — Pretrained detector integration (13 Nov 2026)

**Decision.** `backend/app/detectors.py` keeps the keyword baseline as default and adds `protectai/deberta-v3-base-prompt-injection-v2` (Apache-2.0, DeBERTa-v3, CPU) used as-is, selected with `SENTINELAGENT_DETECTOR=pretrained`. Score = model P(injection). Threshold chosen by max F1 on `data/detector/dev.jsonl` and saved to `data/detector/thresholds.json`; test set scored once. An unavailable model fails closed; an explicit, labelled keyword fallback is opt-in. Detector evaluation uses separate 40 + 40 text sets, not the agent scenarios.
**Limitation.** Hugging Face was unreachable from the build environment, so the model has not been run. No model numbers exist until a team member runs `python run.py detector-eval --pretrained`. The adapter is tested with a stand-in pipeline.

## TD-011 — One launcher and editor configuration (13 Nov 2026)

**Decision.** `run.py` (standard library only) handles setup, start, tests, experiments and detector evaluation on Windows, macOS and Linux, and installs backend packages from `requirements-lock.txt`. Frontend dependencies are pinned to the lockfile versions. `.vscode/` provides tasks, debug configurations and test settings; `CLAUDE.md` and `.claude/settings.json` configure Claude Code. Canonical results are written to `reports/results/` (tracked) via `--export-dir`; ad-hoc runs still go to `data/exports/` (ignored).

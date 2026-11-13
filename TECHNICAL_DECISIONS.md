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
**Revisit.** Step 6 will define an explicit, documented experimental reviewer policy.

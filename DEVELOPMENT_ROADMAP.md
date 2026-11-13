# Development roadmap

Status key: ✅ done · 🔄 in progress · ⏳ not started. Leads follow the approved proposal.

| Step | Task | Lead | Status |
|---|---|---|---|
| 0 | Inspect prototype, verify tests/build/results, initial technical assessment | Shared | ✅ 13 Nov |
| 1 | Project docs (this set), roles fixed to proposal, `SENTINELAGENT_DB` fix, git repo and member branches | Shared | ✅ 13 Nov |
| 2 | Metric definitions v2: trusted attack target, correct denominators, review metrics, tests | Teddy | ✅ 13 Nov |
| 3 | Agent instruction-following upgrade (reworded email/forward requests can succeed in baseline); route `read_document` through the gateway | Teddy | ⏳ |
| 4 | Scenario set v2 (~48–60): detector-evasive (misspelling, spacing, encoding, other language), paraphrased, allowed-channel leak, more benign look-alikes; freeze `final_test` before tuning | Irwine | ⏳ |
| 5 | Pretrained classifier adapter (CPU, offline fallback to keyword) + separate detector dev/test text sets + detector report | Benedict | ⏳ |
| 6 | Experimental reviewer policy for REVIEW, peak memory (`tracemalloc`), re-run all four configurations | Teddy | ⏳ |
| 7 | Dashboard: per-scenario table (proposed call, expected, decision, reason), detector panel, v2 metric columns | Irwine | ⏳ |
| 8 | Evaluation report, screenshots, single-command start, demo script | Shared | ⏳ |

## Dependencies

- Step 4 depends on step 3 (evasive attacks only make sense once the agent can follow them).
- Step 5 needs step 4's scenarios for the end-to-end run, but can start now on its own text sets.
- Step 6 runs after 3–5; the final numbers come from step 6.

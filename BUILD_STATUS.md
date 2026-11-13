# Build status

Last verified **13 Nov 2026** (Linux; Python 3.11, 3.12 and 3.13; Node 22). Earlier history is in `DEVELOPMENT_LOG.md`.

## Commands and actual outcomes

| Command | Outcome |
|---|---|
| `python run.py setup` (fresh clone) | Passed on Python 3.11 (see log entry) |
| `python run.py test` | **57 passed**, 1 Starlette deprecation warning. JUnit: `reports/test_evidence/pytest-results.xml` |
| `npm ci && npm run build` | Passed; Vite advises the JS bundle is over 500 kB (not an error) |
| `python run.py experiment --export-dir reports/results` | `experiment_34c8615a58e1`: 216 trials (54 scenarios × 4 setups) + 2 reviewer-sensitivity runs |
| `python run.py detector-eval` | Keyword baseline scored on the 40-text test set; pretrained run skipped (no model in build environment) |
| Backend + dashboard | All six pages load against the live API with no console errors; screenshots in `reports/screenshots/` |

## Acceptance criteria (PROJECT_SPEC §25 / proposal §1.7)

| # | Criterion | Status |
|---|---|---|
| 1 | Agent reads untrusted synthetic documents | ✅ |
| 2 | Indirect injection attempts demonstrated (incl. evasive forms) | ✅ 54 scenarios |
| 3 | Content detection component | ✅ keyword · ⚠️ pretrained implemented, **not yet run** |
| 4 | Independently switchable gateway | ✅ |
| 5 | ALLOW / BLOCK / REVIEW with recorded approval | ✅ |
| 6 | Mock `read_document` and `send_email` only; reads gated in C/D | ✅ |
| 7 | Fail closed on errors / missing inputs | ✅ tested |
| 8 | Four configurations compared on the same scenarios | ✅ |
| 9 | Labelled, separated, frozen splits | ✅ |
| 10 | Attack success, normal completion, false blocks, latency, CPU, memory | ✅ (metrics v2) |
| 11 | Reproducible records and audit logs | ✅ SQLite + CSV/JSON in `reports/results/` |
| 12 | Dashboard with per-scenario call / expected / decision / reason | ✅ |
| 13 | Single-command start from README | ✅ `python run.py` |
| 14 | Detector precision / recall / confusion on separate test set | ✅ keyword · ⚠️ pretrained pending |
| 15 | Setup, safety, protocol, evaluation docs | ✅ |
| 16 | Per-member Git branches | ✅ created; members must commit their own work |

## Not done / limitations

- **Pretrained classifier not run.** Hugging Face was unreachable from the build sandbox. The adapter is tested with a stand-in model. Run `python run.py ml-setup` and `python run.py detector-eval --pretrained` on a laptop with internet.
- The agent is a rule-based simulation of a gullible LLM, not a real model.
- 18 scenarios per split; rates are descriptive.
- Final-test labels are in the repo; the split is frozen against tuning but not blind.
- Allowed-channel leaks pass every configuration (expected; reported as failures).
- Latency/memory are local measurements; tracemalloc adds overhead equally to all setups.

# Build status

## Verified build

- Python `3.14.6`; FastAPI `0.162.4`; Uvicorn `0.54.0`; Pydantic `2.14.3`; SQLite; pytest `8.4.2`; HTTPX `0.28.1`.
- Node `v26.13.1`; npm `11.20.0`; React `19.3.1`; Vite `8.3.8`; TypeScript `7.0.2`; Recharts `3.10.1`; Lucide React `1.72.0`.
- Backend versions are pinned in `backend/requirements-lock.txt`; the frontend tree is pinned in `frontend/package-lock.json`.
- `npm install` reported zero vulnerabilities. No paid service, GPU, API key, external LLM, or external email service is required.

## Commands and actual outcomes

- 13 Nov 2026 (Linux, Python 3.13.18, Node 22.23.4): `python -m pytest tests -q` → **23 passed**, 1 warning; `npm ci && npm run build` → **passed**; full experiment → 96 rows (`experiment_11ef358658a0`).
- 12 Nov 2026 (original build, Windows) — Backend tests, from `backend/`: `.venv\Scripts\python.exe -m pytest tests -q --basetemp .pytest-tmp --junitxml ..\reports\test_evidence\pytest-results.xml` → **14 passed**, 1 Starlette deprecation warning in 4.25 seconds.
- Frontend build, from `frontend/`: `npm run build` → **passed** TypeScript and Vite production build. Vite reports a 634.38 kB minified JavaScript chunk (186.76 kB gzip), above its 500 kB advisory threshold.
- Backend local run: `uvicorn app.main:app --host 127.0.0.1 --port 8000` → started; `/health` returned `ok` and `/api/scenarios` returned 24 scenarios.
- Frontend local run: `npm run dev` → Vite ready at `http://127.0.0.1:5173/`; page request returned HTTP 200 and the browser showed the connected dashboard and genuine empty-result states before experiments.
- Fresh live API check after the final experiment: health `ok`; 24 scenarios; 288 persisted simulation runs; 3 experiments; CSV export includes detector score and threshold.
- Full experiment: `python -m app.experiment_cli` → **96 scenario/configuration rows** across four configurations and three splits. Canonical final run: `experiment_658b38e6eee2`.
- Latest test output: `reports/test_evidence/pytest-results.xml`. Latest raw CSV and summary: `data/exports/experiment_658b38e6eee2_results.csv` and `data/exports/experiment_658b38e6eee2_summary.json`.

## Final-test sample results (metrics v2, 13 Nov 2026)

Run `experiment_11ef358658a0` (Linux, Python 3.13), fresh database, all four configurations × three splits = 96 rows. Final-test split: 3 action attacks, 1 non-action attack, 4 normal tasks (2 requiring an email). Descriptive results on a synthetic corpus, not general performance claims. Latency is machine-dependent.

| Configuration | Attack success | Normal completion | False blocks | Normal reviews |
|---|---:|---:|---:|---:|
| A Baseline / No Gateway | 100% (3/3) | 100% (4/4) | 0% (0/2) | 0% (0/2) |
| B Content Check Only | 33.3% (1/3) | 100% (4/4) | 0% (0/2) | 0% (0/2) |
| C Policy Gateway Only | 0% (0/3) | 75% (3/4) | 0% (0/2) | 50% (1/2) |
| D Combined Controls | 0% (0/3) | 75% (3/4) | 0% (0/2) | 50% (1/2) |

The content-only miss is `final_unapproved_public` (detector score 0.0); the same miss occurs on validation (`val_ambiguous_action`, score 0.5). The 75% normal completion for C and D comes from one internal-data email left at pending REVIEW (TD-004).

The 12 Nov table that was here (baseline 50%, run `experiment_658b38e6eee2`) used metric definitions v1 and is superseded (`TECHNICAL_DECISIONS.md` TD-002).

## Acceptance criteria

1. Backend starts locally — **passed**.
2. Frontend starts locally — **passed**; production build also succeeds.
3. Synthetic scenarios load — **passed**, 24 total, 8 per split.
4. Agent reads through the scenario-store `read_document` boundary — **passed** in end-to-end/API tests.
5. Agent proposes and records mock `send_email` actions — **passed**.
6. Detector can be enabled independently — **passed**.
7. Gateway can be enabled independently — **passed**.
8. Four configurations execute — **passed**, 96 rows in the canonical experiment.
9. Protected actions pass through gateway — **passed** by integration tests.
10. BLOCK prevents execution — **passed**.
11. REVIEW waits for separate recorded approval; rejection does not execute — **passed**.
12. Detector and gateway failures fail closed — **passed**.
13. Audit events record decisions and outcomes — **passed**.
14. Experiment records persist — **passed** in SQLite and API retrieval tests.
15. Defined rates, denominators, latency, CPU, and detector confusion counts calculate — **passed**; memory is explicitly null.
16. Dashboard consumes backend analytics and run totals — **implemented and API/build verified**. The populated chart was not visually rechecked in a browser after the final run.
17. CSV export works — **passed**, including detector method, score, and threshold.
18. Automated tests — **passed**, 23/23 on 13 Nov 2026 (Linux, Python 3.13), one Starlette deprecation warning.
19. Safety boundaries — **passed** in tests for recipient policy, BLOCK, REVIEW, rejection, errors, unknown tools, trusted-task/label/allowlist separation, and mock-only execution.
20. Setup, safety, API, experiment, and data documentation — **passed**.

## Incomplete outline deliverables and limitations

- The content detector is a transparent local keyword heuristic. The outline’s teammate-selected pretrained classifier is not present; no model provenance or claimed model accuracy is supplied.
- The dashboard uses local CSS and native accessible components with Lucide and Recharts. Tailwind CSS and shadcn/ui are not included.
- Screenshot evidence was not saved. The initial overview was visually checked; the final populated chart was not visually rechecked.
- The corpus is small and synthetic. Final-test labels are present in source, so this is not a blind evaluation.
- Peak memory is not measured. Latency and CPU are machine-dependent local process measurements.
- One Starlette test-client deprecation warning and one Vite bundle-size advisory remain; neither fails the build or test suite.
- `experiment_17b9fdeb1a3b` is an earlier exploratory run at threshold 0.50. Later runs use the development-selected 0.75 threshold. The canonical current output is `experiment_658b38e6eee2`; earlier records remain preserved in SQLite.

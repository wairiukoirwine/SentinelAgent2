# Team contribution record

Roles follow the **approved Chapter One proposal** (Table P.1), which takes precedence over the role section of `PROJECT_SPEC.txt` (see `TECHNICAL_DECISIONS.md`, TD-001).

| Member | Role | Lead objective(s) | Areas in this repository |
|---|---|---|---|
| Teddy Musyoki | Team lead and lead developer | ii, iv | Simulated agent and mock tools (`backend/app/engine.py`), policy gateway: action record, ordered rules, safe defaults, REVIEW, audit log, on/off switches (`security.py` → `evaluate_gateway`, `config.py`), integration, four-setup experiment runner (`experiment_cli.py`, `metrics.py`). |
| Irwine Kang'acha | Design lead | i, dashboard part of iv | Architecture and data-flow diagrams (`SYSTEM_ARCHITECTURE.md`, `docs/architecture.md`), fake documents and labelled normal/attack scenarios (`data/scenarios/`), results dashboard (`frontend/`). |
| Benedict Sau | Detection lead | iii | Pretrained detector and keyword baseline behind `check_content(text)` (`security.py`), development/test text sets, threshold selection, detector results report; shared reference list. |
| All | Shared | — | Introduction, background reading, references, README, final demonstration. |

## Status of each member's area (13 Nov 2026)

- **Teddy:** agent, gateway, switches and runner exist from the received prototype; metric definitions revised to v2. Agent realism and gating of `read_document` outstanding (roadmap steps 3).
- **Irwine:** 24 scenarios exist but do not yet test detector evasion (roadmap step 4). Dashboard exists; per-scenario results table outstanding (step 7). Architecture docs being consolidated.
- **Benedict:** only the keyword baseline exists. The pretrained classifier, separate detector test set and detector report are outstanding (step 5).

## Attribution note

The received prototype has no commit history, so this table records **intended** ownership, not authorship. From 13 Nov 2026 each member works on their own branch (`teddy/dev`, `irwine/dev`, `benedict/dev`) and merges to `main`, so individual work is traceable. Code produced with AI assistance must be disclosed per the proposal's AI Tool Use Disclosure.

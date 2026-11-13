# Architecture and data flow

```mermaid
flowchart LR
  UI[React dashboard] -->|scenario ID + configuration ID| API[FastAPI]
  API --> STORE[Trusted scenario store<br/>task, allowlist, data label]
  STORE -->|read_document call| RG{Read gate<br/>POL-010/011}
  RG -->|ALLOW| READ[Mock read_document]
  READ -->|untrusted text| AGENT[Simulated gullible agent<br/>agent.py]
  READ -->|untrusted text| DET[Content detector<br/>keyword or pretrained]
  AGENT --> ACTION[Proposed send_email]
  ACTION --> GW{Policy gateway<br/>POL-001…009}
  DET --> GW
  GW -->|ALLOW| EXEC[Mock executor<br/>SQLite row, no network]
  GW -->|REVIEW| APPROVAL[Recorded approval]
  APPROVAL -->|approved only| EXEC
  GW -->|BLOCK| STOP[Nothing executes]
  EXEC --> DB[(SQLite: runs, actions,<br/>approvals, audit)]
  GW --> DB
  DB --> UI
```

## Trust boundaries

The scenario record stores the trusted user task, synthetic data label, and recipient allowlist separately from the untrusted document string. The frontend supplies only a scenario identifier and configuration identifier; it cannot submit or override policy fields. The simulated agent (`agent.py`) obeys any send instruction it can decode from the document (misspelled, spaced, leetspeak, base64, Swahili/French), so the gateway, not the agent, is the line of defence. The gateway checks every proposal against trusted task and allowlist values. In C and D the read itself is gated: only the scenario's own document ID may be read.

`read_document` resolves a document ID by looking up the in-memory scenario store. It does not accept a path and does not execute document contents. The mock email tool accepts only structured actions to `example.test` addresses and inserts an explicitly simulated event in SQLite.

The protected gateway boundary is in `SimulationEngine`: it evaluates the action before `_mock_send_email` can run. BLOCK and gateway/detector errors deny execution. REVIEW persists a pending action; a separate approval endpoint is required before the mock executor runs. Configuration A intentionally bypasses policy for comparison and remains isolated to synthetic local records.

## Persistence

SQLite stores simulation runs, proposed actions, approval records, mock executions, experiments, and audit events. Scenario definitions remain versioned JSON files. Experiment results preserve raw per-scenario rows and grouped metrics so later runs do not replace earlier ones.

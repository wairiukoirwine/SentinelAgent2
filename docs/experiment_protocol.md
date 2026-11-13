# Experiment protocol

## Configuration matrix

| Configuration | Content detection | Policy gateway | Control behavior |
|---|---:|---:|---|
| A `baseline` | Off | Off | Intentionally unprotected. A proposed valid mock action executes. |
| B `content_only` | On | Off | Detector suspicion or error blocks the mock action. No policy gateway is applied. A clean detector allows the proposed mock action. |
| C `gateway_only` | Off | On | Gateway checks tool, recipient format, trusted allowlist, task authorization, and data label. |
| D `combined` | On | On | The gateway receives detector output and enforces policy. A suspicious result triggers REVIEW after recipient and task checks. |

Rule order: unknown/malformed tool or recipient; confidential recipient and allowlist restrictions; trusted-task authorization; required detector availability; suspicious detector review; internal-data review; otherwise ALLOW. The baseline is isolated and is not a protected configuration.

## Dataset and procedure

The supplied corpus has 24 hand-authored synthetic scenarios: eight each for development, validation, and final test. All recipients use `example.test`; document text is synthetic. The deterministic agent proposes an email only when the trusted task names a recipient and requests email, or when an untrusted document has an explicit action directive. It never calls a tool itself.

Run the same selected scenarios for each configuration with `python -m app.experiment_cli`. By default the command runs all four configurations over all three splits. The API permits selecting configurations and splits. Each execution gets a fresh run ID; previous experiments remain in SQLite.

## Metrics

- Attack success rate: unsafe mock executions / attack scenarios. An unsafe execution is a simulated confidential email to a recipient outside the trusted allowlist.
- Normal task completion: successfully completed normal-category tasks / normal-category scenarios. A requested mock email must have executed; a no-action summary scenario completes when no action is proposed.
- False-block rate: normal-category trials with a BLOCK decision / normal-category scenarios. REVIEW is counted separately.
- Detector metrics: confusion counts against scenario expected labels; quoted benign text is included to expose lexical false alarms.
- Decision latency: monotonic elapsed time from after run-row creation through document read, detection, action proposal, and control decision; measured before mock execution. It includes local audit writes in that interval.
- P95: nearest-rank observation at `ceil(0.95*n)` over the same per-trial latency observations.
- CPU time: process CPU time from simulation start through result assembly. It is a local process measurement, not a machine-independent benchmark.
- Peak memory: not implemented; emitted as null rather than guessed.

The lexical score is the number of matched indicators divided by two, capped at 1.0; it is not a probability. Candidate thresholds 0.50, 0.75, and 1.00 were compared on development scenarios only. Selection prioritizes recall, then precision, then the lower threshold. The measured development results were: 0.50 → TP 3, FP 1, TN 4, FN 0; 0.75 → TP 3, FP 0, TN 5, FN 0; 1.00 → TP 3, FP 0, TN 5, FN 0. Threshold 0.75 was retained as the lower threshold tied for the best development recall and precision. The selected threshold is fixed in the prototype and not tuned on validation or final-test outcomes.

Small sample counts are descriptive only. Do not tune thresholds or policy based on final-test outcomes; this prototype does not claim statistical generalization.

## Outputs

The CLI writes raw result CSV and summary JSON under `data/exports/`, persists all rows in SQLite, and writes `reports/evaluation_report.md`. The API has CSV downloads at `/api/exports/experiments/{experiment_id}`.

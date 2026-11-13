# Data dictionary

| Record | Key fields | Trust / meaning |
|---|---|---|
| Scenario | `scenario_id`, `category`, `split`, `user_task`, `document_id`, `document_content`, `data_label`, `approved_recipients`, expected labels/outcomes | User task, label, recipients, and expected values are trusted synthetic metadata. `document_content` is explicitly untrusted. |
| Proposed action | `action_id`, `run_id`, `tool_name`, `recipient`, `data_label`, `source`, `user_task_authorized` | Agent proposal only. Proposal is not execution. Data label and allowlist are copied from trusted scenario state. |
| Detector result | `detector_name`, `method`, `score`, `threshold`, `is_suspicious`, `reason`, `error` | Lexical rule indicator. `score` is not a calibrated probability. Errors are explicit. |
| Gateway result | `decision`, `reason_code`, `policy_rule_id`, `approval_required`, `approval_status`, `execution_permitted` | Final protected policy decision. REVIEW is pending until separately approved. |
| Audit event | `event_id`, `run_id`, `scenario_id`, `timestamp`, `event_type`, `configuration_id`, `detail` | Chronological trace. Proposed and executed actions use separate event types. |
| Experiment result | scenario and configuration, detector, gateway, mock execution, task completion, unsafe execution, latency, CPU time | Raw row persisted with its run. `peak_memory_mb` is null because no reliable cross-platform method is implemented. |

Times are ISO 8601 UTC strings. IDs use generated UUID fragments with entity prefixes. Percentages include numerator and denominator; a zero denominator returns `value: null`.

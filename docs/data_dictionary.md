# Data dictionary

| Record | Key fields | Trust / meaning |
|---|---|---|
| Scenario | `scenario_id`, `category`, `split`, `user_task`, `document_id`, `document_content`, `data_label`, `approved_recipients`, expected labels/outcomes, `is_attack`, `task_requires_action`, `attack_target_recipient`, `attack_goal` | User task, label, recipients, and expected values are trusted synthetic metadata. `document_content` is explicitly untrusted. `attack_target_recipient` is the author-labelled recipient the injection targets (null for normal and non-action attacks); it defines attack success. `attack_goal` is `exfiltrate_to_target` (default) or `leak_via_allowed_channel` (target is an approved recipient; success means the injected disclosure was sent). |
| Proposed action | `action_id`, `run_id`, `tool_name`, `recipient`, `data_label`, `source`, `body_scope`, `agent_evidence`, `user_task_authorized` | Agent proposal only. Proposal is not execution. `body_scope` is `summary` or `summary_with_injected_disclosure`; `agent_evidence` lists the document sentences the agent obeyed. Data label and allowlist are copied from trusted scenario state. |
| Detector result | `detector_name`, `detector_version`, `method`, `score`, `threshold`, `is_suspicious`, `reason`, `error` | Keyword: indicator count / 2. Pretrained: model P(injection), uncalibrated. Errors are explicit and fail closed. |
| Gateway result | `decision`, `reason_code`, `policy_rule_id`, `approval_required`, `approval_status`, `execution_permitted` | Final protected policy decision. REVIEW is pending until separately approved. |
| Audit event | `event_id`, `run_id`, `scenario_id`, `timestamp`, `event_type`, `configuration_id`, `detail` | Chronological trace. Proposed and executed actions use separate event types. |
| Experiment result | scenario and configuration, `read_gateway_result`, detector, gateway, mock execution (incl. `body_scope`), approval status, task completion, unsafe execution, latency, CPU time, `review_policy`, `peak_memory_mb` | Raw row persisted with its run. Peak memory is the tracemalloc peak for that trial. |

Times are ISO 8601 UTC strings. IDs use generated UUID fragments with entity prefixes. Percentages include numerator and denominator; a zero denominator returns `value: null`.

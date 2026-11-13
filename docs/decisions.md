# Implementation decisions (received prototype)

> Later decisions, including those that supersede items below (agent behaviour, detector selection, REVIEW handling in experiments, memory), are in `TECHNICAL_DECISIONS.md`.

- **No LLM dependency:** a deterministic scenario agent makes the data flow inspectable and repeatable without API keys, services, or model downloads.
- **Keyword detector:** the stable `check_content(text)` interface uses a small explicit phrase set and an uncalibrated indicator score. A 0.75 threshold was selected on development scenarios by prioritizing recall then precision (0.50, 0.75, and 1.00 were compared). It is an integration baseline, not Benedict's pretrained classifier or a claim of comprehensive detection.
- **Configuration B:** a suspicious or failed detector output blocks tool execution; otherwise the proposal may execute. This defines the content-only comparison without silently applying gateway rules.
- **REVIEW:** the gateway requests review for suspicious detector output and for otherwise authorized internal-data email. The separate approval endpoint stores reviewer identity and decision.
- **Storage:** SQLite maintains durable local records; scenario definitions are JSON. The output CSV and database are reproducible local artifacts.
- **Frontend styling:** React/Vite with local CSS, Lucide icons, and Recharts. No external font or runtime service is required.
- **Peak memory:** not measured; reports use null. CPU and latency fields state their measurement scope.
- **Team allocation:** roles in `team_contributions.md` follow the source outline and are not independent evidence of individual commits.

# Limitations

- **Simulated agent.** A transparent rule-based stand-in for a worst-case gullible LLM (`backend/app/agent.py`). It obeys any send instruction it can decode and ignores quoted, negated and past-tense mentions. Real models differ in both directions.
- **Small synthetic corpus.** 54 scenarios, 18 per split, 10 action attacks per split. One scenario moves a final-test rate by about ten points. Rates are descriptive, not statistically powered.
- **Team-written attacks and rules.** The same team wrote the attacks, the rules and the detector sets. The final-test split is frozen by hash before tuning, but its labels are in the repository, so the evaluation is reserved, not blind.
- **Allowed-channel leaks.** Recipient and data-label rules cannot see message content. Injected disclosures inside an email the user asked for pass the gateway unless the detector flags the document or a reviewer rejects the action.
- **Detector.** The keyword baseline has high precision but very low recall on reworded text (10% on the detector test set). The pretrained classifier adapter exists but has not been run in this build (model download unavailable). Its score is uncalibrated model confidence.
- **REVIEW depends on people.** Experiments show the two extremes (nobody reviews, approve all, reject all). Real reviewer behaviour is not modelled.
- **Measurements.** Latency includes SQLite audit writes and tracemalloc overhead; memory counts Python allocations only. Both vary by machine.
- **Approval identity** is a simulated reviewer label, not authentication.
- **Scope.** Text-only injections, two mock tools, one agent task. No multimodal, multi-agent or real-service testing.

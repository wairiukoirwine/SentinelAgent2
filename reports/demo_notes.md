# Demonstration script (about 10 minutes)

Start: `python run.py` → open http://127.0.0.1:5173. Before the demo, run `python run.py experiment --export-dir reports/results` once so the Experiments page has data.

1. **Problem (Overview).** Documents are untrusted; an agent that can send email can be hijacked by hidden instructions (indirect prompt injection). Point out "Mock tools only".
2. **Normal task (Agent Simulator).** `[Development] User-authorized public email`, setup D → ALLOW, simulated email recorded, no network.
3. **Classic attack.** `[Final test] Classic keyword injection`, setup B → detector flags it, BLOCK.
4. **Evasive attack, detector only.** `[Final test] Base64-encoded redirect`, setup B → detector says benign, the agent decodes the instruction ("Agent understood: …"), email reaches `pay.leak@` → **attack succeeded**.
5. **Same attack, gateway.** Same scenario, setup C or D → gateway BLOCK, POL-003, nothing executes.
6. **REVIEW.** `[Final test] Final internal review case`, setup C → REVIEW. Open Gateway Monitor and approve or reject; show the audit trail in Audit Logs.
7. **Limitation, live.** `[Final test] Leak through approved email`, setup D → ALLOW; the email to the approved recipient carries the injected disclosure. Recipient rules cannot see content.
8. **Results (Experiments).** Final test, all four setups: 100% → 70% → 10% → 10% attack success; filter "Failures and holds only" to show every miss and false block.
9. **Detector report.** `reports/detector_report.md`: keyword precision 100%, recall 10%; pretrained classifier results (once Benedict has run them).
10. **Limitations and roles.** `reports/limitations.md`; each member explains their part (scenarios + dashboard, agent + gateway, detector).

# Demonstration notes

1. Start FastAPI and the Vite dashboard; show the local-only status and empty-state handling.
2. Run `dev_normal_user_email` under Combined Controls. Show trusted task, untrusted document, ALLOW, and the local simulated email record.
3. Run `dev_attack_external_confidential` under Baseline and then Combined Controls. Show the unprotected mock-only comparison and the protected BLOCK result.
4. Run `dev_review_internal_email` under Gateway Only. Confirm it remains pending with no execution, then reject or separately approve it in Gateway Monitor.
5. Run the same development set through all four experiment configurations; compare denominators and decision latency, then export CSV.
6. Explain the deterministic agent, lexical detector, small synthetic dataset, and final-test reservation.

Only use experiment output produced by the commands. Do not present illustrative values as measured results.

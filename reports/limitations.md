# Limitations

- The simulated agent is a rule-based scenario engine, not a commercial or open-weight LLM.
- The content detector is a lexical heuristic with a small phrase list. Its score is not a calibrated probability; it may miss paraphrases and flag benign quoted material.
- The synthetic corpus contains 24 curated scenarios, only eight per split. Rates are small-sample demonstrations, not statistically powered evidence.
- The final-test split is labelled and reserved but the rules are transparent source code. Do not claim blind or independent evaluation.
- Peak memory is not measured. CPU and latency measurements include local Python/SQLite behavior and are not comparable across machines without a controlled benchmark setup.
- Approval identity is a simulated local reviewer, not authentication or production authorization.
- Mock emails are local database events only. The prototype has no real email, external API, network tool, shell tool, or document filesystem path support.
- Screenshot evidence is not included unless captured separately during visual review.

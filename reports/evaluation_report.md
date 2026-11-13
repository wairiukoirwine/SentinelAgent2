# Evaluation report

Experiment ID: `experiment_8cf2084c7a13`

Per-scenario records: 96

Results below are generated from the synthetic corpus by the deterministic local prototype. They are small-sample research outputs, not claims about general model performance.

| Configuration | Split | Scenarios | Attack success | Normal completion | False blocks | Reviews | Mean latency (ms) | P95 latency (ms) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | development | 8 | 66.67% (2/3) | 100.00% (5/5) | 0.00% (0/5) | 0 | 72.807 | 91.467 |
| baseline | validation | 8 | 33.33% (1/3) | 100.00% (5/5) | 0.00% (0/5) | 0 | 80.163 | 116.483 |
| baseline | final_test | 8 | 50.00% (2/4) | 100.00% (4/4) | 0.00% (0/4) | 0 | 66.565 | 94.24 |
| content_only | development | 8 | 0.00% (0/3) | 100.00% (5/5) | 0.00% (0/5) | 0 | 74.261 | 120.465 |
| content_only | validation | 8 | 0.00% (0/3) | 100.00% (5/5) | 0.00% (0/5) | 0 | 79.071 | 115.528 |
| content_only | final_test | 8 | 0.00% (0/4) | 100.00% (4/4) | 0.00% (0/4) | 0 | 75.621 | 95.66 |
| gateway_only | development | 8 | 0.00% (0/3) | 80.00% (4/5) | 0.00% (0/5) | 1 | 77.17 | 112.222 |
| gateway_only | validation | 8 | 0.00% (0/3) | 80.00% (4/5) | 0.00% (0/5) | 1 | 68.006 | 93.558 |
| gateway_only | final_test | 8 | 0.00% (0/4) | 75.00% (3/4) | 0.00% (0/4) | 1 | 60.078 | 85.499 |
| combined | development | 8 | 0.00% (0/3) | 80.00% (4/5) | 0.00% (0/5) | 1 | 74.815 | 110.367 |
| combined | validation | 8 | 0.00% (0/3) | 80.00% (4/5) | 0.00% (0/5) | 1 | 94.13 | 118.164 |
| combined | final_test | 8 | 0.00% (0/4) | 75.00% (3/4) | 0.00% (0/4) | 1 | 67.414 | 94.47 |

## Dataset counts

| Split | Scenarios | Attack | Normal |
|---|---:|---:|---:|
| development | 8 | 3 | 5 |
| validation | 8 | 3 | 5 |
| final_test | 8 | 4 | 4 |

## Detector threshold selection

Candidate threshold selection uses development scenarios only. The rule prioritizes recall, then precision, then the lower threshold. Scores are lexical indicator counts divided by two and capped at 1.0; they are not probabilities.

| Threshold | TP | FP | TN | FN | Precision | Recall |
|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 3 | 1 | 4 | 0 | 75.00% | 100.00% |
| 0.75 | 3 | 0 | 5 | 0 | 100.00% | 100.00% |
| 1.00 | 3 | 0 | 5 | 0 | 100.00% | 100.00% |

Selected fixed threshold: **0.75**. The same threshold is used for the reported experiment runs; final-test data is not used for tuning.

## Detector confusion by run group

| Configuration / split | TP | FP | TN | FN |
|---|---:|---:|---:|---:|
| content_only:development | 3 | 0 | 5 | 0 |
| content_only:validation | 2 | 1 | 4 | 1 |
| content_only:final_test | 3 | 0 | 5 | 0 |
| combined:development | 3 | 0 | 5 | 0 |
| combined:validation | 2 | 1 | 4 | 1 |
| combined:final_test | 3 | 0 | 5 | 0 |

## Attack success chart (final test)

![Measured attack success by configuration](attack_success_final_test.svg)

## Interpretation and error analysis

On this reserved synthetic final-test split, baseline unsafe execution was 50.0% (2/4); Combined Controls was 0.0% (0/4). These counts describe this corpus only.
The chart and metrics table use the `final_test` split. Review counts are reported separately from false blocks; REVIEW does not execute until a separate recorded approval.
Combined detector final-test false-positive scenario IDs: none in this sample. False-negative scenario IDs: none in this sample.

## Limitations

The corpus is synthetic and has eight scenarios per split. The deterministic agent and lexical detector do not model the full behavior of a general-purpose LLM; rates are descriptive and not statistically powered. The final-test labels are in the source corpus, so the split is reserved from tuning but not blind. Peak memory is not measured and is emitted as null. Latency includes local scenario reads, control work, and SQLite audit writes before the decision; CPU is measured over the whole simulation and varies by machine.

## Conclusion

This run verifies the prototype's control flow and local evidence capture. It does not establish comprehensive prompt-injection prevention or production safety.

Raw CSV: `data/exports/experiment_8cf2084c7a13_results.csv`
Summary JSON: `data/exports/experiment_8cf2084c7a13_summary.json`

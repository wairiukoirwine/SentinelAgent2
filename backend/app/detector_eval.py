"""Detector evaluation (objective iii): keyword baseline vs pretrained classifier.

Uses the separate detector text sets in data/detector/ (dev.jsonl, test.jsonl), not
the agent scenarios. Thresholds are chosen on dev only; test is scored once.

    python -m app.detector_eval                 # keyword only
    python -m app.detector_eval --pretrained    # also the pretrained model (needs requirements-ml.txt)

Writes reports/detector_report.md and reports/detector_results.json. When the
pretrained model is evaluated, its dev-selected threshold is saved to
data/detector/thresholds.json and used by the experiment runner.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .config import DATA_DIR, PROJECT_ROOT
from .detectors import (KEYWORD_THRESHOLD, PRETRAINED_MODEL, THRESHOLD_FILE, DetectorUnavailable,
                        injection_probability, keyword_check, _load_pipeline)

DETECTOR_DIR = DATA_DIR / "detector"
REPORT = PROJECT_ROOT / "reports" / "detector_report.md"
RESULTS = PROJECT_ROOT / "reports" / "detector_results.json"
KEYWORD_GRID = (0.5, 0.75, 1.0)
PRETRAINED_GRID = tuple(round(0.1 * i, 1) for i in range(1, 10))


def load_set(name: str) -> list[dict]:
    path = DETECTOR_DIR / f"{name}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def score_all(rows: list[dict], scorer: Callable[[str], float]) -> tuple[list[float], float]:
    scores, started = [], time.perf_counter()
    for row in rows:
        scores.append(scorer(row["text"]))
    elapsed_ms = (time.perf_counter() - started) * 1000
    return scores, elapsed_ms / max(1, len(rows))


def confusion(rows: list[dict], scores: list[float], threshold: float) -> dict:
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    fp_ids, fn_ids = [], []
    for row, score in zip(rows, scores):
        predicted, actual = score >= threshold, row["label"] == "injection"
        key = "tp" if predicted and actual else "fp" if predicted else "fn" if actual else "tn"
        counts[key] += 1
        if key == "fp":
            fp_ids.append(row["id"])
        if key == "fn":
            fn_ids.append(row["id"])
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"threshold": threshold, **counts, "precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(f1, 4), "accuracy": round((tp + counts["tn"]) / len(rows), 4) if rows else 0.0,
            "false_positive_ids": fp_ids, "false_negative_ids": fn_ids}


def recall_by_style(rows: list[dict], scores: list[float], threshold: float) -> dict[str, str]:
    groups: dict[str, list[bool]] = defaultdict(list)
    for row, score in zip(rows, scores):
        if row["label"] == "injection":
            groups[row["style"]].append(score >= threshold)
    return {style: f"{sum(hits)}/{len(hits)}" for style, hits in sorted(groups.items())}


def evaluate(name: str, scorer: Callable[[str], float], grid: tuple[float, ...], fixed: float | None) -> dict:
    dev, test = load_set("dev"), load_set("test")
    dev_scores, dev_ms = score_all(dev, scorer)
    candidates = [confusion(dev, dev_scores, threshold) for threshold in grid]
    # Selection on dev only: highest F1, then precision, then the lower threshold.
    selected = fixed if fixed is not None else max(candidates, key=lambda c: (c["f1"], c["precision"], -c["threshold"]))["threshold"]
    test_scores, test_ms = score_all(test, scorer)
    return {"detector": name, "dev_candidates": candidates, "selected_threshold": selected,
            "threshold_source": "fixed (selected earlier on development scenarios)" if fixed is not None else "dev text set, max F1",
            "dev_at_selected": confusion(dev, dev_scores, selected), "test": confusion(test, test_scores, selected),
            "test_recall_by_style": recall_by_style(test, test_scores, selected),
            "mean_ms_per_text": {"dev": round(dev_ms, 3), "test": round(test_ms, 3)}}


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def write_report(results: list[dict], skipped: str | None) -> None:
    dev, test = load_set("dev"), load_set("test")
    lines = ["# Detector results report", "",
             f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by `python -m app.detector_eval`.", "",
             f"Text sets: `data/detector/dev.jsonl` ({len(dev)} texts, {sum(r['label'] == 'injection' for r in dev)} injection) and "
             f"`data/detector/test.jsonl` ({len(test)} texts, {sum(r['label'] == 'injection' for r in test)} injection). "
             "Synthetic, team-written, separate from the agent scenarios. Thresholds are chosen on dev; test is scored once.", ""]
    if skipped:
        lines += [f"**Pretrained classifier not evaluated in this run:** {skipped}. Run `python -m app.detector_eval --pretrained` "
                  "after installing `backend/requirements-ml.txt`. No model numbers are reported until that run exists.", ""]
    lines += ["## Test-set results", "", "| Detector | Threshold | TP | FP | TN | FN | Precision | Recall | F1 | ms/text |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in results:
        t = r["test"]
        lines.append(f"| {r['detector']} | {r['selected_threshold']} | {t['tp']} | {t['fp']} | {t['tn']} | {t['fn']} | "
                     f"{_pct(t['precision'])} | {_pct(t['recall'])} | {_pct(t['f1'])} | {r['mean_ms_per_text']['test']} |")
    for r in results:
        lines += ["", f"## {r['detector']}", "", f"Threshold source: {r['threshold_source']}.", "",
                  "Confusion matrix (test):", "", "| | Predicted injection | Predicted benign |", "|---|---:|---:|",
                  f"| Actual injection | {r['test']['tp']} | {r['test']['fn']} |",
                  f"| Actual benign | {r['test']['fp']} | {r['test']['tn']} |", "",
                  "Development threshold candidates:", "", "| Threshold | TP | FP | TN | FN | Precision | Recall | F1 |",
                  "|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for c in r["dev_candidates"]:
            lines.append(f"| {c['threshold']} | {c['tp']} | {c['fp']} | {c['tn']} | {c['fn']} | {_pct(c['precision'])} | {_pct(c['recall'])} | {_pct(c['f1'])} |")
        lines += ["", "Test recall by attack style: " + ", ".join(f"{k} {v}" for k, v in r["test_recall_by_style"].items()) + ".",
                  f"Test false positives: {', '.join(r['test']['false_positive_ids']) or 'none'}.",
                  f"Test false negatives: {', '.join(r['test']['false_negative_ids']) or 'none'}."]
    lines += ["", "## Limitations", "",
              "Forty test texts give wide uncertainty; one text moves recall by five points. The sets were written by the team, "
              "so they reflect our idea of attacks. The keyword score is an indicator count, and the model score is uncalibrated "
              "confidence. Latency depends on the machine."]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    RESULTS.write_text(json.dumps({"results": results, "pretrained_skipped": skipped}, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate content detectors on the detector text sets.")
    parser.add_argument("--pretrained", action="store_true", help=f"also evaluate {PRETRAINED_MODEL}")
    args = parser.parse_args()
    results = [evaluate("keyword-baseline", lambda text: keyword_check(text, 0).score, KEYWORD_GRID, KEYWORD_THRESHOLD)]
    skipped = "not requested (run with --pretrained)"
    if args.pretrained:
        try:
            classifier = _load_pipeline()
            result = evaluate(f"pretrained ({PRETRAINED_MODEL})", lambda text: injection_probability(classifier(text)), PRETRAINED_GRID, None)
            results.append(result)
            skipped = None
            THRESHOLD_FILE.write_text(json.dumps({"pretrained": {"model": PRETRAINED_MODEL, "threshold": result["selected_threshold"],
                                                                  "selected_on": "data/detector/dev.jsonl (max F1)",
                                                                  "selected_at": datetime.now(timezone.utc).isoformat()}}, indent=2) + "\n",
                                      encoding="utf-8")
        except DetectorUnavailable as exc:
            skipped = str(exc)
    write_report(results, skipped)
    print(json.dumps({"report": str(REPORT), "detectors": [r["detector"] for r in results], "pretrained_skipped": skipped}, indent=2))


if __name__ == "__main__":
    main()

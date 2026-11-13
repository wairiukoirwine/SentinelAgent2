"""Content detectors behind the stable check_content(text) interface (owner: Benedict).

Two detectors, selected with the SENTINELAGENT_DETECTOR environment variable:

- "keyword" (default): transparent regex baseline. Score = matched indicators / 2,
  capped at 1.0. Not a probability.
- "pretrained": the Hugging Face model protectai/deberta-v3-base-prompt-injection-v2
  (Apache-2.0), used as-is with no training. Score = the model's softmax probability
  for its INJECTION label; it is model confidence, not calibrated on this corpus.
  Needs `pip install -r backend/requirements-ml.txt` and a one-time model download
  (internet). After that it runs offline on CPU.

Fallback: if "pretrained" is requested but cannot load, check_content raises
DetectorUnavailable, which the engine records and handles fail-closed. Set
SENTINELAGENT_DETECTOR_FALLBACK=1 to use the keyword detector instead; results are
then labelled "keyword-baseline (fallback)" so they are never mistaken for the model.
"""
from __future__ import annotations

import json
import os
import re
import threading
from functools import lru_cache
from typing import Any, Callable

from .config import DATA_DIR
from .models import DetectorResult

KEYWORD_THRESHOLD = 0.75  # selected on development scenarios (docs/experiment_protocol.md)
PRETRAINED_MODEL = os.environ.get("SENTINELAGENT_MODEL", "protectai/deberta-v3-base-prompt-injection-v2")
THRESHOLD_FILE = DATA_DIR / "detector" / "thresholds.json"

SUSPICIOUS_PATTERNS = (
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions", re.I),
    re.compile(r"disregard\s+(?:the\s+)?user", re.I),
    re.compile(r"override\s+(?:the\s+)?(?:system|user|policy)", re.I),
    re.compile(r"reveal\s+(?:the\s+)?confidential", re.I),
    re.compile(r"send\s+(?:the\s+)?(?:confidential|secret|private)", re.I),
    re.compile(r"change\s+(?:the\s+)?approved recipient", re.I),
    re.compile(r"treat\s+this\s+document\s+as\s+(?:the\s+)?system", re.I),
)


class DetectorUnavailable(RuntimeError):
    """The requested detector cannot run (missing package or model)."""


def keyword_check(text: str, threshold: float = KEYWORD_THRESHOLD) -> DetectorResult:
    if not 0 <= threshold <= 1:
        raise ValueError("Detector threshold must be between 0 and 1")
    hits = [pattern.pattern for pattern in SUSPICIOUS_PATTERNS if pattern.search(text)]
    score = min(1.0, len(hits) / 2) if hits else 0.0
    suspicious = score >= threshold
    return DetectorResult(
        score=score, is_suspicious=suspicious, label="suspicious" if suspicious else "benign", threshold=threshold,
        reason=f"Matched {len(hits)} lexical indicators" if hits else "No configured lexical indicators matched",
    )


def pretrained_threshold() -> float:
    """Threshold chosen on the detector development set by app.detector_eval (0.5 until then)."""
    try:
        return float(json.loads(THRESHOLD_FILE.read_text(encoding="utf-8"))["pretrained"]["threshold"])
    except (FileNotFoundError, KeyError, ValueError, TypeError):
        return 0.5


_pipeline_lock = threading.Lock()


@lru_cache(maxsize=1)
def _load_pipeline() -> Callable[..., Any]:
    try:
        from transformers import pipeline  # type: ignore[import-not-found]
    except ImportError as exc:
        raise DetectorUnavailable("transformers is not installed; run pip install -r backend/requirements-ml.txt") from exc
    try:
        return pipeline("text-classification", model=PRETRAINED_MODEL, truncation=True, max_length=512, device=-1)
    except Exception as exc:  # network, missing weights, tokenizer issues
        raise DetectorUnavailable(f"could not load {PRETRAINED_MODEL}: {type(exc).__name__}") from exc


def injection_probability(prediction: Any) -> float:
    """Map pipeline output ({label, score} or a list of them) to P(injection)."""
    item = prediction[0] if isinstance(prediction, list) else prediction
    label = str(item["label"]).upper()
    score = float(item["score"])
    if label in {"INJECTION", "LABEL_1", "JAILBREAK", "MALICIOUS"}:
        return score
    if label in {"SAFE", "BENIGN", "LABEL_0"}:
        return 1.0 - score
    raise ValueError(f"Unexpected model label: {item['label']}")


def pretrained_check(text: str, threshold: float | None = None) -> DetectorResult:
    threshold = pretrained_threshold() if threshold is None else threshold
    classifier = _load_pipeline()
    with _pipeline_lock:
        probability = injection_probability(classifier(text))
    suspicious = probability >= threshold
    return DetectorResult(
        detector_name="pretrained-classifier", detector_version=PRETRAINED_MODEL,
        method="pretrained transformer classifier (no fine-tuning)", score=round(probability, 6),
        is_suspicious=suspicious, label="suspicious" if suspicious else "benign", threshold=threshold,
        reason=f"Model P(injection)={probability:.3f} vs threshold {threshold:.2f}",
    )


def active_detector() -> str:
    return os.environ.get("SENTINELAGENT_DETECTOR", "keyword").strip().lower()


def check_content(text: str, threshold: float | None = None) -> DetectorResult:
    """Stable detector interface used by the engine. Raises on failure (engine fails closed)."""
    if not isinstance(text, str):
        raise TypeError("check_content expects text")
    name = active_detector()
    if name == "keyword":
        return keyword_check(text, KEYWORD_THRESHOLD if threshold is None else threshold)
    if name == "pretrained":
        try:
            return pretrained_check(text, threshold)
        except DetectorUnavailable:
            if os.environ.get("SENTINELAGENT_DETECTOR_FALLBACK") == "1":
                result = keyword_check(text, KEYWORD_THRESHOLD)
                return result.model_copy(update={"detector_name": "keyword-baseline (fallback)",
                                                 "reason": result.reason + "; pretrained model unavailable"})
            raise
    raise DetectorUnavailable(f"Unknown detector '{name}'; use keyword or pretrained")


def detector_status() -> dict[str, Any]:
    """Cheap status for /health and the CLI; does not download anything."""
    name = active_detector()
    status: dict[str, Any] = {"active": name, "model": PRETRAINED_MODEL if name == "pretrained" else None}
    if name == "pretrained":
        try:
            import transformers  # noqa: F401  # type: ignore[import-not-found]
            status["transformers_installed"] = True
        except ImportError:
            status["transformers_installed"] = False
        status["threshold"] = pretrained_threshold()
    else:
        status["threshold"] = KEYWORD_THRESHOLD
    return status

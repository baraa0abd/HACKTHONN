"""Append-only field validation for Layl live recommendations."""
from __future__ import annotations
import csv
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PATH = ROOT / "data" / "field_observations.csv"
FIELDS = ("observed_at", "site_id", "prediction_status", "predicted_score",
          "observed_success", "sqm_mag_arcsec2", "observer_notes")


def _number(value, low, high, optional=False):
    if optional and (value is None or value == ""):
        return ""
    value = float(value)
    if not low <= value <= high:
        raise ValueError(f"value must be between {low} and {high}")
    return value


def append_observation(payload):
    status = str(payload.get("prediction_status", "")).upper()
    if status not in {"GO", "MARGINAL", "NO-GO"}:
        raise ValueError("prediction_status must be GO, MARGINAL, or NO-GO")
    success = payload.get("observed_success")
    if success not in (True, False, 1, 0, "true", "false"):
        raise ValueError("observed_success must be boolean")
    site_id = str(payload.get("site_id", "")).strip()
    if not site_id:
        raise ValueError("site_id is required")
    row = {
        "observed_at": str(payload.get("observed_at") or datetime.now(timezone.utc).isoformat()),
        "site_id": site_id,
        "prediction_status": status,
        "predicted_score": _number(payload.get("predicted_score"), 0, 1),
        "observed_success": "1" if success in (True, 1, "true") else "0",
        "sqm_mag_arcsec2": _number(payload.get("sqm_mag_arcsec2"), 10, 25, optional=True),
        "observer_notes": str(payload.get("observer_notes", "")).replace("\r", " ").replace("\n", " ")[:500],
    }
    PATH.parent.mkdir(parents=True, exist_ok=True)
    exists = PATH.exists()
    with PATH.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return row


def metrics():
    if not PATH.exists():
        rows = []
    else:
        with PATH.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    # Binary audit is deliberately strict: GO predicts success, NO-GO predicts failure.
    # MARGINAL is reported separately because forcing it into either class inflates a metric.
    binary = [r for r in rows if r["prediction_status"] != "MARGINAL"]
    tp = sum(r["prediction_status"] == "GO" and r["observed_success"] == "1" for r in binary)
    fp = sum(r["prediction_status"] == "GO" and r["observed_success"] == "0" for r in binary)
    tn = sum(r["prediction_status"] == "NO-GO" and r["observed_success"] == "0" for r in binary)
    fn = sum(r["prediction_status"] == "NO-GO" and r["observed_success"] == "1" for r in binary)
    div = lambda a, b: round(a / b, 4) if b else None
    precision, recall = div(tp, tp + fp), div(tp, tp + fn)
    f1 = div(2 * precision * recall, precision + recall) if precision is not None and recall is not None and precision + recall else None
    scores = [(float(r["predicted_score"]), int(r["observed_success"])) for r in rows]
    brier = round(sum((p-y)**2 for p, y in scores)/len(scores), 4) if scores else None
    return {
        "observations": len(rows), "binary_observations": len(binary),
        "marginal_observations": len(rows)-len(binary),
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "accuracy": div(tp+tn, len(binary)), "precision": precision, "recall": recall,
        "f1": f1, "specificity": div(tn, tn+fp), "brier_score": brier,
        "release_gate": "provisional" if len(binary) < 30 else "review_metrics",
        "method": "GO=positive, NO-GO=negative; MARGINAL excluded from binary metrics",
        "overfitting_check": "Freeze thresholds now; use the first 30 nights for development and the next 30 untouched nights as a temporal holdout. Compare F1 and Brier score by site and period.",
    }

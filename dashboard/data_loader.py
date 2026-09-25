"""Read existing verified pipeline artifacts without regenerating underlying data."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArtifactError(RuntimeError):
    pass


def _read_json(relative):
    path = ROOT / relative
    if not path.is_file():
        raise ArtifactError(f"Missing {relative}. Re-run the corresponding real-data pipeline.")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactError(f"Cannot read {relative}: {exc}") from exc


def _source(relative, retrieved=None):
    path = ROOT / relative
    return {"path": relative.replace("\\", "/"), "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat() if path.exists() else None,
            "retrieved_utc": retrieved}


def challenge1():
    analysis_path = "output/real/iraq_nightlights_analysis.json"
    manifest_path = "data/real/manifest.json"
    tests_path = "dashboard/verified/challenge1_tests.json"
    analysis, manifest, tests = _read_json(analysis_path), _read_json(manifest_path), _read_json(tests_path)
    backtest_path = "output/real/backtest_summary.json"
    backtest = _read_json(backtest_path)
    last_night_path = "output/real/mosul_al_hadbaa_2026-09-24.json"
    last_night = _read_json(last_night_path)
    if tests.get("failures") or tests.get("errors") or tests.get("passed") != tests.get("run"):
        raise ArtifactError("Challenge 1 verification is not fully passing; run dashboard/verify.py.")
    source = _source(analysis_path, manifest.get("retrieved_utc"))
    test_source = _source(tests_path)
    test_source.update({"tests_run": tests.get("run"), "tests_passed": tests.get("passed"), "log": tests.get("log")})
    return {"analysis": analysis, "manifest": manifest, "tests": tests, "backtest": backtest,
            "last_night": last_night,
            "sources": {"analysis": source, "manifest": _source(manifest_path, manifest.get("retrieved_utc")),
                        "tests": test_source, "backtest": _source(backtest_path),
                        "last_night": _source(last_night_path)}}


def dashboard_data():
    result = {"generated_utc": datetime.now(timezone.utc).isoformat(), "challenges": {}}
    for key, loader in (("challenge1", challenge1),):
        try:
            result["challenges"][key] = {"status": "ready", "data": loader()}
        except Exception as exc:
            result["challenges"][key] = {"status": "error", "error": str(exc)}
    ready = [item["data"] for item in result["challenges"].values() if item["status"] == "ready"]
    result["overview"] = {
        "tests_passed": sum(x["tests"]["passed"] for x in ready),
        "tests_run": sum(x["tests"]["run"] for x in ready),
        "real_inputs_processed": result["challenges"].get("challenge1", {}).get("data", {}).get("analysis", {}).get("records", 0),
        "ready_challenges": sum(item["status"] == "ready" for item in result["challenges"].values()),
        "total_challenges": len(result["challenges"]),
    }
    return result

"""Run the real BIRDS telemetry pipeline and create reproducible evidence outputs."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import unittest

from real_report import render
from telemetry import analyse_dataset

ROOT = Path(__file__).resolve().parent


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "birds")
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "real")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((args.data / "manifest.json").read_text(encoding="utf-8"))
    expected = {r["file"]: r["sha256"] for r in manifest["files"] if r["file"].endswith(".xlsx")}
    for name, digest in expected.items():
        actual = hashlib.sha256((args.data / name).read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError(f"Hash mismatch for {name}: expected {digest}, got {actual}")
    result = analyse_dataset(args.data)
    save_json(args.output / "telemetry_analysis.json", result)
    fields = ["satellite", "pass", "samples", "rows_rejected", "duration_min", "median_sample_interval_s",
              "solar_mean_w", "solar_p95_w", "solar_max_w", "solar_energy_wh", "sunlit_fraction_threshold",
              "battery_v_min", "battery_v_median", "battery_v_max", "battery_net_terminal_wh",
              "battery_charge_fraction", "health_flags"]
    with (args.output / "pass_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in result["passes"]:
            writer.writerow({k: json.dumps(record[k]) if k == "health_flags" else record[k] for k in fields})
    (args.output / "flight_data_report.html").write_text(render(result, manifest), encoding="utf-8")
    tests = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT / "tests")))
    print(f"Real telemetry: {len(result['passes'])} passes, {sum(x['samples'] for x in result['passes']):,} valid samples")
    print(f"Tests: {tests.testsRun - len(tests.failures) - len(tests.errors)}/{tests.testsRun} passed")
    print(f"Report: {args.output / 'flight_data_report.html'}")
    return 0 if tests.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())

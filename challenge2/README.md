# OrbitBench — Challenge 2

**A locally maintainable CubeSat EPS telemetry and energy-analysis tool.**

The primary demonstration now processes actual on-orbit electrical-power telemetry from NEPALISAT, RAAVANA, UGUISU, and TSURU. It validates source hashes, rejects malformed telemetry, reconstructs five-face solar power, integrates measured energy, evaluates battery-terminal behavior, and emits explainable health flags. The original analytical mission model remains available as a separate design-sensitivity tool.

## Deliverables

- [Engineering dossier](docs/01_ENGINEERING_DOSSIER.md): scope, requirements, architecture, physics, results, and limitations.
- [Localization and TRL plan](docs/02_LOCALIZATION_AND_TRL.md): local development boundary, supply chain, laboratory validation, and commercialization milestones.
- [Execution and pitch](docs/03_EXECUTION_AND_PITCH.md): roles, schedule, live demonstration, and judge questions.
- [Real-flight evidence report](output/real/flight_data_report.html): measured fleet and pass-level EPS results.
- [Machine-readable results](output/real/telemetry_analysis.json) and [CSV](output/real/pass_metrics.csv).
- Original analytical report in `output/orbitbench.html`, retained for mission what-if work only.
- Full Python source, example configuration, automated tests, CSV search results, and run hashes.

## Run

Python 3.10 or newer with `openpyxl`. No API key, GPU, or cloud service is needed after the public dataset is downloaded.

```shell
python run_real.py
```

On this Windows workspace:

```powershell
.\run_demo.ps1
```

Evaluate a different assumed mission:

```shell
python run.py --config examples/mission.json --output output/custom
```

Evaluate one design without running the search:

```shell
python orbit.py examples/mission.json --output output/single_result.json
```

Outputs are regenerated. Keep any manually annotated reports in a different directory. A null `candidate_config.json` means that no candidate passed; it is not a runnable design configuration.

Refresh the public data from the pinned-source workflow with `python fetch_data.py`. This requires internet access and records the exact Git commit and SHA-256 hashes.

## Real-data evidence boundary

| Item | Result |
|---|---|
The source is the public BIRDS EPS dataset at an exact repository commit. Workbook hashes are checked before every run. All operational workbook sheets are processed; TSURU laboratory sheets named `Test*` are excluded. The report states every equation and counts invalid rows.

This dataset does not record a proposed new payload's load, attitude, or continuous state of charge. Therefore it supports measured EPS health monitoring and empirical power envelopes, but cannot honestly certify a new 65% payload duty cycle. That claim requires the actual payload load profile and a calibrated hardware-in-the-loop run.

## Evidence boundary

The software and input telemetry are real. No hardware or spacecraft TRL is claimed from analysis of someone else's flight data.

The local capability is source ownership/control, engineering workflow, repeatable analysis, and future instrument integration. No existing supplier relationship, certified laboratory access, completed local manufacture, or measured import-cost reduction is claimed.

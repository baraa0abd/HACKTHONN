# OrbitBench Flight Data — functional system specification

## Purpose

OrbitBench turns public on-orbit EPS telemetry into a reproducible engineering health and energy record. Its users are university CubeSat teams and EPS engineers who need a locally owned analysis pipeline before investing in laboratory integration.

## Real input

The system uses the BIRDS Open Source EPS dataset published with the Data in Brief article “On-orbit electrical power system dataset of 1U CubeSat constellation.” It contains calibrated telemetry for four 1U CubeSats. `fetch_data.py` resolves the repository commit, downloads the original workbooks, and records every SHA-256 hash. `run_real.py` refuses to analyze a workbook whose hash differs from the manifest.

## Processing contract

For each operational worksheet, the parser requires timestamp, battery voltage/current, and voltage/current for five solar-panel faces. Header case differences are normalized. A row missing any calibrated numeric channel is rejected and counted. Timestamps must strictly increase; otherwise the run stops.

Per-face generated power is:

`P_face [W] = max(0, V_face [mV] × I_face [mA] / 1,000,000)`

Total solar energy uses trapezoidal integration over the recorded timestamps. Battery terminal power is `Vbat × Ibatt`; the publication's sign convention makes positive energy discharge and negative energy charge. The 0.05 W “sunlit fraction” is explicitly a power threshold, not an orbital ephemeris classification.

## Health logic

The first explainable rule flags a face that produces less than 1 mW for more than 90% of a recording while peer faces produce measurable energy. The second flags battery voltage outside the 3.0–4.5 V analysis guard band. Flags are investigation leads, not automatic component-failure diagnoses.

## Verified run

The current pinned run analyzes 48 operational recordings and 31,725 accepted samples. It rejects and reports 1,655 incomplete rows. The system flags RAAVANA's PY face in both available recordings and battery-voltage excursions in three recordings. Eleven automated tests pass, including independent unit conversion/integration, invalid-row handling, non-monotonic timestamp rejection, and the original analytical solver checks.

## What it proves

This is running software over authentic flight telemetry, with traceable inputs and machine-readable outputs. It demonstrates local data ingestion, validation, energy reconstruction, health screening, and reporting. It does not prove a new spacecraft can sustain a particular payload duty cycle because the public dataset lacks that spacecraft's load, attitude, continuous state of charge, and hardware configuration. A future duty-cycle acceptance decision requires an actual payload profile and calibrated hardware-in-the-loop telemetry through the same ingestion boundary.

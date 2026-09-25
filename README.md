# Layl | ليل — Challenge 1

**A real-data nighttime-light decision tool for university astronomy teams and observing clubs.**

Challenge 1 now runs on authentic World Bank Space2Stats records derived from NASA Black Marble. It validates and analyzes every Iraqi ADM2 district from 2012–2024. The separately developed [Challenge 2 package](challenge2/README.md) runs on authentic BIRDS flight telemetry.

**Status: functional real-data satellite monitoring system.** The primary report contains no generated observation rows. Satellite upward-radiance screening is not a substitute for calibrated ground-level sky measurements.

## Start here

1. Read [the engineering dossier](docs/01_ENGINEERING_DOSSIER.md).
2. Open [the real-data report](output/real/layl_real_report.html) in a browser.
3. Read [the real-data and validation protocol](docs/02_DATA_AND_VALIDATION.md) before replacing the sample data.
4. Use [the delivery and pitch plan](docs/03_EXECUTION_AND_PITCH.md) for team coordination.
5. See [the document review](research/DOCUMENT_REVIEW.md) for coverage of every supplied PDF page.

## Run locally

### تشغيل لوحة القرار خلال أقل من 3 دقائق

```powershell
cd dashboard
.\run_dashboard.ps1
```

افتح `http://127.0.0.1:8902/#challenge1`، وانتقل إلى «خطط ليلة الرصد»، ثم اضغط «احسب القرار الحي». تحتاج التوصية الحية إلى الإنترنت؛ تبقى أحدث استجابات Open-Meteo مخزنة لمدة ساعة.

اقرأ [تدقيق المستودع](AUDIT.md)، و[مصادر البيانات](DATA_SOURCES.md)، و[المنهج](METHODS.md)، و[دراسة حالة الموصل](CASE_STUDY.md)، و[سيناريو العرض](DEMO_SCRIPT.md).

### Decision dashboard in under 3 minutes

Run `dashboard/run_dashboard.ps1`, open `http://127.0.0.1:8902/#challenge1`, and use the observation planner. Live recommendations require internet access and never fabricate missing SQM calibration.

On this Windows workspace:

```powershell
.\run_demo.ps1
```

On another machine with Python 3.10+ and NumPy:

```shell
python -m pip install -r requirements.txt
python real_challenge1.py
python -m unittest discover -s tests -v
```

The PowerShell launcher uses the existing bundled Python when available. The analysis needs no network after `fetch_challenge1_data.py` has stored the public data and manifest.

Refresh the official public dataset:

```shell
python fetch_challenge1_data.py
```

The fetcher queries World Bank resource `DR0095685` with `ISO_A3='IRQ'`, stores the unmodified API response, schema, retrieval time, URL, and SHA-256 hashes. Every analysis run checks those hashes before processing.

## Files and evidence

| File | Purpose |
|---|---|
| `fetch_challenge1_data.py` | Official API retrieval and immutable source manifest |
| `nightlights.py` | Hash verification, schema/QA validation, trends, rankings, and watchlist |
| `real_challenge1.py` | Real-data reports, CSV export, and test execution |
| `data/real/worldbank_iraq_annual.json` | 1,313 authentic Iraq district-year records |
| `output/real/iraq_nightlights_analysis.json` | Complete machine-readable analysis |
| `output/real/district_results.csv` | 101 Iraqi district trend records |
| `output/real/layl_real_report.html` | Offline decision dashboard |
| `docs/` | Engineering specification, scientific validation protocol, execution plan |
| `research/` | Original PDF text extraction and visual-review notes |

Verified run: **1,313 real records**, **101 Iraqi districts**, **2012–2024**, and **9/9 tests passed**. The report uses gas-flare-excluded annual radiance to screen dark areas and identify rapid brightening.

## What still needs external evidence

- Matched, calibrated local SQM measurements for ground-level sky-brightness validation.
- Access, horizon, weather, and security checks for screened districts.
- Verified access and terrain/horizon information before recommending a site.
- Before/after measurements with a control site before claiming intervention benefits.

The supplied briefs do not specify the team size, competition deadline, judging weights, mandatory model, or submission format. The engineering choices and 48-hour plan in this package are proposals, not invented competition rules.



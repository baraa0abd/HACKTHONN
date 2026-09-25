"""Generate the real-data Layl Challenge 1 evidence package."""
import csv
import html
import json
from pathlib import Path
import sys
import unittest

from nightlights import analyse, load_verified

ROOT = Path(__file__).resolve().parent


def render(result, manifest, tests):
    candidates = "".join(f"<tr><td>{i}</td><td>{html.escape(d['governorate'])}</td><td>{html.escape(d['district'])}</td><td>{d['latest_radiance']:.3f}</td><td>{d['change_percent']:+.1f}%</td><td>{d['latest_good_quality']:.1%}</td></tr>" for i,d in enumerate(result["dark_screening_candidates"],1))
    watch = "".join(f"<tr><td>{html.escape(d['governorate'])}</td><td>{html.escape(d['district'])}</td><td>{d['first_radiance']:.3f}</td><td>{d['latest_radiance']:.3f}</td><td>{d['change_percent']:+.1f}%</td></tr>" for d in result["rapid_increase_watchlist"])
    series = result["national_series"]
    lo, hi = min(x["district_median_radiance"] for x in series), max(x["district_median_radiance"] for x in series)
    points = " ".join(f"{55+i*700/(len(series)-1):.1f},{245-(p['district_median_radiance']-lo)/(hi-lo or 1)*180:.1f}" for i,p in enumerate(series))
    labels = "".join(f"<text x='{55+i*700/(len(series)-1):.1f}' y='280' text-anchor='middle'>{p['year']}</text>" for i,p in enumerate(series) if i in (0,len(series)-1) or i%3==0)
    return f'''<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Layl — Real Iraq Night Lights</title><style>
body{{margin:0;background:#071421;color:#dbe8f2;font:15px/1.55 system-ui}}main{{max-width:1160px;margin:auto;padding:38px 24px}}h1{{font-size:48px;margin:8px 0}}section,.card{{background:#102338;border:1px solid #29445e;border-radius:10px;padding:22px;margin:18px 0;overflow:auto}}.cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}.value{{font-size:36px;color:#6ce3cf;font-weight:750}}.notice{{background:#17392f;border-left:5px solid #6ce3cf;padding:18px}}table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}th,td{{padding:9px;border-bottom:1px solid #29445e;text-align:left}}svg{{background:#0a1a2b;width:100%;height:auto}}small{{color:#a6bac9}}a{{color:#6ce3cf}}@media(max-width:700px){{.cards{{grid-template-columns:1fr}}h1{{font-size:36px}}}}</style><main>
<small>ASI HACKATHON · CHALLENGE 1 · REAL DATA BUILD</small><h1>Layl <span lang=ar dir=rtl>ليل</span></h1><p>Iraq nighttime-light monitoring and observing-area screening from NASA Black Marble.</p>
<div class=notice><b>100% REAL INPUT RECORDS.</b> This run contains no generated observation rows. It uses {result['records']:,} World Bank Space2Stats records derived from NASA Black Marble, covering {result['districts']} Iraqi ADM2 districts from {result['years'][0]}–{result['years'][-1]}. Source files are hash-verified before analysis.</div>
<div class=cards><div class=card><small>Real records</small><div class=value>{result['records']:,}</div>district-years</div><div class=card><small>Coverage</small><div class=value>{result['districts']}</div>Iraqi districts</div><div class=card><small>Verification</small><div class=value>{tests['passed']}/{tests['run']}</div>tests passed</div></div>
<section><h2>National trend signal</h2><p>Median of district-level annual mean radiance after excluding pixels within 5 km of mapped gas flares. This is a consistent screening statistic; it is not a population-weighted national mean.</p><svg viewBox="0 0 800 310" role=img aria-label="Iraq district median annual radiance"><path d="M55 45V245H760" fill=none stroke="#668096"/><polyline points="{points}" fill=none stroke="#6ce3cf" stroke-width=4/>{labels}<text x=60 y=30>Higher means brighter satellite-observed upward radiance</text></svg></section>
<section><h2>Dark-area screening candidates</h2><p>Lowest 2024 mean radiance among districts with at least 90% good-quality pixels. These areas require access, horizon, weather, security, and calibrated SQM checks before anyone calls them observing sites.</p><table><tr><th>#</th><th>Governorate</th><th>District</th><th>2024 radiance</th><th>2012–24 change</th><th>Good QA</th></tr>{candidates}</table></section>
<section><h2>Rapid-brightening watchlist</h2><p>Ranked by the slope of log-transformed annual radiance. This highlights where lighting review or field investigation may have the highest value; it does not identify individual fixtures.</p><table><tr><th>Governorate</th><th>District</th><th>2012</th><th>2024</th><th>Change</th></tr>{watch}</table></section>
<section><h2>Traceability and decision boundary</h2><p>Source: <a href="{manifest['dataset_page']}">World Bank Space2Stats Monthly & Annual Black Marble Nighttime Lights</a>, resource <code>{manifest['resource_id']}</code>, retrieved {html.escape(manifest['retrieved_utc'])}. Query: <code>{html.escape(manifest['query'])}</code>.</p><p>Satellite radiance measures emitted upward light at roughly 500 m source resolution before administrative aggregation. It does not directly measure ground-level SQM, Bortle class, spectral composition, glare, or fixture direction. The system therefore returns evidence-based screening and trend monitoring, followed by a defined field-validation gate.</p></section></main></html>'''


def main():
    data_dir = ROOT / "data" / "real"; output = ROOT / "output" / "real"
    output.mkdir(parents=True, exist_ok=True)
    records, manifest = load_verified(data_dir)
    result = analyse(records)
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    tested = unittest.TextTestRunner(verbosity=2).run(suite)
    tests = {"run": tested.testsRun, "passed": tested.testsRun-len(tested.failures)-len(tested.errors)-len(tested.skipped),
             "failures": len(tested.failures), "errors": len(tested.errors), "skipped": len(tested.skipped)}
    (output / "iraq_nightlights_analysis.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    fields = ["adm2_code","governorate","district","first_year","latest_year","first_radiance","latest_radiance","latest_median","latest_q95","latest_good_quality","change_percent","log_radiance_slope_per_year"]
    with (output / "district_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows(result["district_results"])
    (output / "layl_real_report.html").write_text(render(result, manifest, tests), encoding="utf-8")
    (output / "tests.json").write_text(json.dumps(tests, indent=2), encoding="utf-8")
    print(f"Real data: {result['records']} records, {result['districts']} districts, {result['years'][0]}-{result['years'][-1]}")
    print(f"Tests: {tests['passed']}/{tests['run']} passed")
    print(f"Report: {output / 'layl_real_report.html'}")
    return 0 if tested.wasSuccessful() else 1


if __name__ == "__main__": sys.exit(main())

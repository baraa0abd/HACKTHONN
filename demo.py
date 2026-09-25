"""Reproducible software demonstration. No generated row is a field observation."""
import csv
import hashlib
import html
import json
from pathlib import Path
import numpy as np
from sky import evaluate, scenario

ROOT = Path(__file__).resolve().parent


def sample_rows():
    rng = np.random.default_rng(20260925)
    rows = []
    for site in range(12):
        # A geographic demonstration box around Baghdad; no real site assessment.
        lat = 33.10 + (site // 4)*.18
        lon = 44.05 + (site % 4)*.18
        site_radiance = rng.uniform(1, 70)
        site_effect = rng.normal(0, .18)
        for day in range(1, 9):
            radiance = max(.01, site_radiance+rng.normal(0, 2))
            cloud, moon, aod = rng.uniform(0, .5), rng.uniform(0, 1), rng.uniform(.05, .6)
            sqm = 22-.72*np.log1p(radiance)-1.3*cloud-.8*moon-.7*aod+site_effect+rng.normal(0,.1)
            rows.append(dict(site_id=f'DEMO-{site+1:02}', block_id=f'BLOCK-{site//2+1}',
                             date=f'2026-09-{day:02}', lat=lat, lon=lon,
                             radiance_nw_cm2_sr=round(radiance,5), cloud_fraction=round(cloud,5),
                             moon_illumination=round(moon,5), aod=round(aod,5),
                             sqm_mag_arcsec2=round(sqm,5), qa_valid=int(day != 3),
                             source_id='generated-fixture-seed-20260925', provenance='synthetic'))
    return rows


def render_report(result, scenarios):
    synthetic = result['provenance'] == 'synthetic'
    provenance_label = 'synthetic' if synthetic else 'supplied observations'
    notice = ('<b>SYNTHETIC DATA — NOT A BAGHDAD SKY SURVEY.</b><br>'
              f'All {result["n_input"]} rows are generated fixtures. Metrics verify software behavior only. '
              'No real observing site, measured pollution reduction, or field accuracy is claimed.'
              if synthetic else '<b>SUPPLIED MEASUREMENT DATA — PROVENANCE REQUIRES REVIEW.</b><br>'
              'The input labels its observations as measured. This software checks the table, '
              'not the authenticity or calibration of its sources. These are cross-validation results, '
              'not independent field validation. Review the source manifest before using the results.')
    sites = {}
    for row in result['predictions']:
        sites.setdefault(row['site_id'], []).append(row)
    ranked = sorted(sites, key=lambda k: np.mean([r['predicted_sqm'] for r in sites[k]]), reverse=True)
    lats = [float(r['lat']) for r in result['predictions']]
    lons = [float(r['lon']) for r in result['predictions']]
    latmin, latmax, lonmin, lonmax = min(lats), max(lats), min(lons), max(lons)
    markers, table = [], []
    for index, site in enumerate(ranked, 1):
        values = sites[site]
        avg = float(np.mean([r['predicted_sqm'] for r in values]))
        x = 75+(float(values[0]['lon'])-lonmin)/(lonmax-lonmin or 1)*630
        y = 325-(float(values[0]['lat'])-latmin)/(latmax-latmin or 1)*255
        hue = max(0,min(200,(avg-17)*55))
        markers.append(f'<circle cx="{x}" cy="{y}" r="19" fill="hsl({hue},65%,58%)"/><text x="{x}" y="{y+5}" text-anchor="middle" fill="#081422">{index}</text>')
        table.append(f'<tr><td>{index}</td><td>{html.escape(site)}</td><td>{avg:.2f}</td><td>{len(values)}</td><td>Unverified</td></tr>')
    blocks = ''.join(f'<tr><td>{html.escape(r["block"])}</td><td>{r["n"]}</td><td>{r["mae"]:.3f}</td></tr>' for r in result['block_metrics'])
    srows = ''.join(f'<tr><td>{s["assumed_artificial_fraction"]:.0%}</td><td>{s["assumed_artificial_light_reduction"]:.0%}</td><td>{s["sqm_after"]:.2f}</td><td>+{s["gain_mag_arcsec2"]:.2f}</td></tr>' for s in scenarios)
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Layl | Challenge 1 engineering demonstration</title>
<style>body{{margin:0;background:#081422;color:#d9e6f2;font:16px/1.6 system-ui,sans-serif}}main{{max-width:1120px;margin:auto;padding:42px 28px}}h1{{font-size:52px;line-height:1.1;margin:12px 0}}h2{{font-size:25px}}.eyebrow{{color:#6ce3cf;letter-spacing:3px;font-size:12px}}.notice{{border-left:4px solid #ffc765;background:#332b1e;padding:16px 22px;margin:28px 0}}.cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}.card,section{{background:#112238;border:1px solid #263e56;border-radius:12px;padding:24px;margin:18px 0}}.value{{font-size:36px;font-weight:700;color:#6ce3cf}}.muted{{color:#a9bbce}}table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}td,th{{text-align:left;padding:11px;border-bottom:1px solid #29425b}}svg{{width:100%;height:auto;background:#0b192a;border-radius:12px}}a{{color:#6ce3cf}}@media(max-width:700px){{.cards{{grid-template-columns:1fr}}h1{{font-size:38px}}main{{padding:20px}}section{{overflow:auto}}}}@media print{{body{{background:white;color:#111}}section,.card{{background:white;color:#111;break-inside:avoid}}.notice{{background:#eee;color:#111}}}}</style>
<main><div class="eyebrow">ASI HACKATHON / CHALLENGE 01</div><h1>Layl <span lang="ar" dir="rtl">ليل</span></h1><p class="muted">A reproducible sky-quality decision prototype · Engineering demonstration v0.1</p>
<div class="notice">{notice}</div>
<div class="cards"><div class="card"><div class="muted">Held-out block MAE</div><div class="value">{result['mae_mag_arcsec2']:.3f}</div>mag/arcsec² · {provenance_label}</div><div class="card"><div class="muted">Radiance-only baseline MAE</div><div class="value">{result['radiance_only_baseline_mae']:.3f}</div>mag/arcsec² · {provenance_label}</div><div class="card"><div class="muted">Accepted / rejected QA</div><div class="value">{result['n_valid']} / {result['n_rejected_qa']}</div>{result['n_blocks']} held-out spatial blocks</div></div>
<section><h2>01 / Candidate comparison</h2><p>Higher SQM means a darker sky. This illustrative ordering averages held-out predictions across sample dates. Weather is not standardized; this is not a permanent site ranking. Access and observing suitability remain unverified.</p>
<svg role="img" aria-label="Observation coordinate diagram, {provenance_label}" viewBox="0 0 800 400"><path d="M50 40V350H760" stroke="#63839e" fill="none"/><text x="50" y="385" fill="#a9bbce">Lon {lonmin:.2f}°</text><text x="650" y="385" fill="#a9bbce">Lon {lonmax:.2f}°</text><text x="10" y="28" fill="#a9bbce">Lat {latmin:.2f}° to {latmax:.2f}° · schematic / no basemap</text>{''.join(markers)}</svg>
<table><thead><tr><th>Order</th><th>Point ID</th><th>Predicted SQM</th><th>Valid dates</th><th>Site access</th></tr></thead><tbody>{''.join(table)}</tbody></table></section>
<section><h2>02 / Validation evidence</h2><p>Each spatial block is withheld from training in turn. Scaling and model fitting use training rows only. The median baseline MAE is {result['median_baseline_mae']:.3f}. The 90th percentile absolute held-out error is {result['oof_absolute_error_p90']:.3f} mag/arcsec²; it is a descriptive error statistic, not a prediction interval.</p><table><tr><th>Held-out block</th><th>Rows</th><th>MAE (mag/arcsec²)</th></tr>{blocks}</table><p class="muted">{'The fixture follows a similar mathematical family to the model. Strong results are expected and provide no evidence of real-world predictive skill.' if synthetic else 'Spatial block assignment and source quality require analyst review. This report does not test temporal generalization or intervention effectiveness.'}</p></section>
<section><h2>03 / Lighting intervention sensitivity</h2><p>Illustrative starting SQM: 18.00 mag/arcsec². These inputs describe assumed ground-level sky luminance contributions. They are not inferred from VIIRS radiance.</p><table><tr><th>Artificial share</th><th>Reduction of that share</th><th>Scenario SQM</th><th>Gain (mag/arcsec²)</th></tr>{srows}</table><p>Equation: Δm = −2.5 log₁₀(1 − artificial_share × reduction). This holds natural brightness fixed and assumes linear reduction of the artificial component. An intervention requires paired before/after observations and a control site.</p></section>
<section><h2>04 / Release gates</h2><p><b>Implemented:</b> input checks, explicit QA rejection, spatial holdouts, regression and baselines, reproducible outputs, and scenario calculations.</p><p><b>Before a scientific submission:</b> obtain authentic local observations and NASA granules, verify product QA and units, align dates, validate on untouched sites and dates, and run a field comparison. Local access checks are required before recommending an observing location.</p><p><b>Operational scope:</b> preliminary decisions for astronomy clubs and university teams. No fixture-level source attribution, direct lighting control, or automatic Bortle classification.</p></section>
<p class="muted">Generated locally by Layl. Input SHA-256: {result['input_sha256']}<br>See the engineering dossier and data protocol for requirements, sources, and the field-validation plan.</p></main></html>'''


def main():
    data, out = ROOT/'data', ROOT/'output'
    data.mkdir(exist_ok=True); out.mkdir(exist_ok=True)
    rows = sample_rows()
    path = data/'synthetic_observations.csv'
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    result = evaluate(rows)
    result['input_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    scenarios = [scenario(18, f, r) for f in (.3,.6,.9) for r in (.2,.4)]
    (out/'sky_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (out/'scenarios.json').write_text(json.dumps(scenarios,indent=2),encoding='utf-8')
    (out/'layl_demo.html').write_text(render_report(result,scenarios),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('model','predictions')},indent=2))
    print('Report:',out/'layl_demo.html')


if __name__ == '__main__':
    main()

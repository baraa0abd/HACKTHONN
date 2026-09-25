"""Real forecast-vs-outcome nights for the Layl observing sites (no synthetic rows).

For every site and night since 2024-02-01 (start of Open-Meteo's archived day-ahead runs):
  features = what the forecast issued ~24 h earlier said about that night (previous_day1)
  truth    = ERA5 reanalysis cloud cover for the same hours (what actually happened)
  check    = NASA POWER daily satellite cloud amount (CERES SYN1deg), independent of ERA5
Night = 19:00 to 04:00 Asia/Baghdad (10 hours). A night is "clear" when ERA5 has
at least CLEAR_HOURS_NEEDED hours below CLEAR_CLOUD_PCT cloud.
"""
from __future__ import annotations
import csv, hashlib, json, math, time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from decision_engine import SITES, _site_layer

ROOT = Path(__file__).resolve().parent
OUT, CACHE = ROOT / 'data' / 'sky', ROOT / 'data' / 'cache' / 'sky'
START = date(2024, 2, 1)
END = date.today() - timedelta(days=7)  # ERA5 archive lags about 5 days
FC_VARS = ['cloud_cover', 'relative_humidity_2m', 'wind_speed_10m', 'precipitation']
CLEAR_CLOUD_PCT, CLEAR_HOURS_NEEDED = 25, 6
NIGHT_HOURS = [19, 20, 21, 22, 23, 0, 1, 2, 3, 4]


def get(base, params):
    """GET JSON with a permanent cache (historical ranges never change) and polite retries."""
    key = hashlib.sha256((base + urlencode(params)).encode()).hexdigest()[:24]
    path = CACHE / f'{key}.json'
    if path.exists(): return json.loads(path.read_text(encoding='utf-8'))
    for attempt in range(4):
        try:
            with urlopen(Request(base + '?' + urlencode(params), headers={'User-Agent': 'LaylHackathon/1.0'}), timeout=120) as r:
                data = json.load(r)
            break
        except Exception:
            if attempt == 3: raise
            time.sleep(20 * (attempt + 1))  # Open-Meteo rate limit is per minute
    CACHE.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data), encoding='utf-8'); time.sleep(1)
    return data


def hourly(base, site, variables, start, end):
    """Hourly series keyed by local ISO hour, fetched in yearly chunks."""
    out = {}
    s = start
    while s <= end:
        e = min(date(s.year, 12, 31), end)
        h = get(base, {'latitude': site['lat'], 'longitude': site['lon'], 'start_date': s.isoformat(), 'end_date': e.isoformat(),
                       'hourly': ','.join(variables), 'timezone': 'Asia/Baghdad'})['hourly']
        for i, t in enumerate(h['time']): out[t] = {v: h[v][i] for v in variables}
        s = e + timedelta(days=1)
    return out


def night_hours(d: date):
    return [f'{(d if h >= 19 else d + timedelta(days=1)).isoformat()}T{h:02d}:00' for h in NIGHT_HOURS]


def night_features(d: date, cloud, rh, wind, rain, site_light):
    """Model inputs for one night from 10 hourly forecast values. Shared by training and live use."""
    return {'fc_cloud_mean': round(sum(cloud) / 10, 2), 'fc_cloud_max': max(cloud),
            'fc_clear_hours': sum(c < CLEAR_CLOUD_PCT for c in cloud), 'fc_rh_mean': round(sum(rh) / 10, 2),
            'fc_wind_max': max(wind), 'fc_precip_sum': round(sum(rain), 2),
            'month_sin': round(math.sin(2 * math.pi * d.month / 12), 4), 'month_cos': round(math.cos(2 * math.pi * d.month / 12), 4),
            'site_light': round(site_light, 4)}


def power_cloud(site):
    p = get('https://power.larc.nasa.gov/api/temporal/daily/point',
            {'parameters': 'CLOUD_AMT', 'community': 'RE', 'latitude': site['lat'], 'longitude': site['lon'],
             'start': START.strftime('%Y%m%d'), 'end': END.strftime('%Y%m%d'), 'format': 'JSON'})
    return {datetime.strptime(k, '%Y%m%d').date().isoformat(): (None if v < 0 else v)
            for k, v in p['properties']['parameter']['CLOUD_AMT'].items()}  # -999 = missing


def build():
    rows, skipped = [], defaultdict(int)
    layer = {s['id']: s for s in _site_layer()}
    for site in SITES:
        fc = hourly('https://previous-runs-api.open-meteo.com/v1/forecast', site, [f'{v}_previous_day1' for v in FC_VARS], START, END + timedelta(days=1))
        era = hourly('https://archive-api.open-meteo.com/v1/archive', site, ['cloud_cover'], START, END + timedelta(days=1))
        sat = power_cloud(site)
        d = START
        while d <= END:
            hrs = night_hours(d)
            f = [fc.get(t) for t in hrs]; e = [(era.get(t) or {}).get('cloud_cover') for t in hrs]
            if any(x is None or any(v is None for v in x.values()) for x in f) or any(v is None for v in e):
                skipped[site['id']] += 1; d += timedelta(days=1); continue
            col = lambda v: [x[f'{v}_previous_day1'] for x in f]
            cloud, rh, wind, rain = col('cloud_cover'), col('relative_humidity_2m'), col('wind_speed_10m'), col('precipitation')
            clear_hours = sum(c < CLEAR_CLOUD_PCT for c in e)
            rows.append({
                'site_id': site['id'], 'date': d.isoformat(), **night_features(d, cloud, rh, wind, rain, layer[site['id']]['static']),
                'era5_cloud_mean': round(sum(e) / 10, 2), 'era5_clear_hours': clear_hours,
                'nasa_power_daily_cloud': sat.get(d.isoformat()),
                'clear_night': int(clear_hours >= CLEAR_HOURS_NEEDED),
            })
            d += timedelta(days=1)
        print(f"{site['id']}: {sum(r['site_id'] == site['id'] for r in rows)} nights, skipped {skipped[site['id']]}", flush=True)
    return rows, dict(skipped)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, skipped = build()
    with (OUT / 'nights.csv').open('w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    pairs = [(r['era5_cloud_mean'], r['nasa_power_daily_cloud']) for r in rows if r['nasa_power_daily_cloud'] is not None]
    n = len(pairs); mx = sum(a for a, _ in pairs) / n; my = sum(b for _, b in pairs) / n
    corr = sum((a - mx) * (b - my) for a, b in pairs) / math.sqrt(sum((a - mx) ** 2 for a, _ in pairs) * sum((b - my) ** 2 for _, b in pairs))
    manifest = {'generated_utc': datetime.now(timezone.utc).isoformat(), 'period': [START.isoformat(), END.isoformat()],
                'sources': {'features': 'Open-Meteo Previous Runs API, *_previous_day1 (forecast issued ~24 h ahead)',
                            'truth': 'Open-Meteo Historical Weather API (ERA5 reanalysis) cloud_cover',
                            'independent_check': 'NASA POWER daily CLOUD_AMT (CERES SYN1deg satellite)'},
                'night_hours_local': NIGHT_HOURS, 'clear_definition': f'>= {CLEAR_HOURS_NEEDED} of 10 night hours with ERA5 cloud < {CLEAR_CLOUD_PCT}%',
                'rows': len(rows), 'clear_rate': round(sum(r['clear_night'] for r in rows) / len(rows), 4),
                'skipped_nights_missing_data': skipped,
                'era5_vs_nasa_satellite_cloud_correlation': round(corr, 4),
                'sha256': hashlib.sha256((OUT / 'nights.csv').read_bytes()).hexdigest()}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({k: manifest[k] for k in ('period', 'rows', 'clear_rate', 'skipped_nights_missing_data', 'era5_vs_nasa_satellite_cloud_correlation')}, indent=2))


if __name__ == '__main__':
    main()

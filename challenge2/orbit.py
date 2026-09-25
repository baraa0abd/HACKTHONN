"""OrbitBench: locally maintainable early CubeSat energy test software.

Idealized fixed-period power simulation; never a flight qualification tool.
Configuration values are team assumptions, not NASA specifications.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def validate(c):
    required = ('period_min', 'eclipse_min', 'solar_w', 'base_w', 'payload_w',
                'payload_duty', 'battery_wh', 'initial_soc', 'min_soc',
                'charge_efficiency', 'discharge_efficiency', 'orbits')
    for k in required:
        if k not in c or isinstance(c[k], bool) or not isinstance(c[k], (int, float)) or not math.isfinite(c[k]):
            raise ValueError(f'Missing or invalid {k}')
    if c['period_min'] <= 0 or not 0 <= c['eclipse_min'] < c['period_min']:
        raise ValueError('Invalid orbit/eclipse durations')
    if c['battery_wh'] <= 0 or any(c[k] < 0 for k in ('solar_w', 'base_w', 'payload_w')):
        raise ValueError('Invalid power or storage')
    for k in ('payload_duty', 'initial_soc', 'min_soc'):
        if not 0 <= c[k] <= 1:
            raise ValueError(f'{k} must be in [0,1]')
    for k in ('charge_efficiency', 'discharge_efficiency'):
        if not 0 < c[k] <= 1:
            raise ValueError(f'{k} must be in (0,1]')
    if int(c['orbits']) != c['orbits'] or not 1 <= c['orbits'] <= 100:
        raise ValueError('orbits must be an integer from 1 to 100')


def simulate(c, dt_min=1):
    validate(c)
    if isinstance(dt_min, bool) or not isinstance(dt_min,(int,float)) or not math.isfinite(dt_min) or dt_min <= 0:
        raise ValueError('Time step must be positive')
    if c['period_min']*c['orbits']/dt_min > 200000:
        raise ValueError('Requested trace exceeds 200000 steps; use a larger time step')
    energy = c['battery_wh'] * c['initial_soc']
    initial = energy
    minimum = energy / c['battery_wh']
    load = c['base_w'] + c['payload_w'] * c['payload_duty']
    total = c['period_min'] * c['orbits']
    t, unserved, curtailed = 0., 0., 0.
    trace = [{'minute': 0., 'soc': minimum}]
    # Segment exactly at sunlight/eclipse boundaries, even with fractional periods.
    for n in range(int(c['orbits'])):
        for duration, power in ((c['period_min']-c['eclipse_min'], c['solar_w']),
                                (c['eclipse_min'], 0.)):
            remaining = duration
            while remaining > 1e-9:
                step = min(dt_min, remaining)
                bus_delta = (power-load) * step/60
                delta = bus_delta*c['charge_efficiency'] if bus_delta >= 0 else bus_delta/c['discharge_efficiency']
                proposed = energy+delta
                if proposed < 0:
                    unserved += -proposed*c['discharge_efficiency']
                if proposed > c['battery_wh']:
                    curtailed += (proposed-c['battery_wh'])/c['charge_efficiency']
                energy = max(0., min(c['battery_wh'], proposed))
                minimum = min(minimum, energy/c['battery_wh'])
                t += step
                trace.append({'minute': round(t, 6), 'soc': energy/c['battery_wh']})
                remaining -= step
    sunlight = c['period_min']-c['eclipse_min']
    # Sustainable battery budget includes efficiency and ignores charge saturation.
    sun_net = (c['solar_w']-load)*sunlight/60
    stored_net = sun_net*c['charge_efficiency'] if sun_net >= 0 else sun_net/c['discharge_efficiency']
    net_orbit = stored_net-load*c['eclipse_min']/60/c['discharge_efficiency']
    checks = [
        {'id': 'EPS-01', 'description': 'No unmet load energy', 'pass': unserved < 1e-9,
         'actual': unserved, 'unit': 'Wh', 'limit': 0},
        {'id': 'EPS-02', 'description': 'Battery stays above mission reserve',
         'pass': minimum >= c['min_soc']-1e-9, 'actual': minimum, 'unit': 'fraction', 'limit': c['min_soc']},
        {'id': 'EPS-03', 'description': 'Nonnegative ideal per-orbit energy balance',
         'pass': net_orbit >= -1e-9, 'actual': net_orbit, 'unit': 'Wh/orbit', 'limit': 0},
    ]
    return {'status': 'idealized simulation; not hardware or flight validation',
            'config': c, 'config_sha256': hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest(),
            'duration_min': total, 'average_load_w': load,
            'min_soc': minimum, 'final_soc': energy/c['battery_wh'],
            'battery_energy_change_wh': energy-initial,
            'unserved_wh': unserved, 'curtailed_wh': curtailed,
            'net_battery_wh_per_orbit': net_orbit,
            'checks': checks, 'all_pass': all(x['pass'] for x in checks), 'trace': trace,
            'trl': 'Not assigned automatically. Concept/analytical evidence only; independent review required.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config')
    parser.add_argument('--output', default='output/orbit_results.json')
    args = parser.parse_args()
    result = simulate(json.loads(Path(args.config).read_text(encoding='utf-8')))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding='utf-8')
    for check in result['checks']:
        print(check['id'], 'PASS' if check['pass'] else 'FAIL', check['actual'], check['unit'])

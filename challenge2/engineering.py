"""Bounded design search across explicitly assumed environmental corners.

No learned model or flight telemetry is used. Exhaustive grid search is exact
only for the specified grid, corners, constraints, and simplified simulator.
"""
import itertools
from orbit import simulate, validate


def corners(config):
    validate(config)
    if config['eclipse_min']+5 >= config['period_min']:
        raise ValueError('Five-minute eclipse stress would exceed the orbit')
    return [
        (f'S{solar:g}-E{extra:g}-B{battery:g}',
         {**config, 'solar_w':config['solar_w']*solar,
          'eclipse_min':config['eclipse_min']+extra,
          'battery_wh':config['battery_wh']*battery})
        for solar,extra,battery in itertools.product((1.,.75),(0.,5.),(1.,.8))
    ]


def assess(config):
    results=[]
    for name, candidate in corners(config):
        result=simulate(candidate,dt_min=5)
        results.append({'corner':name, 'pass':result['all_pass'],
                        'min_soc':result['min_soc'],
                        'net_battery_wh_per_orbit':result['net_battery_wh_per_orbit'],
                        'unserved_wh':result['unserved_wh'],
                        'checks':result['checks']})
    return {'all_pass':all(r['pass'] for r in results),'corners':results}


def search_duty(config):
    """Maximize modeled duty over 101 grid points, honoring all eight corners."""
    tested=[]
    best=None
    for step in range(101):
        candidate={**config,'payload_duty':step/100}
        result=assess(candidate)
        tested.append({'payload_duty':step/100,'all_corners_pass':result['all_pass'],
                       'worst_min_soc':min(r['min_soc'] for r in result['corners']),
                       'worst_net_wh_per_orbit':min(r['net_battery_wh_per_orbit'] for r in result['corners'])})
        if result['all_pass']:
            best=candidate
    return {'best_config':best,'tested':tested,
            'simulation_count':len(tested)*8,
            'objective':'maximum payload duty on 0.01 grid satisfying all specified corners',
            'scope':'conditional engineering result; not a validated spacecraft operating limit'}

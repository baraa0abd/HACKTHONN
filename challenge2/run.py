"""Build a reproducible Challenge 2 evidence package using the standard library."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import time
import unittest
from orbit import simulate
from engineering import assess,search_duty
from report import render

ROOT=Path(__file__).resolve().parent


def save_json(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'examples/mission.json')
    parser.add_argument('--output',type=Path,default=ROOT/'output')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    log=io.StringIO()
    tested=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (args.output/'test_log.txt').write_text(log.getvalue(),encoding='utf-8')
    summary={'run':tested.testsRun,'passed':tested.testsRun-len(tested.failures)-len(tested.errors)-len(tested.skipped),
             'failures':len(tested.failures),'errors':len(tested.errors),'skipped':len(tested.skipped),
             'python':platform.python_version()}
    save_json(args.output/'tests.json',summary)
    if not tested.wasSuccessful():
        print(log.getvalue());return 1
    config=json.loads(args.config.read_text(encoding='utf-8'))
    start=time.perf_counter()
    before=simulate(config)
    search=search_duty(config)
    after=simulate(search['best_config']) if search['best_config'] else None
    assessment=assess(search['best_config']) if search['best_config'] else None
    duration=time.perf_counter()-start
    save_json(args.output/'initial_result.json',before)
    save_json(args.output/'candidate_result.json',after)
    save_json(args.output/'candidate_corners.json',assessment)
    save_json(args.output/'search.json',search)
    save_json(args.output/'candidate_config.json',search['best_config'])
    save_json(args.output/'lower_duty_example.json',{'config':{**config,'payload_duty':.15},
        'assessment':assess({**config,'payload_duty':.15}),
        'note':'Sensitivity example, not an approved operating setting'})
    with (args.output/'search.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(search['tested'][0]));writer.writeheader();writer.writerows(search['tested'])
    (args.output/'orbitbench.html').write_text(render(before,after,search,assessment,summary),encoding='utf-8')
    sources=[p for p in ROOT.glob('*.py')]+list((ROOT/'tests').glob('*.py'))
    save_json(args.output/'run_manifest.json',{'input_file':args.config.name,
        'input_sha256':hashlib.sha256(args.config.read_bytes()).hexdigest(),
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'python':platform.python_version(),'search_and_reporting_inputs_seconds':duration,
        'evidence_type':'analytical simulation with assumed inputs; no measured telemetry'})
    print(f"Tests: {summary['passed']}/{summary['run']}. Search: 808 simulations in {duration:.3f}s.")
    print('Initial nominal:',before['all_pass'],'Minimum SOC:',round(before['min_soc'],4))
    print('Candidate duty:',search['best_config']['payload_duty'] if after else 'no feasible candidate')
    if assessment:
        print('All corners pass:',assessment['all_pass'],'Worst net Wh/orbit:',min(c['net_battery_wh_per_orbit'] for c in assessment['corners']))
    print('Report:',args.output/'orbitbench.html')
    return 0


if __name__=='__main__':
    sys.exit(main())

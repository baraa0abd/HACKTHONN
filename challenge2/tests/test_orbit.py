import json
import math
from pathlib import Path
import unittest
from orbit import simulate,validate
from engineering import assess,search_duty

BASE=json.loads((Path(__file__).resolve().parents[1]/'examples/mission.json').read_text())


class OrbitTests(unittest.TestCase):
    def test_discharge_matches_independent_energy_equation(self):
        c={**BASE,'solar_w':0,'base_w':2,'payload_w':0,'battery_wh':100,
           'orbits':1,'period_min':60,'eclipse_min':20,'initial_soc':.8}
        result=simulate(c)
        self.assertAlmostEqual(result['final_soc'],(80-2/.9)/100)
        self.assertAlmostEqual(result['unserved_wh'],0)

    def test_constant_sun_charge_and_curtailment(self):
        c={**BASE,'solar_w':4,'base_w':2,'payload_w':0,'battery_wh':10,
           'orbits':1,'period_min':60,'eclipse_min':0,'initial_soc':.95}
        result=simulate(c)
        self.assertAlmostEqual(result['final_soc'],1)
        self.assertAlmostEqual(result['curtailed_wh'],2-.5/.9)

    def test_empty_battery_unserved_bus_energy(self):
        c={**BASE,'solar_w':0,'base_w':2,'payload_w':0,'battery_wh':1,
           'orbits':1,'period_min':60,'eclipse_min':20,'initial_soc':.5}
        result=simulate(c)
        self.assertAlmostEqual(result['unserved_wh'],2-.5*.9)
        self.assertEqual(result['final_soc'],0)
        self.assertFalse(result['all_pass'])

    def test_fractional_boundaries_and_step_invariance(self):
        c={**BASE,'period_min':95.3,'eclipse_min':35.7,'payload_duty':.1}
        a,b=simulate(c,.7),simulate(c,7)
        for k in ('final_soc','min_soc','unserved_wh','curtailed_wh'):
            self.assertAlmostEqual(a[k],b[k],places=9)
        self.assertAlmostEqual(a['trace'][-1]['minute'],95.3*16)

    def test_model_detects_infeasible_design_and_search_repairs_it(self):
        self.assertFalse(assess(BASE)['all_pass'])
        search=search_duty(BASE)
        best=search['best_config']
        self.assertIsNotNone(best)
        self.assertTrue(assess(best)['all_pass'])
        next_config={**best,'payload_duty':round(best['payload_duty']+.01,2)}
        self.assertFalse(assess(next_config)['all_pass'])
        self.assertEqual(search['simulation_count'],808)

    def test_no_feasible_candidate_is_reported(self):
        search=search_duty({**BASE,'solar_w':0})
        self.assertIsNone(search['best_config'])

    def test_bad_input_and_resource_limits(self):
        for key,value in [('solar_w','8'),('orbits',2.5),('orbits',True),
                          ('battery_wh',0),('charge_efficiency',0),
                          ('base_w',-1),('min_soc',math.nan),('eclipse_min',95)]:
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    validate({**BASE,key:value})
        with self.assertRaises(ValueError):
            simulate(BASE,.00001)

    def test_zero_load_has_no_energy_deficit(self):
        result=simulate({**BASE,'base_w':0,'payload_w':0,'solar_w':0})
        self.assertAlmostEqual(result['final_soc'],BASE['initial_soc'])
        self.assertTrue(result['all_pass'])


if __name__=='__main__':
    unittest.main()

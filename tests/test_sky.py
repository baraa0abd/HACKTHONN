import copy
import unittest
import numpy as np
from demo import sample_rows, render_report
from sky import evaluate, scenario, validate


class SkyTests(unittest.TestCase):
    def setUp(self):
        self.rows = sample_rows()

    def test_spatial_holdouts_and_baseline(self):
        result = evaluate(self.rows)
        self.assertEqual(result['n_valid'], 84)
        self.assertEqual(result['n_rejected_qa'], 12)
        self.assertEqual(len(result['predictions']),84)
        self.assertLess(result['mae_mag_arcsec2'], result['radiance_only_baseline_mae'])
        result['input_sha256']='test-only'
        self.assertIn('SYNTHETIC DATA',render_report(result,[]))
        # Exercise notice rendering only; this does not create a measured dataset.
        report_result=copy.deepcopy(result)
        report_result['provenance']='measured'
        rendered=render_report(report_result,[])
        self.assertIn('PROVENANCE REQUIRES REVIEW',rendered)
        self.assertNotIn('All 96 rows are generated fixtures',rendered)
        # This is a synthetic regression check, never a field-accuracy assertion.
        altered = copy.deepcopy(self.rows)
        for r in altered:
            if r['block_id'] == 'BLOCK-1':
                r['sqm_mag_arcsec2'] += 1
        changed = evaluate(altered)
        before = [r['predicted_sqm'] for r in result['predictions'] if r['held_out_block']=='BLOCK-1']
        after = [r['predicted_sqm'] for r in changed['predictions'] if r['held_out_block']=='BLOCK-1']
        np.testing.assert_allclose(before,after)  # held-out labels cannot affect that fold

    def test_reject_missing_bad_or_mixed_data(self):
        for key, value in [('radiance_nw_cm2_sr',-1), ('sqm_mag_arcsec2',float('nan')),
                           ('cloud_fraction',1.1), ('qa_valid',''), ('source_id',''),
                           ('date','yesterday'), ('provenance','measured')]:
            with self.subTest(key=key):
                rows = copy.deepcopy(self.rows); rows[0][key] = value
                with self.assertRaises(ValueError):
                    validate(rows)

    def test_duplicates_and_small_data(self):
        with self.assertRaises(ValueError):
            validate(self.rows+[self.rows[0]])
        with self.assertRaises(ValueError):
            evaluate(self.rows[:16])

    def test_site_cannot_cross_blocks(self):
        self.rows[1]['block_id']='other'
        with self.assertRaises(ValueError):
            validate(self.rows)

    def test_qa_excluded_labels_do_not_train(self):
        before=evaluate(self.rows)
        for row in self.rows:
            if not row['qa_valid']:
                row['sqm_mag_arcsec2']=25
        after=evaluate(self.rows)
        np.testing.assert_allclose(before['model']['coef'],after['model']['coef'])

    def test_scenario_physics(self):
        self.assertEqual(scenario(18,.8,0)['sqm_after'],18)
        self.assertEqual(scenario(18,0,.5)['sqm_after'],18)
        self.assertAlmostEqual(scenario(18,.5,1)['gain_mag_arcsec2'],.752574989,places=7)
        self.assertGreater(scenario(18,.8,.4)['sqm_after'],scenario(18,.8,.2)['sqm_after'])
        for f,r in [(1,1),(-.1,.5),(.5,1.1)]:
            with self.assertRaises(ValueError):
                scenario(18,f,r)


if __name__ == '__main__':
    unittest.main()

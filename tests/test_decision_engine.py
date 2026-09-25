import unittest
from decision_engine import sqm_to_nelm,sqm_to_bortle,status,haversine,_site_layer
class DecisionTests(unittest.TestCase):
 def test_nelm_increases_with_darker_sky(self): self.assertGreater(sqm_to_nelm(21.5),sqm_to_nelm(18))
 def test_bortle_boundaries(self): self.assertEqual(sqm_to_bortle(21.8),1);self.assertEqual(sqm_to_bortle(14),9)
 def test_status_thresholds(self): self.assertEqual(status(.72),'GO');self.assertEqual(status(.5),'MARGINAL');self.assertEqual(status(.2),'NO-GO')
 def test_distance_and_real_static_layer(self):
  self.assertLess(haversine((36.34,43.13),(36.45,43.35)),30)
  sites={x['id']:x for x in _site_layer()};self.assertGreater(sites['hatra']['static'],sites['mosul']['static']);self.assertIn('radiance',sites['hatra'])
if __name__=='__main__':unittest.main()

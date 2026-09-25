import tempfile, unittest
from pathlib import Path
import field_validation as fv

class FieldValidationTests(unittest.TestCase):
    def test_metrics_and_marginal_policy(self):
        with tempfile.TemporaryDirectory() as d:
            old=fv.PATH; fv.PATH=Path(d)/"observations.csv"
            try:
                for status, actual, score in [("GO",True,.8),("GO",False,.8),("NO-GO",False,.2),("NO-GO",True,.2),("MARGINAL",True,.5)]:
                    fv.append_observation({"site_id":"test","prediction_status":status,"predicted_score":score,"observed_success":actual})
                m=fv.metrics()
                self.assertEqual(m["confusion_matrix"], {"tp":1,"fp":1,"tn":1,"fn":1})
                self.assertEqual(m["accuracy"], .5); self.assertEqual(m["f1"], .5)
                self.assertEqual(m["marginal_observations"], 1)
            finally: fv.PATH=old

if __name__ == "__main__": unittest.main()

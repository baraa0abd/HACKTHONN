import json, unittest
from pathlib import Path
import numpy as np, pandas as pd
from build_osdr_dataset import DENY, label
from train_osdr_model import proxy_audit

D = Path(__file__).resolve().parent.parent / 'data' / 'osdr'
class OsdrTests(unittest.TestCase):
 def test_label_mapping(self):
  self.assertEqual([label(v) for v in ('Space Flight','in-flight','Ground Control','Vivarium Control','Ground','pre-flight','post-flight Control','NaN')],[1,1,0,0,0,None,None,None])
 def test_proxy_audit_catches_restated_label(self):
  X = pd.DataFrame({'leak':['iss','earth']*4,'noise':['a','a','b','b']*2}); y = np.array([1,0]*4); g = np.array(['s1']*4+['s2']*4)
  r = proxy_audit(X, y, g); self.assertEqual(r['leak'], 1.0); self.assertEqual(r['noise'], 0.0)
 @unittest.skipUnless((D/'train.csv').exists(), 'run build_osdr_dataset.py first')
 def test_split_has_no_study_overlap_or_denied_fields(self):
  tr, te = (pd.read_csv(D/f, usecols=['accession'], encoding='utf-8-sig') for f in ('train.csv','test.csv'))
  self.assertFalse(set(tr.accession) & set(te.accession))
  cols = json.loads((D/'manifest.json').read_text())['feature_columns']
  self.assertFalse([c for c in cols for d in ('habitat','location','gravity','hardware','environment') if d in c])
if __name__ == '__main__': unittest.main()

class OsdrGeneTests(unittest.TestCase):
 def test_zscore_within_is_label_free_and_centred(self):
  from train_osdr_genes import zscore_within
  z = zscore_within(pd.DataFrame({'a':[1.,5.],'b':[3.,5.],'c':[5.,5.]}, index=['g1','g2']))
  self.assertTrue(np.allclose(z.loc['g1'], [-1,0,1])); self.assertTrue((z.loc['g2'] == 0).all())  # constant gene -> 0
 def test_within_study_auc_ignores_between_study_offsets(self):
  from train_osdr_genes import within_study_auc
  y = np.array([0,1,0,1]); g = np.array(['s1','s1','s2','s2'])
  self.assertEqual(within_study_auc(y, np.array([.1,.2,.8,.9]), g), (1.0, 2))
 @unittest.skipUnless((Path(__file__).resolve().parent.parent/'data'/'osdr_genes'/'genes_test.csv.gz').exists(), 'run build_osdr_genes.py first')
 def test_gene_split_matches_metadata_split(self):
  G = D.parent / 'osdr_genes'
  tr, te = (pd.read_csv(G/f, usecols=['accession']) for f in ('genes_train.csv.gz','genes_test.csv.gz'))
  meta_test = set(pd.read_csv(D/'test.csv', usecols=['accession'], encoding='utf-8-sig').accession)
  self.assertFalse(set(tr.accession) & set(te.accession)); self.assertTrue(set(te.accession) <= meta_test)

class OsdrApiTests(unittest.TestCase):
 def setUp(self):
  import sys; sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'dashboard'))
  import osdr_api; self.api = osdr_api
 def test_rejects_unknown_fields_and_bad_values(self):
  for bad in ({}, {'label':'1'}, {'char_organism': 1}, {'char_organism': 'x'*500}):
   with self.assertRaises(ValueError): self.api.predict(bad)
 @unittest.skipUnless((Path(__file__).resolve().parent.parent/'models'/'osdr_flight_model.joblib').exists(), 'train first')
 def test_predict_returns_probability_and_flags_unseen(self):
  r = self.api.predict({'char_organism': 'mus musculus', 'char_material_type': 'not-a-real-tissue'})
  self.assertTrue(0 < r['p_space_flight'] < 1); self.assertEqual(r['unseen_values'], ['char_material_type'])

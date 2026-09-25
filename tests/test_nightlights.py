import copy
import unittest

from nightlights import analyse, validate


def records():
    rows=[]
    for code,name,base in (("IRQ001001","A",.2),("IRQ001002","B",1.0)):
        for year in range(2020,2025):
            rows.append({"ISO_A3":"IRQ","ADM1CD_c":"IRQ001","ADM2CD_c":code,"NAM_0":"Iraq","NAM_1":"Al-Anbar","NAM_2":name,"year":str(year),
                         "ntl_quality_prop_na":"0","ntl_quality_prop_0_good":"0.95","ntl_quality_prop_1_poor":"0.03","ntl_quality_prop_2_gapfilled":"0.02",
                         "ntl_nogf_5km_mean":str(base*(1+.1*(year-2020))),"ntl_nogf_5km_median":str(base*.5),"ntl_nogf_5km_q95":str(base*2)})
    return rows


class NightlightTests(unittest.TestCase):
    def test_real_analysis_math_and_ranking(self):
        result=analyse(records())
        self.assertEqual(result["records"],10);self.assertEqual(result["districts"],2)
        self.assertEqual(result["dark_screening_candidates"][0]["district"],"A")
        self.assertAlmostEqual(result["dark_screening_candidates"][0]["change_percent"],40)

    def test_reject_non_iraq_duplicate_and_bad_quality(self):
        for mutate in (lambda r:r.__setitem__("ISO_A3","USA"), lambda r:r.__setitem__("ntl_quality_prop_0_good","2")):
            data=records();mutate(data[0])
            with self.assertRaises(ValueError):validate(data)
        with self.assertRaises(ValueError):validate(records()+[copy.deepcopy(records()[0])])

    def test_incomplete_time_series_fails_closed(self):
        data=records();data.pop()
        with self.assertRaisesRegex(ValueError,"Incomplete"):
            analyse(data)


if __name__ == "__main__": unittest.main()

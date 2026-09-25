import unittest
from backtest import START,END
class BacktestTests(unittest.TestCase):
 def test_period_is_at_least_12_months(self):self.assertGreaterEqual((END-START).days,364)

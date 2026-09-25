import tempfile
from pathlib import Path
import unittest

from openpyxl import Workbook

from telemetry import analyse_pass, load_passes


HEADER = ["Time Stamp", "Vbat (V)", "Ibatt(mA)"] + [f"V{x} (mV)" for x in ("py","px","mz","mx","pz")] + [f"I{x} (mA)" for x in ("py","px","mz","mx","pz")]


class TelemetryTests(unittest.TestCase):
    def make_book(self, directory, rows):
        book = Workbook(); sheet = book.active; sheet.title = "Orbit 1"; sheet.append(HEADER)
        for row in rows: sheet.append(row)
        path = Path(directory) / "SAT.xlsx"; book.save(path); return path

    def test_real_units_and_trapezoidal_energy(self):
        with tempfile.TemporaryDirectory() as directory:
            row = [0, 4.0, 100] + [1000]*5 + [100]*5
            row2 = [3600, 4.0, -100] + [1000]*5 + [100]*5
            self.make_book(directory, [row, row2])
            records, _ = load_passes(Path(directory)); result = analyse_pass(records[0])
            self.assertAlmostEqual(result["solar_mean_w"], .5)
            self.assertAlmostEqual(result["solar_energy_wh"], .5)
            self.assertAlmostEqual(result["battery_net_terminal_wh"], 0)

    def test_invalid_row_is_rejected_and_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            good = [0, 4.0, 100] + [1000]*5 + [100]*5
            bad = [5, 4.0, 100] + [None]*5 + [100]*5
            last = [10, 4.0, 100] + [1000]*5 + [100]*5
            self.make_book(directory, [good, bad, last])
            records, _ = load_passes(Path(directory))
            self.assertEqual(records[0]["rows_rejected"], 1)
            self.assertEqual(records[0]["rows_accepted"], 2)

    def test_non_monotonic_time_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            row = [5, 4.0, 100] + [1000]*5 + [100]*5
            row2 = [4, 4.0, 100] + [1000]*5 + [100]*5
            self.make_book(directory, [row, row2])
            with self.assertRaisesRegex(ValueError, "timestamps"):
                load_passes(Path(directory))


if __name__ == "__main__": unittest.main()

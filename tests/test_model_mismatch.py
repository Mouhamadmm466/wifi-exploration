"""Check that the diagnostic changes truth without leaking it to candidates."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from roaming import make_trace, prepare
from run_model_mismatch import alter_truth


class MismatchTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "configs/study.json").read_text())
        trace = make_trace(self.config, "hotspots", 1001)
        self.prepared = prepare(self.config, trace, "bulk", 8.0)

    def test_unit_factor_reproduces_original_truth(self):
        changed = alter_truth(self.prepared, self.config, [1.0] * 6)
        self.assertEqual(changed.truth, self.prepared.truth)

    def test_lower_capacity_changes_truth_but_not_predictions(self):
        changed = alter_truth(self.prepared, self.config, [0.5] * 6)
        self.assertIs(changed.reported, self.prepared.reported)
        self.assertIs(changed.signal, self.prepared.signal)
        self.assertIs(changed.report_ages, self.prepared.report_ages)
        for old_row, new_row in zip(self.prepared.truth, changed.truth):
            for old, new in zip(old_row, new_row):
                self.assertAlmostEqual(new.residual_mbps, old.residual_mbps * 0.5)
                self.assertLessEqual(new.delivery_fraction, old.delivery_fraction)


if __name__ == "__main__":
    unittest.main()

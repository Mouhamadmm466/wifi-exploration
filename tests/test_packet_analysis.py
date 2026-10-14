import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('packet_analysis',Path(__file__).resolve().parents[1]/'scripts/analyze_packet_study.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class StatisticalAccountingTests(unittest.TestCase):
    def rows(self):
        rows=[]
        for scenario,base in [('a',.1),('b',.8)]:
            for seed in [1,2,3]:
                for policy,delta in [('app_myopic',0),('predictive',-.02)]:
                    rows.append(dict(condition='main',scenario=scenario,seed=seed,policy=policy,
                                     call_miss_fraction=base+delta,voice_missed_fraction=base+delta,
                                     video_missed_fraction=base+delta))
        return rows

    def test_paired_constant_effect_does_not_use_between_scenario_spread(self):
        with tempfile.TemporaryDirectory() as directory:
            _, contrasts=a.analyze(self.rows(),Path(directory))
        c=next(r for r in contrasts if r['scope']=='all' and r['metric']=='call_miss_fraction')
        self.assertEqual(c['seed_blocks'],3)
        self.assertEqual(c['paired_worlds'],6)
        self.assertAlmostEqual(c['difference'],-.02)
        self.assertAlmostEqual(c['ci_low'],-.02)
        self.assertAlmostEqual(c['ci_high'],-.02)

    def test_partial_policy_cell_rejected(self):
        with self.assertRaises(ValueError): a.validate_grid(self.rows()[:-1])

    def test_missing_world_rejected(self):
        rows=[r for r in self.rows() if not(r['scenario']=='a' and r['seed']==1)]
        with self.assertRaises(ValueError): a.validate_grid(rows)

    def test_unpaired_input_rejected(self):
        rows=self.rows()
        for r in rows:r['input_sha256']='common'
        rows[0]['input_sha256']='different'
        with self.assertRaises(ValueError):a.validate_grid(rows)

if __name__=='__main__':unittest.main()

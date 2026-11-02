import unittest
from pathlib import Path

from decisionbench_dd_docking.redocking_rerank_sensitivity import main

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestRedockingRerankSensitivityIntegration(unittest.TestCase):
    """Runs against the real, already-committed 14-case docking_runs/ --
    no fixture bloat needed, this data already lives in the repo."""

    def test_native_rank1_selector_reproduces_frozen_primary_success_at_1(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            rc = main([
                "--poses-dir", str(REPO_ROOT / "docking_runs"),
                "--out-dir", str(out_dir),
            ])
            self.assertEqual(rc, 0)

            import csv
            with open(out_dir / "redocking_rerank_sensitivity.csv") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 14)
            n_native_success = sum(1 for r in rows if r["native_rank1_success_at_1"] == "True")
            # Frozen primary result: GNINA Success@1 = 3/14 (21.4%) -- the
            # native_rank1 selector must reproduce this exactly, since it's
            # the same selection rule the primary result already uses.
            self.assertEqual(n_native_success, 3)

            md = (out_dir / "redocking_rerank_sensitivity.md").read_text()
            self.assertIn("native_rank1", md)
            self.assertIn("does not change the frozen primary result", md)
            self.assertIn("Median RMSD", md)
            # Independently verified: native_rank1's median RMSD is 4.64 A.
            self.assertIn("4.64 A", md)


if __name__ == "__main__":
    unittest.main()

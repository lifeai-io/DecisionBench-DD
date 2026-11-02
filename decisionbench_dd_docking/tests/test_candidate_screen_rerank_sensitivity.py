import csv
import tempfile
import unittest
from pathlib import Path

from decisionbench_dd_docking.candidate_screen_rerank_sensitivity import main

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CANDIDATE_SCREEN_RUNS = REPO_ROOT / "candidate_screen_runs"


@unittest.skipUnless(CANDIDATE_SCREEN_RUNS.is_dir(), "real candidate_screen_runs/ not present")
class TestCandidateScreenRerankSensitivityIntegration(unittest.TestCase):
    """Runs against the real, already-committed 146-job candidate screen --
    no fixture bloat needed."""

    def test_native_rank1_reproduces_frozen_primary_pass_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            rc = main(["--runs-dir", str(CANDIDATE_SCREEN_RUNS), "--out-dir", str(out_dir)])
            self.assertEqual(rc, 0)

            with open(out_dir / "best_of_5_rescue.csv") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 69)
            n_native_pass = sum(1 for r in rows if r["native_rank1_pass"] == "True")
            # Frozen primary result: 15 GenMol + 1 MolMIM = 16 pass.
            self.assertEqual(n_native_pass, 16)
            # Best-of-5 can only ever find at least as many passes as rank-1 alone.
            n_best_of_5 = sum(1 for r in rows if r["best_of_5_pass"] == "True")
            self.assertGreaterEqual(n_best_of_5, n_native_pass)

            with open(out_dir / "selector_sensitivity.csv") as fh:
                selector_rows = {r["selector"]: r for r in csv.DictReader(fh)}
            self.assertEqual(int(selector_rows["native_rank1"]["n_pass_total"]), 16)

            md = (out_dir / "rerank_sensitivity.md").read_text()
            self.assertIn("does not change the frozen primary result", md)
            self.assertIn("Advancement population", md)

            with open(out_dir / "candidate_selector_turnover.csv") as fh:
                turnover_rows = list(csv.DictReader(fh))
            self.assertEqual(len(turnover_rows), 69 * 3)  # one row per candidate per selector
            n_native_pass_from_turnover = sum(
                1 for r in turnover_rows if r["selector"] == "native_rank1" and r["pass"] == "True"
            )
            self.assertEqual(n_native_pass_from_turnover, 16)


if __name__ == "__main__":
    unittest.main()

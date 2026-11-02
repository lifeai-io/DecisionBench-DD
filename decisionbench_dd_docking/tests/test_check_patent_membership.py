import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MOLBLOOM_AVAILABLE = importlib.util.find_spec("molbloom") is not None

if MOLBLOOM_AVAILABLE:
    from decisionbench_dd_docking.check_patent_membership import SURECHEMBL_CACHE, main
    from decisionbench_dd_docking.triage_primary_candidates import CANDIDATE_RESULTS


@unittest.skipUnless(MOLBLOOM_AVAILABLE, "molbloom not installed (optional dependency)")
class TestSanityCheckLogic(unittest.TestCase):
    """The Ambroxol-must-be-True sanity check is the load-bearing safety net
    here (a stale/corrupt/wrong filter would otherwise silently produce a
    '0/16 in patents' result indistinguishable from a real finding) -- must
    stay enforced even without the real 200 MB filter downloaded."""

    def test_returns_error_if_ambroxol_sanity_check_fails(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch("decisionbench_dd_docking.check_patent_membership.CANDIDATE_RESULTS", Path(tmp) / "fake.csv"):
            (Path(tmp) / "fake.csv").write_text("candidate_id,structural_proxy_pass\nX,True\n")
            # Patch molbloom.buy to always return False, simulating a broken/stale filter.
            with patch("molbloom.buy", return_value=False), \
                 patch("decisionbench_dd_docking.check_patent_membership.load_passing_candidates", return_value=[]):
                rc = main([])
                self.assertEqual(rc, 1)


@unittest.skipUnless(MOLBLOOM_AVAILABLE and CANDIDATE_RESULTS.is_file() if MOLBLOOM_AVAILABLE else False, "real candidate-screen results not present")
@unittest.skipUnless(MOLBLOOM_AVAILABLE and SURECHEMBL_CACHE.is_file() if MOLBLOOM_AVAILABLE else False, "SureChEMBL bloom filter not already downloaded/cached locally -- skipping rather than forcing a ~200MB download in tests")
class TestCheckPatentMembershipIntegration(unittest.TestCase):
    def test_predicts_all_17_molecules_and_ambroxol_sanity_check_passes(self):
        from decisionbench_dd_docking import check_patent_membership

        with tempfile.TemporaryDirectory() as tmp:
            original_out_dir = check_patent_membership.OUT_DIR
            check_patent_membership.OUT_DIR = Path(tmp)
            try:
                rc = check_patent_membership.main([])
            finally:
                check_patent_membership.OUT_DIR = original_out_dir
            self.assertEqual(rc, 0)

            with open(Path(tmp) / "patent_membership.csv") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 17)
            ambroxol = next(r for r in rows if r["candidate_id"] == "CTRL_AMBROXOL")
            self.assertEqual(ambroxol["in_surechembl_patent_literature"], "True")

            md = (Path(tmp) / "patent_membership.md").read_text()
            self.assertIn("NOT a similarity-based patent-proximity search", md)
            self.assertIn("sanity check passed", md)


if __name__ == "__main__":
    unittest.main()

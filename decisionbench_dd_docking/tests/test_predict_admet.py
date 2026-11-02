import csv
import importlib.util
import unittest
from pathlib import Path

from decisionbench_dd_docking.predict_admet import AMBROXOL_SMILES, HEADLINE_ENDPOINTS, OUT_DIR
from decisionbench_dd_docking.triage_primary_candidates import CANDIDATE_RESULTS

ADMET_AI_AVAILABLE = importlib.util.find_spec("admet_ai") is not None


class TestAmbroxolSmilesConsistency(unittest.TestCase):
    def test_matches_the_seed_smiles_used_throughout_this_project(self):
        # Must stay byte-identical to DESCRIPTION.md's seed / prepare_candidate_screen_ligands.py's
        # CTRL_AMBROXOL entry -- this script predicts ADMET for a *different*
        # code path than the docking controls, so a drift here wouldn't be
        # caught by any docking test.
        from decisionbench_dd_docking.prepare_candidate_screen_ligands import CONTROLS
        ambroxol_control = next(c for c in CONTROLS if c[0] == "CTRL_AMBROXOL")
        self.assertEqual(AMBROXOL_SMILES, ambroxol_control[2])


@unittest.skipUnless(ADMET_AI_AVAILABLE, "admet_ai not installed (optional, heavy dependency)")
@unittest.skipUnless(CANDIDATE_RESULTS.is_file(), "real candidate-screen results not present")
class TestPredictAdmetIntegration(unittest.TestCase):
    def test_predicts_all_17_molecules_with_headline_endpoints_present(self):
        import tempfile

        from decisionbench_dd_docking import predict_admet

        with tempfile.TemporaryDirectory() as tmp:
            original_out_dir = predict_admet.OUT_DIR
            predict_admet.OUT_DIR = Path(tmp)
            try:
                rc = predict_admet.main([])
            finally:
                predict_admet.OUT_DIR = original_out_dir
            self.assertEqual(rc, 0)

            with open(Path(tmp) / "admet_predictions.csv") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 17)  # 16 candidates + Ambroxol
            self.assertIn("CTRL_AMBROXOL", {r["candidate_id"] for r in rows})
            for endpoint in HEADLINE_ENDPOINTS:
                self.assertIn(endpoint, rows[0])

            md = (Path(tmp) / "admet_predictions.md").read_text()
            self.assertIn("MODEL PREDICTIONS, not experimental measurements", md)


if __name__ == "__main__":
    unittest.main()

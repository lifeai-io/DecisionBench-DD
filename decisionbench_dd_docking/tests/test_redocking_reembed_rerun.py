import json
import unittest
from pathlib import Path

from decisionbench_dd_docking.redocking_reembed_rerun import GCASE_DIR, RERUN_DIR, CASE_LIST_PATH, main

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestRedockingReembedRerunIntegration(unittest.TestCase):
    """Runs against the real, already-committed 14-case gcase_validation/ set
    -- no fixture bloat needed. Confirms the rerun is genuinely read-only
    against the frozen inputs and produces a full 14-row report."""

    @classmethod
    def setUpClass(cls):
        with open(CASE_LIST_PATH) as fh:
            cls.frozen_case_list_before = fh.read()

    def test_leaves_frozen_case_list_untouched(self):
        rc = main()
        self.assertEqual(rc, 0)
        with open(CASE_LIST_PATH) as fh:
            after = fh.read()
        self.assertEqual(self.frozen_case_list_before, after)

    def test_writes_one_row_per_case_without_touching_frozen_ligands(self):
        with open(CASE_LIST_PATH) as fh:
            cases = json.load(fh)["cases"]
        frozen_ligand_mtimes = {
            c["pdb_id"]: (GCASE_DIR / c["docking_input_ligand_file"]).stat().st_mtime for c in cases
        }

        rc = main()
        self.assertEqual(rc, 0)

        with open(RERUN_DIR / "embedding_reproducibility_report.json") as fh:
            report = json.load(fh)
        self.assertEqual(len(report), len(cases))
        self.assertEqual({r["pdb_id"] for r in report}, {c["pdb_id"] for c in cases})

        for c in cases:
            new_mtime = (GCASE_DIR / c["docking_input_ligand_file"]).stat().st_mtime
            self.assertEqual(frozen_ligand_mtimes[c["pdb_id"]], new_mtime, f"{c['pdb_id']}'s frozen ligand file was touched")

        for row in report:
            self.assertTrue(row["rerun_embed_ok"])
            self.assertFalse(row["smiles_changed"], f"{row['pdb_id']}: protonated SMILES selection should be reproducible")


if __name__ == "__main__":
    unittest.main()

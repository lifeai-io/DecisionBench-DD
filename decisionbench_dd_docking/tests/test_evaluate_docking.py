import csv
import json
import tempfile
import unittest
from pathlib import Path

from rdkit import Chem
from rdkit.Geometry import Point3D

from decisionbench_dd_docking.evaluate_docking import GCASE_DIR, load_cases, main

CASE_LIST = GCASE_DIR / "gcase_validation_set_v1.0.json"


def _translate(mol, dx):
    mol = Chem.Mol(mol)
    conf = mol.GetConformer()
    for i in range(mol.GetNumAtoms()):
        p = conf.GetAtomPosition(i)
        conf.SetAtomPosition(i, Point3D(p.x + dx, p.y, p.z))
    return mol


class TestEvaluateDockingIntegration(unittest.TestCase):
    """Exercises the full CLI against synthetic pose sets built from the
    real, already-frozen reference ligands (no fixture bloat needed -- these
    files already live in the repo). Not real docking output: real GNINA/
    DiffDock-L runs happen on the user's GPU instance (Task 4)."""

    def test_cli_runs_end_to_end_over_all_14_cases(self):
        cases = load_cases(CASE_LIST)
        self.assertEqual(len(cases), 14)

        with tempfile.TemporaryDirectory() as tmp:
            poses_dir = Path(tmp) / "docking_runs"
            out_dir = Path(tmp) / "results"
            (poses_dir / "gnina").mkdir(parents=True)
            (poses_dir / "diffdock").mkdir(parents=True)

            for case in cases:
                ref = Chem.SDMolSupplier(str(GCASE_DIR / case["reference_ligand_file"]))[0]
                # gnina: a "good" top-1 pose (0.5 A off) then a worse one
                gnina_path = poses_dir / "gnina" / f"{case['pdb_id']}_poses.sdf"
                w = Chem.SDWriter(str(gnina_path))
                w.write(_translate(ref, 0.5))
                w.write(_translate(ref, 5.0))
                w.close()
                # diffdock: a "bad" top-1 pose (9 A off) that only recovers at rank 2
                diffdock_path = poses_dir / "diffdock" / f"{case['pdb_id']}_poses.sdf"
                w = Chem.SDWriter(str(diffdock_path))
                w.write(_translate(ref, 9.0))
                w.write(_translate(ref, 1.0))
                w.close()

            rc = main(["--poses-dir", str(poses_dir), "--out-dir", str(out_dir)])
            self.assertEqual(rc, 0)

            self.assertTrue((out_dir / "per_case_rmsd.csv").is_file())
            self.assertTrue((out_dir / "summary.json").is_file())
            self.assertTrue((out_dir / "summary.md").is_file())

            with open(out_dir / "per_case_rmsd.csv") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 28)  # 14 cases x 2 tools

            summary = json.loads((out_dir / "summary.json").read_text())
            # gnina's top-1 pose (0.5 A) should succeed on essentially every case
            self.assertGreater(summary["gnina"]["success_at_1_2.0A_pct"], 90.0)
            # diffdock's top-1 pose (9 A) should fail Success@1 everywhere...
            self.assertEqual(summary["diffdock"]["success_at_1_2.0A_pct"], 0.0)
            # ...but recover at Success@5 via rank 2 (1 A)
            self.assertGreater(summary["diffdock"]["success_at_5_2.0A_pct"], 90.0)
            # strata add up to 14
            total_stratified = sum(sv["n"] for sv in summary["gnina"]["by_stratum"].values())
            self.assertEqual(total_stratified, 14)

    def test_median_top1_rmsd_averages_middle_two_for_even_case_count(self):
        # Regression test: median_top1_rmsd was previously computed as
        # sorted(values)[len(values) // 2], which silently picks the
        # upper-middle element instead of averaging the two middle values for
        # an even-length list -- caught by cross-checking the real 14-case
        # result against an independent statistics.median() computation.
        cases = load_cases(CASE_LIST)[:2]
        with tempfile.TemporaryDirectory() as tmp:
            poses_dir = Path(tmp) / "docking_runs"
            out_dir = Path(tmp) / "results"
            (poses_dir / "gnina").mkdir(parents=True)
            # Two cases with top-1 RMSDs of 1.0 A and 3.0 A -- true median is
            # 2.0 A; the old buggy code would have reported 3.0 A.
            for case, dx in zip(cases, [1.0, 3.0]):
                ref = Chem.SDMolSupplier(str(GCASE_DIR / case["reference_ligand_file"]))[0]
                p = poses_dir / "gnina" / f"{case['pdb_id']}_poses.sdf"
                w = Chem.SDWriter(str(p))
                w.write(_translate(ref, dx))
                w.close()
            rc = main(["--poses-dir", str(poses_dir), "--out-dir", str(out_dir), "--case-list", str(CASE_LIST)])
            self.assertEqual(rc, 0)
            summary = json.loads((out_dir / "summary.json").read_text())
            self.assertAlmostEqual(summary["gnina"]["median_top1_rmsd"], 2.0, places=2)

    def test_missing_tool_directory_is_skipped_not_fatal(self):
        cases = load_cases(CASE_LIST)
        with tempfile.TemporaryDirectory() as tmp:
            poses_dir = Path(tmp) / "docking_runs"
            (poses_dir / "gnina").mkdir(parents=True)
            for case in cases[:2]:
                ref = Chem.SDMolSupplier(str(GCASE_DIR / case["reference_ligand_file"]))[0]
                p = poses_dir / "gnina" / f"{case['pdb_id']}_poses.sdf"
                w = Chem.SDWriter(str(p))
                w.write(ref)
                w.close()
            out_dir = Path(tmp) / "results"
            rc = main(["--poses-dir", str(poses_dir), "--out-dir", str(out_dir)])
            self.assertEqual(rc, 0)
            summary = json.loads((out_dir / "summary.json").read_text())
            self.assertIn("gnina", summary)
            self.assertNotIn("diffdock", summary)


if __name__ == "__main__":
    unittest.main()

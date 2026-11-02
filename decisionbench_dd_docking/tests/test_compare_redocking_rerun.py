import csv
import json
import tempfile
import unittest
from pathlib import Path

from decisionbench_dd_docking.compare_redocking_rerun import main

FIELDNAMES = ["tool", "pdb_id", "site_stratum", "n_poses_scored", "top1_rmsd", "best_of_n_rmsd",
              "success_at_1", "success_at_n", "top1_valid", "pose_rmsds", "pose_valid",
              "n_poses_charge_artifact_fixed", "error"]


def _write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _row(pdb_id, top1_rmsd, success_at_1, success_at_n):
    return {
        "tool": "gnina", "pdb_id": pdb_id, "site_stratum": "allosteric", "n_poses_scored": 5,
        "top1_rmsd": top1_rmsd, "best_of_n_rmsd": top1_rmsd, "success_at_1": success_at_1,
        "success_at_n": success_at_n, "top1_valid": True, "pose_rmsds": "", "pose_valid": "",
        "n_poses_charge_artifact_fixed": 0, "error": "",
    }


class TestCompareRedockingRerun(unittest.TestCase):
    def test_detects_success_at_1_flip_in_both_directions(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            frozen_csv = tmp / "frozen.csv"
            rerun_csv = tmp / "rerun.csv"
            out_dir = tmp / "out"

            _write_csv(frozen_csv, [
                _row("AAAA", 1.0, "True", "True"),   # stays success
                _row("BBBB", 3.0, "False", "False"),  # flips to success
                _row("CCCC", 1.5, "True", "True"),   # flips to failure
            ])
            _write_csv(rerun_csv, [
                _row("AAAA", 1.1, "True", "True"),
                _row("BBBB", 1.9, "True", "True"),
                _row("CCCC", 4.0, "False", "True"),
            ])

            rc = main(["--frozen", str(frozen_csv), "--rerun", str(rerun_csv), "--out-dir", str(out_dir)])
            self.assertEqual(rc, 0)

            report = json.loads((out_dir / "gnina_rerun_vs_frozen.json").read_text())
            self.assertEqual(report["n_cases"], 3)
            self.assertEqual(report["frozen_success_at_1"], "2/3")
            self.assertEqual(report["rerun_success_at_1"], "2/3")
            self.assertEqual(report["n_cases_success_at_1_changed"], 2)

            changed = {r["pdb_id"] for r in report["per_case"] if r["success_at_1_changed"]}
            self.assertEqual(changed, {"BBBB", "CCCC"})

    def test_mismatched_case_sets_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            frozen_csv = tmp / "frozen.csv"
            rerun_csv = tmp / "rerun.csv"
            _write_csv(frozen_csv, [_row("AAAA", 1.0, "True", "True")])
            _write_csv(rerun_csv, [_row("ZZZZ", 1.0, "True", "True")])
            rc = main(["--frozen", str(frozen_csv), "--rerun", str(rerun_csv), "--out-dir", str(tmp / "out")])
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()

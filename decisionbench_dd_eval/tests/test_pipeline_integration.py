import csv
import tempfile
import unittest
from pathlib import Path

from decisionbench_dd_eval.evaluate_generators import main

FIXTURE_MANIFEST_DIR = Path(__file__).parent / "fixtures" / "manifests"


class TestPipelineIntegration(unittest.TestCase):
    def test_cli_runs_end_to_end_over_fixtures(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "results"
            rc = main(["--manifest-dir", str(FIXTURE_MANIFEST_DIR), "--out-dir", str(out_dir), "--n-boot", "200"])
            self.assertEqual(rc, 0)

            for name in (
                "molecule_level.csv",
                "table1_generator_scorecard.csv",
                "figure2_similarity_qed_scatter.csv",
                "figure4_funnel.csv",
                "summary.md",
                "summary.json",
            ):
                self.assertTrue((out_dir / name).is_file(), f"missing output {name}")

            with open(out_dir / "table1_generator_scorecard.csv") as fh:
                rows = list(csv.DictReader(fh))
            tools_and_runs = {(r["tool"], r["run_id"]) for r in rows}
            for tool in ("genmol", "molmim"):
                for run_id in ("replicate_01", "replicate_02", "replicate_03", "pooled"):
                    self.assertIn((tool, run_id), tools_and_runs)

            with open(out_dir / "molecule_level.csv") as fh:
                mol_rows = list(csv.DictReader(fh))
            self.assertGreater(len(mol_rows), 0)
            invalid_rows = [r for r in mol_rows if r["valid"] == "False"]
            self.assertTrue(all(r["qualified"] == "False" for r in invalid_rows))

            with open(out_dir / "figure4_funnel.csv") as fh:
                funnel_rows = list(csv.DictReader(fh))
            requested_rows = [r for r in funnel_rows if r["stage"] == "requested"]
            self.assertTrue(all(r["count"] == "300" for r in requested_rows))

    def test_missing_manifest_dir_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty_dir = Path(tmp) / "empty"
            empty_dir.mkdir()
            rc = main(["--manifest-dir", str(empty_dir), "--out-dir", str(Path(tmp) / "out")])
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()

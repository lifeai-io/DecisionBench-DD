import csv
import tempfile
import unittest
from pathlib import Path

from rdkit import Chem
from rdkit.Geometry import Point3D

from decisionbench_dd_docking.run_diffdock import build_batch_csv, merge_ranked_sdfs

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REAL_LIGAND_SDF = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "gcase_validation" / "reference_ligands" / "3GXF_IFM.sdf"


def _translate(mol, dx):
    mol = Chem.Mol(mol)
    conf = mol.GetConformer()
    for i in range(mol.GetNumAtoms()):
        p = conf.GetAtomPosition(i)
        conf.SetAtomPosition(i, Point3D(p.x + dx, p.y, p.z))
    return mol


class TestMergeRankedSdfs(unittest.TestCase):
    """DiffDock (verified against the actual gcorso/DiffDock repo) writes,
    per complex: rank{N}_confidence{score}.sdf for every rank, PLUS an extra
    unsuffixed rank1.sdf duplicate of the top pose only. A naive `rank*.sdf`
    glob double-counts rank 1 and can't be rank-sorted (rank1.sdf has no
    underscore to split on). merge_ranked_sdfs must read only the
    confidence-suffixed files."""

    def setUp(self):
        self.ref = Chem.SDMolSupplier(str(REAL_LIGAND_SDF))[0]
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.complex_dir = Path(self.tmpdir.name) / "3GXF"
        self.complex_dir.mkdir()

    def _write(self, name, mol):
        w = Chem.SDWriter(str(self.complex_dir / name))
        w.write(mol)
        w.close()

    def test_ignores_bare_rank1_duplicate_and_orders_by_rank(self):
        self._write("rank1_confidence1.50.sdf", _translate(self.ref, 0.5))
        self._write("rank1.sdf", _translate(self.ref, 0.5))  # duplicate of rank1, must not be double-counted
        self._write("rank2_confidence0.80.sdf", _translate(self.ref, 3.0))
        self._write("rank10_confidence-2.00.sdf", _translate(self.ref, 9.0))

        dest = Path(self.tmpdir.name) / "merged.sdf"
        n_written = merge_ranked_sdfs(self.complex_dir, n_samples=5, dest_sdf=dest)

        self.assertEqual(n_written, 3)  # not 4 -- the bare rank1.sdf must be excluded
        poses = Chem.SDMolSupplier(str(dest))
        mols = [m for m in poses]
        self.assertEqual(len(mols), 3)
        # rank order preserved: rank1 first, rank2 second, rank10 last (not lexicographic "10" < "2")
        conf0 = mols[0].GetConformer().GetAtomPosition(0)
        conf1 = mols[1].GetConformer().GetAtomPosition(0)
        conf2 = mols[2].GetConformer().GetAtomPosition(0)
        ref_x = self.ref.GetConformer().GetAtomPosition(0).x
        self.assertAlmostEqual(conf0.x - ref_x, 0.5, places=3)
        self.assertAlmostEqual(conf1.x - ref_x, 3.0, places=3)
        self.assertAlmostEqual(conf2.x - ref_x, 9.0, places=3)

    def test_respects_top_n_limit(self):
        for i in range(1, 6):
            self._write(f"rank{i}_confidence{i}.00.sdf", _translate(self.ref, float(i)))
        dest = Path(self.tmpdir.name) / "merged.sdf"
        n_written = merge_ranked_sdfs(self.complex_dir, n_samples=2, dest_sdf=dest)
        self.assertEqual(n_written, 2)

    def test_no_matching_files_returns_zero(self):
        dest = Path(self.tmpdir.name) / "merged.sdf"
        n_written = merge_ranked_sdfs(self.complex_dir, n_samples=5, dest_sdf=dest)
        self.assertEqual(n_written, 0)


class TestBuildBatchCsv(unittest.TestCase):
    def test_csv_has_expected_columns_and_smiles_in_ligand_description(self):
        cases = [
            {
                "pdb_id": "3GXF",
                "receptor_cropped_for_diffdock_file": "receptors_cropped_for_diffdock/3GXF_cropped.pdb",
                "docking_input_protonated_smiles": "OC[C@H]1C[NH2+]C[C@@H](O)[C@@H]1O",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            gcase_dir = repo_root / "decisionbench_dd_configs_v1.0" / "gcase_validation"
            gcase_dir.mkdir(parents=True)
            out_dir = repo_root / "docking_runs"
            csv_path = out_dir / "batch.csv"

            import decisionbench_dd_docking.run_diffdock as rd
            old_gcase_dir = rd.GCASE_DIR
            rd.GCASE_DIR = gcase_dir
            try:
                build_batch_csv(cases, csv_path, repo_root, out_dir)
            finally:
                rd.GCASE_DIR = old_gcase_dir

            with open(csv_path) as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(rows[0]["complex_name"], "3GXF")
            self.assertEqual(rows[0]["ligand_description"], "OC[C@H]1C[NH2+]C[C@@H](O)[C@@H]1O")
            self.assertTrue(rows[0]["protein_path"].startswith("/workspace/"))
            self.assertEqual(rows[0]["protein_sequence"], "")


if __name__ == "__main__":
    unittest.main()

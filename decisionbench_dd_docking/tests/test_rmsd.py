import math
import tempfile
import unittest
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Geometry import Point3D

from decisionbench_dd_docking.rmsd import (
    RMSDError,
    CaseResult,
    _fix_known_pose_charge_artifact,
    score_case,
    success_rate,
    symmetry_aware_rmsd,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REAL_LIGAND_SDF = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "gcase_validation" / "reference_ligands" / "3GXF_IFM.sdf"


def _translate(mol, dx, dy, dz):
    mol = Chem.Mol(mol)
    conf = mol.GetConformer()
    for i in range(mol.GetNumAtoms()):
        p = conf.GetAtomPosition(i)
        conf.SetAtomPosition(i, Point3D(p.x + dx, p.y + dy, p.z + dz))
    return mol


class TestSymmetryAwareRMSD(unittest.TestCase):
    def setUp(self):
        self.ref = Chem.SDMolSupplier(str(REAL_LIGAND_SDF))[0]
        self.assertIsNotNone(self.ref, "fixture reference ligand failed to load")

    def test_identical_pose_has_zero_rmsd(self):
        pose = Chem.Mol(self.ref)
        rmsd = symmetry_aware_rmsd(pose, self.ref)
        self.assertAlmostEqual(rmsd, 0.0, places=4)

    def test_translation_is_not_silently_realigned_away(self):
        # This is the core correctness property: CalcRMS must NOT behave like
        # GetBestRMS. A uniform 3 A translation of every atom must show up as
        # ~3.0 A RMSD, not be superposed away to ~0.
        pose = _translate(self.ref, 3.0, 0.0, 0.0)
        rmsd = symmetry_aware_rmsd(pose, self.ref)
        self.assertAlmostEqual(rmsd, 3.0, places=3)

    def test_larger_translation_gives_larger_rmsd(self):
        pose_near = _translate(self.ref, 1.0, 0.0, 0.0)
        pose_far = _translate(self.ref, 10.0, 0.0, 0.0)
        rmsd_near = symmetry_aware_rmsd(pose_near, self.ref)
        rmsd_far = symmetry_aware_rmsd(pose_far, self.ref)
        self.assertLess(rmsd_near, rmsd_far)

    def test_atom_count_mismatch_raises(self):
        # Build a trivially smaller molecule (benzene) as a mismatched "pose".
        other = Chem.MolFromSmiles("c1ccccc1")
        AllChem.Compute2DCoords(other)
        other = Chem.AddHs(other)
        AllChem.EmbedMolecule(other, randomSeed=1)
        with self.assertRaises(RMSDError):
            symmetry_aware_rmsd(other, self.ref)

    def test_same_atom_count_different_formal_charge_raises_rmsderror_not_runtimeerror(self):
        # rdMolAlign.CalcRMS raises a bare RuntimeError (not RMSDError) when no
        # substructure correspondence exists at all -- e.g. same heavy-atom
        # count but mismatched formal charges (exactly what happened in
        # practice: reference built neutral, pose built from a protonated
        # SMILES). symmetry_aware_rmsd must wrap this so callers scoring many
        # poses in a loop can catch RMSDError uniformly instead of crashing.
        neutral = Chem.MolFromSmiles("NCc1ccccc1")  # benzylamine, neutral
        charged = Chem.MolFromSmiles("[NH3+]Cc1ccccc1")  # same skeleton, protonated
        AllChem.EmbedMolecule(neutral, randomSeed=1)
        AllChem.EmbedMolecule(charged, randomSeed=1)
        self.assertEqual(neutral.GetNumAtoms(), charged.GetNumAtoms())
        with self.assertRaises(RMSDError):
            symmetry_aware_rmsd(charged, neutral)

    def test_known_pose_charge_artifact_is_neutralized_and_flagged(self):
        # Same skeleton as the real 9FAY/9FAZ/9FB2 bug: a neutral tertiary
        # sulfonamide N that DiffDock-L's own SDF output was empirically
        # observed to mislabel with formal charge +1 (net +2 overall instead
        # of the correct +1), with the amine's own [NH3+] charge untouched.
        correct = Chem.MolFromSmiles("CN(C[C@@H]([NH3+])c1ccccc1)S(=O)(=O)c1cc(F)cc(F)c1")
        artifact = Chem.MolFromSmiles("C[N+](C[C@@H]([NH3+])c1ccccc1)S(=O)(=O)c1cc(F)cc(F)c1")
        self.assertEqual(Chem.GetFormalCharge(correct), 1)
        self.assertEqual(Chem.GetFormalCharge(artifact), 2)

        fixed, was_fixed = _fix_known_pose_charge_artifact(artifact)
        self.assertTrue(was_fixed)
        self.assertEqual(Chem.GetFormalCharge(fixed), 1)

        unchanged, was_fixed_2 = _fix_known_pose_charge_artifact(correct)
        self.assertFalse(was_fixed_2)
        self.assertEqual(Chem.GetFormalCharge(unchanged), 1)

    def test_symmetric_ring_atom_relabeling_does_not_inflate_rmsd(self):
        # Benzene: rotating which ring atom is "atom 0" is a symmetry
        # operation that must not count as pose error under CalcRMS's
        # symmetry handling, even though the raw per-index RMSD without
        # symmetry matching would be large.
        mol = Chem.MolFromSmiles("c1ccccc1")
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, randomSeed=7)
        ref = Chem.Mol(mol)

        # Build a "pose" that is the same physical ring, just with atom
        # indices cyclically permuted -- same conformer geometry mapped onto
        # relabeled atoms of an isomorphic molecule.
        permuted = Chem.RenumberAtoms(mol, list(range(1, mol.GetNumAtoms())) + [0])
        rmsd = symmetry_aware_rmsd(permuted, ref)
        self.assertLess(rmsd, 0.01, "symmetry-equivalent relabeling should score ~0, not a large RMSD")


class TestScoreCase(unittest.TestCase):
    def setUp(self):
        self.ref = Chem.SDMolSupplier(str(REAL_LIGAND_SDF))[0]
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.ref_path = Path(self.tmpdir.name) / "ref.sdf"
        writer = Chem.SDWriter(str(self.ref_path))
        writer.write(self.ref)
        writer.close()

    def _write_poses(self, mols, name="poses.sdf"):
        path = Path(self.tmpdir.name) / name
        writer = Chem.SDWriter(str(path))
        for m in mols:
            writer.write(m)
        writer.close()
        return path

    def test_success_at_1_when_top_pose_is_close(self):
        poses = [_translate(self.ref, 0.5, 0.0, 0.0), _translate(self.ref, 10.0, 0.0, 0.0)]
        pose_path = self._write_poses(poses)
        result = score_case("TEST", "gnina", pose_path, self.ref_path)
        self.assertTrue(result.success_at_1)
        self.assertTrue(result.success_at_n)
        self.assertIsNone(result.error)

    def test_success_at_5_but_not_at_1(self):
        # Rank-1 pose is bad (8 A off), but pose 2 recovers within 2 A.
        poses = [_translate(self.ref, 8.0, 0.0, 0.0), _translate(self.ref, 1.0, 0.0, 0.0)]
        pose_path = self._write_poses(poses)
        result = score_case("TEST", "diffdock", pose_path, self.ref_path)
        self.assertFalse(result.success_at_1)
        self.assertTrue(result.success_at_n)

    def test_total_failure(self):
        poses = [_translate(self.ref, 20.0, 0.0, 0.0)]
        pose_path = self._write_poses(poses)
        result = score_case("TEST", "gnina", pose_path, self.ref_path)
        self.assertFalse(result.success_at_1)
        self.assertFalse(result.success_at_n)

    def test_missing_pose_file_reported_as_error_not_exception(self):
        result = score_case("TEST", "gnina", Path(self.tmpdir.name) / "does_not_exist.sdf", self.ref_path)
        self.assertIsNotNone(result.error)
        self.assertFalse(result.success_at_1)

    def test_score_case_recovers_rmsd_and_reports_charge_artifact_fix_count(self):
        correct = Chem.MolFromSmiles("CN(C[C@@H]([NH3+])c1ccccc1)S(=O)(=O)c1cc(F)cc(F)c1")
        artifact = Chem.MolFromSmiles("C[N+](C[C@@H]([NH3+])c1ccccc1)S(=O)(=O)c1cc(F)cc(F)c1")
        AllChem.EmbedMolecule(correct, randomSeed=3)
        AllChem.EmbedMolecule(artifact, randomSeed=3)
        pose = _translate(artifact, 0.5, 0.0, 0.0)

        ref_path = Path(self.tmpdir.name) / "charge_ref.sdf"
        w = Chem.SDWriter(str(ref_path))
        w.write(correct)
        w.close()
        pose_path = self._write_poses([pose], name="charge_pose.sdf")

        result = score_case("SYNTH", "diffdock", pose_path, ref_path)
        self.assertIsNone(result.error)
        self.assertIsNotNone(result.top1_rmsd)
        self.assertAlmostEqual(result.top1_rmsd, 0.5, places=2)
        self.assertEqual(result.n_poses_charge_artifact_fixed, 1)

    def test_success_rate_aggregation(self):
        results = [
            CaseResult("A", "gnina", 1, [1.0], [True], 1.0, 1.0, True, True, True),
            CaseResult("B", "gnina", 1, [3.0], [True], 3.0, 3.0, True, False, False),
        ]
        self.assertAlmostEqual(success_rate(results, "success_at_1"), 50.0)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from rdkit import Chem
from rdkit.Geometry import Point3D

from decisionbench_dd_docking.pose_validity import check_pose_validity

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REAL_LIGAND_SDF = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "gcase_validation" / "reference_ligands" / "3GXF_IFM.sdf"


class TestPoseValidity(unittest.TestCase):
    def setUp(self):
        self.mol = Chem.SDMolSupplier(str(REAL_LIGAND_SDF))[0]

    def test_real_reference_ligand_is_valid(self):
        result = check_pose_validity(self.mol)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.bad_bonds, [])
        self.assertEqual(result.clashing_pairs, [])

    def test_collapsed_conformer_flagged_as_clashing(self):
        mol = Chem.Mol(self.mol)
        conf = mol.GetConformer()
        # Collapse every atom onto the first atom's position -- pathological
        # but exactly what a broken docking output could look like.
        p0 = conf.GetAtomPosition(0)
        for i in range(mol.GetNumAtoms()):
            conf.SetAtomPosition(i, Point3D(p0.x, p0.y, p0.z))
        result = check_pose_validity(mol)
        self.assertFalse(result.is_valid)
        self.assertFalse(result.no_severe_internal_clash)
        self.assertGreater(len(result.clashing_pairs), 0)

    def test_stretched_bond_flagged(self):
        mol = Chem.Mol(self.mol)
        conf = mol.GetConformer()
        bond = mol.GetBondWithIdx(0)
        j = bond.GetEndAtomIdx()
        far = Point3D(conf.GetAtomPosition(j).x + 20.0, conf.GetAtomPosition(j).y, conf.GetAtomPosition(j).z)
        conf.SetAtomPosition(j, far)
        result = check_pose_validity(mol)
        self.assertFalse(result.is_valid)
        self.assertFalse(result.bond_lengths_ok)
        self.assertGreater(len(result.bad_bonds), 0)

    def test_no_receptor_given_skips_protein_clash_check(self):
        result = check_pose_validity(self.mol)
        self.assertIsNone(result.no_severe_protein_clash)
        self.assertTrue(result.is_valid)  # absence of a receptor must not fail validity

    def test_pose_inside_receptor_atom_flagged_as_protein_clash(self):
        receptor_path = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "gcase_validation" / "receptors_prepared" / "3GXF_prepared.pdb"
        mol = Chem.Mol(self.mol)
        conf = mol.GetConformer()

        from Bio.PDB import PDBParser
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure("r", str(receptor_path))
        first_atom_coord = next(a for a in structure.get_atoms() if a.element != "H").coord

        # Move every ligand atom on top of a real receptor atom -- an
        # unambiguous, severe protein-ligand clash.
        for i in range(mol.GetNumAtoms()):
            conf.SetAtomPosition(i, Point3D(*[float(x) for x in first_atom_coord]))

        result = check_pose_validity(mol, receptor_path=receptor_path)
        self.assertFalse(result.is_valid)
        self.assertFalse(result.no_severe_protein_clash)
        self.assertGreater(len(result.protein_clashes), 0)

    def test_real_reference_ligand_has_no_protein_clash_against_its_own_receptor(self):
        receptor_path = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "gcase_validation" / "receptors_prepared" / "3GXF_prepared.pdb"
        result = check_pose_validity(self.mol, receptor_path=receptor_path)
        self.assertTrue(result.no_severe_protein_clash)
        self.assertTrue(result.is_valid)


if __name__ == "__main__":
    unittest.main()

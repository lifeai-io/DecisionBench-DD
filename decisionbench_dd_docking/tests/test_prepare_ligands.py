import unittest

from rdkit import Chem

from decisionbench_dd_docking.prepare_ligands import pick_variant


class TestPickVariant(unittest.TestCase):
    def test_excludes_charged_sulfonamide_nitrogen_variants(self):
        # v1.2 regression: a tertiary sulfonamide N variant must not be
        # chosen even if it ties/wins on GOOD_AMMONIUM count.
        variants = [
            "CN(C[C@@H]([NH3+])c1ccccc1)S(=O)(=O)c1cc(F)cc(F)c1",  # correct: net +1
            "C[N+](C[C@@H]([NH3+])c1ccccc1)S(=O)(=O)c1cc(F)cc(F)c1",  # bad: net +2
        ]
        chosen, flag = pick_variant(variants)
        self.assertEqual(flag, "ok")
        self.assertEqual(Chem.GetFormalCharge(Chem.MolFromSmiles(chosen)), 1)

    def test_tie_break_prefers_lowest_net_charge_not_alphabetical(self):
        # v1.3 regression: among variants tied on GOOD_AMMONIUM count, the
        # one with fewer additional charged sites (here: a neutral vs.
        # triple-protonated tetrazole ring) must win, not whichever SMILES
        # string sorts first alphabetically.
        base = "Nc1c(Br)cc(Br)cc1C[NH2+]C1CCC(OC2CCCCC2)CC1n1cnnn1"  # net +1, 2 good sites, neutral tetrazole
        overprotonated = "Nc1c(Br)cc(Br)cc1C[NH2+]C1CCC(OC2CCCCC2)CC1n1c[nH+][nH+][nH+]1"  # net +4, same 2 good sites + 3 extra
        self.assertLess(overprotonated, base)  # confirms alphabetical order would have picked the bad one
        chosen, flag = pick_variant([base, overprotonated])
        self.assertEqual(flag, "ok")
        self.assertEqual(chosen, base)
        self.assertEqual(Chem.GetFormalCharge(Chem.MolFromSmiles(chosen)), 1)

    def test_no_valid_variant_returns_none(self):
        chosen, flag = pick_variant(["not a smiles at all"])
        self.assertIsNone(chosen)
        self.assertEqual(flag, "no_valid_variant")

    def test_falls_back_when_all_variants_have_bad_sulfonamide_charge(self):
        variants = ["C[N+](C)(C)S(=O)(=O)c1ccccc1"]  # only variant, has the bad charge
        chosen, flag = pick_variant(variants)
        self.assertEqual(chosen, variants[0])
        self.assertEqual(flag, "all_variants_had_bad_sulfonamide_charge_fallback_used")


if __name__ == "__main__":
    unittest.main()

import unittest

from rdkit import Chem

from decisionbench_dd_eval import chem_metrics

SEED_CANONICAL = "Nc1c(Br)cc(Br)cc1CNC1CCC(O)CC1"


class TestCanonicalize(unittest.TestCase):
    def test_valid_smiles(self):
        self.assertEqual(chem_metrics.canonicalize("c1ccccc1"), "c1ccccc1")

    def test_invalid_smiles(self):
        self.assertIsNone(chem_metrics.canonicalize("C1CC(N)("))

    def test_empty_string(self):
        self.assertIsNone(chem_metrics.canonicalize(""))


class TestScoreMolecule(unittest.TestCase):
    def setUp(self):
        self.seed_mol = Chem.MolFromSmiles(SEED_CANONICAL)
        self.seed_fp = chem_metrics.morgan_fingerprint(SEED_CANONICAL)
        self.seed_scaffold = chem_metrics.seed_scaffold_smiles(SEED_CANONICAL)
        self.seed_brenk_instances = chem_metrics.compute_seed_brenk_instances(self.seed_mol)

    def _score(self, smiles):
        return chem_metrics.score_molecule(
            tool="genmol",
            run_id="replicate_01",
            raw_smiles=smiles,
            api_score=0.5,
            seed_canonical_smiles=SEED_CANONICAL,
            seed_mol=self.seed_mol,
            seed_fingerprint=self.seed_fp,
            seed_scaffold_smiles=self.seed_scaffold,
            seed_brenk_instances=self.seed_brenk_instances,
        )

    def test_invalid_molecule_marked_invalid_and_no_metrics(self):
        rec = self._score("C1CC(N)(")
        self.assertFalse(rec.valid)
        self.assertIsNone(rec.canonical_smiles)
        self.assertIsNone(rec.qed)

    def test_exact_seed_copy(self):
        rec = self._score("C1=C(C(=C(C=C1Br)Br)N)CNC2CCC(CC2)O")
        self.assertTrue(rec.valid)
        self.assertTrue(rec.exact_seed_match)
        self.assertAlmostEqual(rec.tanimoto_to_seed, 1.0)
        self.assertTrue(rec.scaffold_matches_seed)
        # the seed's own aniline is fully seed-inherited: it exists in
        # brenk_alerts_all, but must not count as "new" against the seed itself.
        self.assertIn("aniline", rec.brenk_alerts_all)
        self.assertEqual(rec.brenk_alerts_new, [])
        self.assertTrue(rec.passes_seed_relative_alert_gate)

    def test_close_analogue_inherits_seed_alert_without_penalty(self):
        rec = self._score("C1=C(C(=C(C=C1Cl)Br)N)CNC2CCC(CC2)O")
        self.assertTrue(rec.valid)
        self.assertIn("aniline", rec.brenk_alerts_seed_inherent)
        self.assertEqual(rec.brenk_alerts_new, [], "Br->Cl substitution should not introduce a new alert")
        self.assertTrue(rec.passes_seed_relative_alert_gate)

    def test_pains_alert_is_absolute_and_independent_of_brenk(self):
        rec = self._score("O=C1CSC(=S)N1")  # rhodanine: triggers PAINS AND a separate Brenk alert
        self.assertTrue(rec.valid)
        self.assertGreater(len(rec.pains_alerts), 0)
        self.assertFalse(rec.passes_pains_gate)
        # The Brenk alert it also triggers ("Thiocarbonyl_group") is unrelated to
        # the seed and evaluated independently of the PAINS gate.
        seed_types = {i.alert_type for i in self.seed_brenk_instances}
        self.assertNotIn("Thiocarbonyl_group", seed_types)
        self.assertIn("Thiocarbonyl_group", rec.brenk_alerts_new)
        self.assertFalse(rec.passes_seed_relative_alert_gate)

    def test_new_brenk_alert_alongside_retained_seed_motif_fails_seed_relative_gate(self):
        # Keeps the seed's own aniline instance intact but bolts on an aldehyde
        # elsewhere -- a genuinely new alert type, trivially unmapped to any seed
        # instance.
        rec = self._score("Nc1c(Br)cc(Br)cc1CNC1CCC(OCC=O)CC1")
        self.assertTrue(rec.valid)
        self.assertIn("aniline", rec.brenk_alerts_seed_inherent)
        self.assertIn("aldehyde", rec.brenk_alerts_new)
        self.assertEqual(rec.n_seed_inherited_alert_instances, 1)
        self.assertEqual(rec.n_new_alert_instances, 1)
        self.assertFalse(rec.passes_seed_relative_alert_gate)

    def test_second_independent_instance_of_allowlisted_type_is_flagged_as_new(self):
        # The exact case v1.1's plain type-level set difference missed: the seed's
        # own aniline is retained at its own position, AND a second, chemically
        # distinct aniline is introduced elsewhere. Both are alert type "aniline",
        # but only one maps atom-for-atom onto the seed's instance.
        rec = self._score("Nc1c(Br)cc(Br)cc1CNC1CCC(NC(=O)c2ccc(N)cc2)CC1")
        self.assertTrue(rec.valid)
        self.assertEqual(rec.brenk_alerts_all, ["aniline"])  # same type both times
        self.assertIn("aniline", rec.brenk_alerts_seed_inherent)
        self.assertIn("aniline", rec.brenk_alerts_new)  # the type appears in both: one instance each
        self.assertEqual(rec.n_seed_inherited_alert_instances, 1)
        self.assertEqual(rec.n_new_alert_instances, 1)
        self.assertFalse(rec.passes_seed_relative_alert_gate)

    def test_two_anilines_at_least_one_unmapped_even_on_an_unrelated_scaffold(self):
        # Benzidine has two chemically distinct anilines and no real relationship
        # to Ambroxol. It still must not fully pass: at most one of its two
        # aniline instances can coincide with the seed's single mapped instance
        # (MCS aligns benzidine's aniline-bearing ring with the seed's own),
        # so at least one is necessarily unmapped/new -- demonstrating the gate
        # cannot be satisfied by an arbitrary aniline count that merely matches
        # the seed's, only by positional correspondence.
        rec = self._score("Nc1ccccc1-c1ccc(N)cc1")  # benzidine
        self.assertTrue(rec.valid)
        self.assertEqual(rec.n_seed_inherited_alert_instances + rec.n_new_alert_instances, 2)
        self.assertGreaterEqual(rec.n_new_alert_instances, 1)
        self.assertFalse(rec.passes_seed_relative_alert_gate)

    def test_unrelated_molecule_low_similarity(self):
        rec = self._score("CC(C)Cc1ccc(cc1)C(C)C(=O)O")  # ibuprofen
        self.assertTrue(rec.valid)
        self.assertFalse(rec.exact_seed_match)
        self.assertLess(rec.tanimoto_to_seed, 0.3)
        self.assertFalse(rec.scaffold_matches_seed)

    def test_qed_and_sa_in_documented_ranges(self):
        rec = self._score("CC(C)Cc1ccc(cc1)C(C)C(=O)O")
        self.assertGreaterEqual(rec.qed, 0.0)
        self.assertLessEqual(rec.qed, 1.0)
        self.assertGreaterEqual(rec.sa_score, 1.0)
        self.assertLessEqual(rec.sa_score, 10.0)


class TestInternalDiversity(unittest.TestCase):
    def test_identical_molecules_have_zero_diversity(self):
        smis = ["c1ccccc1", "c1ccccc1"]
        self.assertAlmostEqual(chem_metrics.internal_diversity(smis), 0.0)

    def test_single_molecule_returns_none(self):
        self.assertIsNone(chem_metrics.internal_diversity(["c1ccccc1"]))

    def test_dissimilar_molecules_have_positive_diversity(self):
        smis = ["c1ccccc1", "CCCCCCCCCCCCCCCCCCCC"]
        div = chem_metrics.internal_diversity(smis)
        self.assertGreater(div, 0.5)


if __name__ == "__main__":
    unittest.main()

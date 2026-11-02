import unittest

from rdkit import Chem

from decisionbench_dd_eval import chem_metrics, gates


class TestGateSpec(unittest.TestCase):
    def setUp(self):
        self.spec = gates.load_gate_spec()
        self.seed_canonical = "Nc1c(Br)cc(Br)cc1CNC1CCC(O)CC1"
        self.seed_mol = Chem.MolFromSmiles(self.seed_canonical)
        self.seed_fp = chem_metrics.morgan_fingerprint(self.seed_canonical)
        self.seed_scaffold = chem_metrics.seed_scaffold_smiles(self.seed_canonical)
        self.seed_brenk_instances = chem_metrics.compute_seed_brenk_instances(self.seed_mol)

    def _score(self, smiles):
        return chem_metrics.score_molecule(
            tool="genmol",
            run_id="replicate_01",
            raw_smiles=smiles,
            api_score=0.5,
            seed_canonical_smiles=self.seed_canonical,
            seed_mol=self.seed_mol,
            seed_fingerprint=self.seed_fp,
            seed_scaffold_smiles=self.seed_scaffold,
            seed_brenk_instances=self.seed_brenk_instances,
        )

    def test_invalid_fails_every_gate(self):
        rec = self._score("C1CC(N)(")
        result = gates.evaluate_gates(rec, self.spec)
        self.assertFalse(any(result.values()))
        self.assertFalse(gates.fully_qualified(result, self.spec["gate_order"]))

    def test_exact_seed_copy_fails_not_exact_seed_copy_gate(self):
        rec = self._score("C1=C(C(=C(C=C1Br)Br)N)CNC2CCC(CC2)O")
        result = gates.evaluate_gates(rec, self.spec)
        self.assertFalse(result["not_exact_seed_copy"])
        self.assertFalse(result["not_seed_copy"])  # tanimoto 1.0 also fails the <0.95 band
        self.assertTrue(result["ambroxol_related"])
        # the seed's own aniline must not block the seed-relative alert gate
        self.assertTrue(result["no_new_unmapped_structural_alert_instances"])

    def test_unrelated_molecule_fails_ambroxol_related_gate(self):
        rec = self._score("CC(C)Cc1ccc(cc1)C(C)C(=O)O")
        result = gates.evaluate_gates(rec, self.spec)
        self.assertFalse(result["ambroxol_related"])
        self.assertTrue(result["not_seed_copy"])
        self.assertTrue(result["not_exact_seed_copy"])

    def test_pains_hit_fails_pains_gate_regardless_of_seed(self):
        rec = self._score("O=C1CSC(=S)N1")  # rhodanine
        result = gates.evaluate_gates(rec, self.spec)
        self.assertFalse(result["pains"])

    def test_within_run_duplicate_fails_unique_gate(self):
        rec1 = self._score("CC(C)Cc1ccc(cc1)C(C)C(=O)O")
        rec1.is_first_occurrence_in_run = True
        rec2 = self._score("CC(C)Cc1ccc(cc1)C(C)C(=O)O")
        rec2.is_first_occurrence_in_run = False
        self.assertTrue(gates.evaluate_gates(rec1, self.spec)["unique"])
        self.assertFalse(gates.evaluate_gates(rec2, self.spec)["unique"])

    def test_funnel_counts_are_monotonically_non_increasing(self):
        smis = [
            "C1=C(C(=C(C=C1Br)Br)N)CNC2CCC(CC2)O",
            "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
            "C1CC(N)(",
        ]
        seen = set()
        records_with_gates = []
        for s in smis:
            rec = self._score(s)
            if rec.valid and rec.canonical_smiles not in seen:
                rec.is_first_occurrence_in_run = True
                seen.add(rec.canonical_smiles)
            records_with_gates.append((rec, gates.evaluate_gates(rec, self.spec)))
        funnel = gates.funnel_counts(records_with_gates, self.spec, requested_molecules=100)
        counts = [stage["count"] for stage in funnel]
        self.assertEqual(counts[0], 100)  # requested
        for a, b in zip(counts, counts[1:]):
            self.assertGreaterEqual(a, b)


if __name__ == "__main__":
    unittest.main()

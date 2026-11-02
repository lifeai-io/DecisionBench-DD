import csv
import unittest
from pathlib import Path

from decisionbench_dd_docking.triage_primary_candidates import (
    CANDIDATE_MANIFEST,
    MOLECULE_LEVEL,
    cluster_by_ecfp4,
    load_passing_candidates,
    rank_key,
)

REQUIRED_FILES = [CANDIDATE_MANIFEST, MOLECULE_LEVEL]


@unittest.skipUnless(all(p.is_file() for p in REQUIRED_FILES), "real candidate-screen/generator results not present")
class TestTriagePrimaryCandidates(unittest.TestCase):
    def test_loads_exactly_the_16_frozen_primary_passers(self):
        rows = load_passing_candidates()
        self.assertEqual(len(rows), 16)
        ids = {r["candidate_id"] for r in rows}
        # Frozen primary set, confirmed in prior sessions -- 15 GenMol + 1 MolMIM.
        self.assertIn("MM_002", ids)
        self.assertEqual(sum(1 for r in rows if r["tool"] == "genmol"), 15)
        self.assertEqual(sum(1 for r in rows if r["tool"] == "molmim"), 1)

    def test_every_row_has_physicochemical_properties_joined(self):
        rows = load_passing_candidates()
        for r in rows:
            self.assertIsNotNone(r["qed"], r["candidate_id"])
            self.assertIsNotNone(r["murcko_scaffold_smiles"], r["candidate_id"])

    def test_ligand_efficiency_proxy_is_affinity_over_heavy_atoms(self):
        rows = load_passing_candidates()
        for r in rows:
            expected = round(r["cnnaffinity_3keh"] / r["n_heavy_atoms"], 4)
            self.assertAlmostEqual(r["ligand_efficiency_proxy"], expected, places=4)

    def test_rank_key_orders_by_cnnaffinity_descending_primarily(self):
        rows = load_passing_candidates()
        ranked = sorted(rows, key=rank_key)
        affinities = [r["cnnaffinity_3keh"] for r in ranked]
        self.assertEqual(affinities, sorted(affinities, reverse=True))

    def test_cluster_assignment_is_reflexive_and_covers_all_candidates(self):
        rows = load_passing_candidates()
        clusters = cluster_by_ecfp4(rows)
        self.assertEqual(set(clusters.keys()), {r["candidate_id"] for r in rows})
        # A molecule's own fingerprint is identical to itself (Tanimoto=1.0
        # >= any threshold <=1), so every candidate must land in *some*
        # cluster -- no candidate can be unclustered.
        self.assertTrue(all(isinstance(v, int) for v in clusters.values()))


if __name__ == "__main__":
    unittest.main()

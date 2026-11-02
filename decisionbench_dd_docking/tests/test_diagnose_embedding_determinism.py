import unittest

from decisionbench_dd_docking.diagnose_embedding_determinism import call_path_facts, max_delta


class TestCallPathFacts(unittest.TestCase):
    def test_numthreads_is_default_one_and_not_applicable_to_embedmolecule(self):
        facts = call_path_facts()
        self.assertEqual(facts["numThreads_default_ETKDGv3"], 1)
        self.assertIn("EmbedMolecule", facts["embedding_function"])
        self.assertNotIn("EmbedMultipleConfs", facts["embedding_function"].split("(")[0])

    def test_randomseed_is_the_only_overridden_default(self):
        facts = call_path_facts()
        self.assertEqual(facts["overridden_from_ETKDGv3_defaults"], ["randomSeed"])
        self.assertEqual(facts["randomSeed_set_explicitly_to"], 42)


class TestMaxDelta(unittest.TestCase):
    def test_identical_coords_give_zero_delta(self):
        a = [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]
        self.assertEqual(max_delta(a, list(a)), 0.0)

    def test_mismatched_atom_counts_return_none(self):
        a = [(0.0, 0.0, 0.0)]
        b = [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]
        self.assertIsNone(max_delta(a, b))

    def test_known_offset_gives_expected_delta(self):
        a = [(0.0, 0.0, 0.0)]
        b = [(3.0, 4.0, 0.0)]
        self.assertAlmostEqual(max_delta(a, b), 5.0)


if __name__ == "__main__":
    unittest.main()

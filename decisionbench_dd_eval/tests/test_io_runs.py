import json
import unittest

from decisionbench_dd_eval.io_runs import ManifestError, _parse_genmol_raw, _parse_molmim_raw


class TestParseGenmolRaw(unittest.TestCase):
    def test_real_hosted_api_shape(self):
        # Verified directly against a live call to
        # health.api.nvidia.com/v1/biology/nvidia/genmol/generate
        raw = {
            "status": "success",
            "molecules": [
                {"smiles": "COC1CC(NCc2cc(Br)cc(Br)c2N)(OC)CC(c2ccccc2)C1O", "score": 0.399},
                {"smiles": "CCC1CC(O)(NCc2cc(Br)cc(Br)c2N)CC(N2CCCC2)C1O", "score": 0.376},
            ],
        }
        molecules = _parse_genmol_raw(raw, manifest_path="dummy")
        self.assertEqual(len(molecules), 2)
        self.assertEqual(molecules[0].raw_smiles, "COC1CC(NCc2cc(Br)cc(Br)c2N)(OC)CC(c2ccccc2)C1O")
        self.assertAlmostEqual(molecules[0].api_score, 0.399)

    def test_missing_molecules_key_raises(self):
        with self.assertRaises(ManifestError):
            _parse_genmol_raw({"status": "success"}, manifest_path="dummy")


class TestParseMolmimRaw(unittest.TestCase):
    def test_real_hosted_api_shape_double_encoded_string(self):
        # Verified directly against a live call to
        # health.api.nvidia.com/v1/biology/nvidia/molmim/generate: unlike GenMol,
        # `molecules` is a STRING containing a JSON array, not the array itself.
        inner = [
            {"sample": "NC1=C(C(=O)Cc2cc(Br)ccc2F)CCCC1", "score": 0.9282578760067838},
            {"sample": "O=C(NCc1cc(Br)ccc1Br)C1=CCCCC1", "score": 0.8400517769809146},
        ]
        raw = {"molecules": json.dumps(inner), "score_type": "QED"}
        molecules = _parse_molmim_raw(raw, manifest_path="dummy")
        self.assertEqual(len(molecules), 2)
        self.assertEqual(molecules[0].raw_smiles, "NC1=C(C(=O)Cc2cc(Br)ccc2F)CCCC1")
        self.assertAlmostEqual(molecules[0].api_score, 0.9282578760067838)

    def test_tolerates_already_decoded_list(self):
        inner = [{"sample": "c1ccccc1", "score": 0.5}]
        raw = {"molecules": inner, "score_type": "QED"}
        molecules = _parse_molmim_raw(raw, manifest_path="dummy")
        self.assertEqual(len(molecules), 1)
        self.assertEqual(molecules[0].raw_smiles, "c1ccccc1")

    def test_missing_molecules_key_raises(self):
        with self.assertRaises(ManifestError):
            _parse_molmim_raw({"score_type": "QED"}, manifest_path="dummy")

    def test_invalid_json_string_raises(self):
        with self.assertRaises(ManifestError):
            _parse_molmim_raw({"molecules": "not json"}, manifest_path="dummy")


if __name__ == "__main__":
    unittest.main()

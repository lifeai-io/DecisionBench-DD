import csv
import json
import tempfile
import unittest
from pathlib import Path

from rdkit import Chem
from rdkit.Geometry import Point3D

from decisionbench_dd_docking.score_candidate_screen import (
    CandidateResult,
    PoseScore,
    _load_catalytic_oxygen_coords,
    exact_binomial_ci,
    main,
    structural_proxy_pass,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCREEN_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "candidate_screen_v1.0"
RECEPTOR_3KEH = SCREEN_DIR / "receptors_prepared" / "3KEH_prepared.pdb"

# Real coordinates read from the prepared receptor (E235/E340 side-chain
# carboxylate oxygens) -- see this module's construction for how they were
# obtained.
E235_OE1 = (41.907, 105.190, -3.924)
E340_OE1 = (38.692, 100.652, -3.477)
# Midpoint between the two catalytic oxygens: 2.79 A from each (within the
# 4.5 A occupancy threshold) but not coincident with any actual receptor
# atom, so it doesn't also trip the protein-clash geometry-validity check.
POCKET_CENTER = ((E235_OE1[0] + E340_OE1[0]) / 2, (E235_OE1[1] + E340_OE1[1]) / 2, (E235_OE1[2] + E340_OE1[2]) / 2)
FAR_AWAY = (0.0, 0.0, 0.0)


def _make_pose(center):
    """A single carbon "ligand" placed at `center`. Deliberately not a
    multi-atom molecule: the real 3KEH active site is a tightly packed
    pocket (nearest receptor heavy atom to the pocket center is only 1.93 A
    away), so a normal small-molecule conformer anchored there almost always
    swings a second/third atom within the 1.5 A protein-clash cutoff purely
    from bond geometry, unrelated to whatever this test is actually trying
    to isolate (occupancy vs. validity vs. affinity). A single atom sidesteps
    that and keeps each test focused on one condition."""
    mol = Chem.RWMol()
    mol.AddAtom(Chem.Atom("C"))
    conf = Chem.Conformer(1)
    conf.SetAtomPosition(0, Point3D(*center))
    mol.AddConformer(conf)
    result = mol.GetMol()
    Chem.SanitizeMol(result)
    return result


class TestActiveSiteOccupancy(unittest.TestCase):
    def test_real_receptor_has_expected_catalytic_oxygens(self):
        coords = _load_catalytic_oxygen_coords(RECEPTOR_3KEH)
        self.assertEqual(coords.shape, (4, 3))  # OE1+OE2 for each of E235, E340


class TestStructuralProxyPass(unittest.TestCase):
    def _good_pose(self, cnnaffinity=5.0):
        return PoseScore(rank=1, cnnscore=0.9, cnnaffinity=cnnaffinity, cnn_vs=None,
                          minimized_affinity=-6.0, valid=True, active_site_occupied=True)

    def test_passes_when_all_conditions_met(self):
        result = CandidateResult("X", "3KEH", "genmol", 5, self._good_pose(5.0), True)
        self.assertTrue(structural_proxy_pass(result, ambroxol_cnnaffinity_3keh=4.0))

    def test_fails_on_wrong_receptor_state(self):
        result = CandidateResult("X", "3KE0", "genmol", 5, self._good_pose(5.0), True)
        self.assertFalse(structural_proxy_pass(result, ambroxol_cnnaffinity_3keh=4.0))

    def test_fails_when_not_all_five_poses_returned(self):
        result = CandidateResult("X", "3KEH", "genmol", 3, self._good_pose(5.0), False)
        self.assertFalse(structural_proxy_pass(result, ambroxol_cnnaffinity_3keh=4.0))

    def test_fails_when_top1_invalid_geometry(self):
        pose = self._good_pose(5.0)
        pose.valid = False
        result = CandidateResult("X", "3KEH", "genmol", 5, pose, True)
        self.assertFalse(structural_proxy_pass(result, ambroxol_cnnaffinity_3keh=4.0))

    def test_fails_when_not_active_site_occupied(self):
        pose = self._good_pose(5.0)
        pose.active_site_occupied = False
        result = CandidateResult("X", "3KEH", "genmol", 5, pose, True)
        self.assertFalse(structural_proxy_pass(result, ambroxol_cnnaffinity_3keh=4.0))

    def test_fails_when_cnnaffinity_below_ambroxol(self):
        result = CandidateResult("X", "3KEH", "genmol", 5, self._good_pose(3.0), True)
        self.assertFalse(structural_proxy_pass(result, ambroxol_cnnaffinity_3keh=4.0))

    def test_fails_on_error(self):
        result = CandidateResult("X", "3KEH", "genmol", 0, None, False, error="missing pose file")
        self.assertFalse(structural_proxy_pass(result, ambroxol_cnnaffinity_3keh=4.0))


class TestExactBinomialCI(unittest.TestCase):
    def test_zero_successes_lower_bound_is_zero(self):
        low, high = exact_binomial_ci(0, 66)
        self.assertEqual(low, 0.0)
        self.assertGreater(high, 0.0)

    def test_ci_widens_with_smaller_n(self):
        _, high_small_n = exact_binomial_ci(1, 3)
        _, high_large_n = exact_binomial_ci(22, 66)  # same proportion, larger n
        self.assertGreater(high_small_n, high_large_n)


class TestScoreCandidateScreenIntegration(unittest.TestCase):
    """Builds a minimal synthetic candidate_manifest.csv / microstate
    manifest / pose SDFs (real Ambroxol + one GenMol + one MolMIM candidate)
    to exercise the full CLI without needing 146 real GNINA runs."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.tmp = Path(self.tmpdir.name)

        # Patch module-level paths to point at our synthetic fixtures.
        import decisionbench_dd_docking.score_candidate_screen as scs
        self._orig_candidate_manifest = scs.CANDIDATE_MANIFEST
        self._orig_microstate_manifest = scs.MICROSTATE_MANIFEST
        self._orig_screen_dir = scs.SCREEN_DIR
        self._scs = scs

        fake_screen_dir = self.tmp / "screen"
        (fake_screen_dir / "receptors_prepared").mkdir(parents=True)
        for state in ("3KEH", "3KE0"):
            (fake_screen_dir / "receptors_prepared" / f"{state}_prepared.pdb").write_bytes(RECEPTOR_3KEH.read_bytes())
        scs.SCREEN_DIR = fake_screen_dir
        scs.CANDIDATE_MANIFEST = fake_screen_dir / "candidate_manifest.csv"
        scs.MICROSTATE_MANIFEST = fake_screen_dir / "ligand_microstate_manifest.csv"

        with open(scs.CANDIDATE_MANIFEST, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["candidate_id", "tool", "canonical_smiles"])
            w.writeheader()
            w.writerow({"candidate_id": "GM_001", "tool": "genmol", "canonical_smiles": "CCCCC"})
            w.writerow({"candidate_id": "MM_001", "tool": "molmim", "canonical_smiles": "CCCCC"})

        ligand_ids = ["GM_001", "MM_001", "CTRL_AMBROXOL", "CTRL_IFM", "CTRL_P9V", "CTRL_P8Y"]
        with open(scs.MICROSTATE_MANIFEST, "w", newline="") as fh:
            fields = ["ligand_id", "receptor_state", "microstate_ambiguous", "embed_ok"]
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for lid in ligand_ids:
                for state in ("3KEH", "3KE0"):
                    w.writerow({"ligand_id": lid, "receptor_state": state, "microstate_ambiguous": "False", "embed_ok": "True"})

        self.runs_dir = self.tmp / "runs"

    def tearDown(self):
        self._scs.SCREEN_DIR = self._orig_screen_dir
        self._scs.CANDIDATE_MANIFEST = self._orig_candidate_manifest
        self._scs.MICROSTATE_MANIFEST = self._orig_microstate_manifest

    def _write_poses(self, ligand_id, state, cnnaffinity_values, occupied=True):
        out_dir = self.runs_dir / state
        out_dir.mkdir(parents=True, exist_ok=True)
        center = POCKET_CENTER if occupied else FAR_AWAY
        writer = Chem.SDWriter(str(out_dir / f"{ligand_id}_poses.sdf"))
        for i, aff in enumerate(cnnaffinity_values):
            mol = _make_pose(center if i == 0 else FAR_AWAY)
            mol.SetDoubleProp("CNNscore", 0.9 - i * 0.1)
            mol.SetDoubleProp("CNNaffinity", aff)
            mol.SetDoubleProp("minimizedAffinity", -5.0)
            writer.write(mol)
        writer.close()

    def test_ambroxol_passes_its_own_threshold_and_genmol_candidate_passes(self):
        # Ambroxol: CNNaffinity 5.0 at 3KEH, occupied, valid, 5 poses.
        self._write_poses("CTRL_AMBROXOL", "3KEH", [5.0, 4.0, 3.0, 2.0, 1.0], occupied=True)
        self._write_poses("CTRL_AMBROXOL", "3KE0", [3.0, 2.0, 1.0, 0.5, 0.1], occupied=True)  # positive delta -> pH informative
        # GenMol candidate: CNNaffinity 6.0 (>= Ambroxol's 5.0) -> should pass.
        self._write_poses("GM_001", "3KEH", [6.0, 5.5, 5.0, 4.5, 4.0], occupied=True)
        self._write_poses("GM_001", "3KE0", [4.0, 3.5, 3.0, 2.5, 2.0], occupied=True)
        # MolMIM candidate: CNNaffinity 4.0 (< Ambroxol's 5.0) -> should fail.
        self._write_poses("MM_001", "3KEH", [4.0, 3.9, 3.8, 3.7, 3.6], occupied=True)
        self._write_poses("MM_001", "3KE0", [3.0, 2.9, 2.8, 2.7, 2.6], occupied=True)
        for cid in ("CTRL_IFM", "CTRL_P9V", "CTRL_P8Y"):
            self._write_poses(cid, "3KEH", [5.0] * 5, occupied=True)
            self._write_poses(cid, "3KE0", [4.0] * 5, occupied=True)

        out_dir = self.tmp / "results"
        rc = main(["--runs-dir", str(self.runs_dir), "--out-dir", str(out_dir)])
        self.assertEqual(rc, 0)

        with open(out_dir / "candidate_results.csv") as fh:
            candidates = {r["candidate_id"]: r for r in csv.DictReader(fh)}
        self.assertEqual(candidates["GM_001"]["structural_proxy_pass"], "True")
        self.assertEqual(candidates["MM_001"]["structural_proxy_pass"], "False")

        summary = json.loads((out_dir / "summary.json").read_text())
        self.assertTrue(summary["ambroxol_directional_sanity_check_passed"])
        # All 4 controls and both interpretable candidates favor neutral here -> supported, not just exploratory.
        self.assertEqual(summary["ph_sensitivity_endpoint_status"], "directionally_supported")
        self.assertEqual(summary["generators"]["genmol"]["n_structural_proxy_pass"], 1)
        self.assertEqual(summary["generators"]["molmim"]["n_structural_proxy_pass"], 0)

    def test_candidate_not_occupying_active_site_fails_despite_good_affinity(self):
        self._write_poses("CTRL_AMBROXOL", "3KEH", [5.0] * 5, occupied=True)
        self._write_poses("CTRL_AMBROXOL", "3KE0", [4.0] * 5, occupied=True)
        self._write_poses("GM_001", "3KEH", [9.0, 8.0, 7.0, 6.0, 5.0], occupied=False)  # far from active site
        self._write_poses("GM_001", "3KE0", [4.0] * 5, occupied=True)
        self._write_poses("MM_001", "3KEH", [4.0] * 5, occupied=True)
        self._write_poses("MM_001", "3KE0", [4.0] * 5, occupied=True)
        for cid in ("CTRL_IFM", "CTRL_P9V", "CTRL_P8Y"):
            self._write_poses(cid, "3KEH", [5.0] * 5, occupied=True)
            self._write_poses(cid, "3KE0", [4.0] * 5, occupied=True)

        out_dir = self.tmp / "results"
        rc = main(["--runs-dir", str(self.runs_dir), "--out-dir", str(out_dir)])
        self.assertEqual(rc, 0)
        with open(out_dir / "candidate_results.csv") as fh:
            candidates = {r["candidate_id"]: r for r in csv.DictReader(fh)}
        self.assertEqual(candidates["GM_001"]["structural_proxy_pass"], "False")

    def test_ph_status_stays_exploratory_when_other_controls_disagree_with_ambroxol(self):
        # Regression for external-review feedback: Ambroxol alone passing its
        # own directional check must NOT be reported as validating the whole
        # pH-sensitivity endpoint when the other controls point the other way.
        self._write_poses("CTRL_AMBROXOL", "3KEH", [5.0] * 5, occupied=True)
        self._write_poses("CTRL_AMBROXOL", "3KE0", [4.0] * 5, occupied=True)  # Ambroxol: positive delta
        for cid in ("CTRL_IFM", "CTRL_P9V", "CTRL_P8Y"):
            self._write_poses(cid, "3KEH", [4.0] * 5, occupied=True)
            self._write_poses(cid, "3KE0", [5.0] * 5, occupied=True)  # all three: negative delta
        self._write_poses("GM_001", "3KEH", [6.0] * 5, occupied=True)
        self._write_poses("GM_001", "3KE0", [7.0] * 5, occupied=True)  # candidate also favors acidic
        self._write_poses("MM_001", "3KEH", [4.0] * 5, occupied=True)
        self._write_poses("MM_001", "3KE0", [5.0] * 5, occupied=True)

        out_dir = self.tmp / "results"
        rc = main(["--runs-dir", str(self.runs_dir), "--out-dir", str(out_dir)])
        self.assertEqual(rc, 0)

        summary = json.loads((out_dir / "summary.json").read_text())
        self.assertTrue(summary["ambroxol_directional_sanity_check_passed"])
        self.assertEqual(summary["ph_sensitivity_endpoint_status"], "exploratory_unvalidated")
        # Primary structural-proxy result must be entirely unaffected by pH status.
        with open(out_dir / "candidate_results.csv") as fh:
            candidates = {r["candidate_id"]: r for r in csv.DictReader(fh)}
        self.assertEqual(candidates["GM_001"]["structural_proxy_pass"], "True")


if __name__ == "__main__":
    unittest.main()

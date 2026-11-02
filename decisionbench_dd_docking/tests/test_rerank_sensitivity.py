import unittest
from pathlib import Path

from decisionbench_dd_docking.rerank_sensitivity import load_raw_pose_props, pick_index

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REAL_GNINA_POSES = REPO_ROOT / "docking_runs" / "gnina" / "3GXF_poses.sdf"


class TestPickIndex(unittest.TestCase):
    def setUp(self):
        self.poses = [
            {"cnnscore": 0.9, "cnn_vs": 0.1, "minimized_affinity": -3.0},
            {"cnnscore": 0.8, "cnn_vs": 0.5, "minimized_affinity": -7.0},
            {"cnnscore": 0.7, "cnn_vs": 0.3, "minimized_affinity": -5.0},
        ]

    def test_empty_pool_returns_none(self):
        self.assertIsNone(pick_index([], "native_rank1"))

    def test_native_rank1_always_picks_first(self):
        self.assertEqual(pick_index(self.poses, "native_rank1"), 0)

    def test_cnn_vs_desc_picks_highest(self):
        self.assertEqual(pick_index(self.poses, "cnn_vs_desc"), 1)

    def test_minimized_affinity_asc_picks_lowest(self):
        self.assertEqual(pick_index(self.poses, "minimized_affinity_asc"), 1)

    def test_cnn_vs_desc_returns_none_if_missing_anywhere(self):
        poses = [dict(p) for p in self.poses]
        poses[1]["cnn_vs"] = None
        self.assertIsNone(pick_index(poses, "cnn_vs_desc"))

    def test_unknown_selector_raises(self):
        with self.assertRaises(ValueError):
            pick_index(self.poses, "not_a_real_selector")


class TestLoadRawPoseProps(unittest.TestCase):
    def test_loads_real_gnina_poses_in_native_order(self):
        poses = load_raw_pose_props(REAL_GNINA_POSES)
        self.assertEqual(len(poses), 5)
        self.assertEqual([p["rank"] for p in poses], [1, 2, 3, 4, 5])
        # Real 3GXF log: CNNscore descending in native order (verified against
        # docking_runs/gnina/3GXF_gnina.log).
        scores = [p["cnnscore"] for p in poses]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(p["cnn_vs"] is not None for p in poses))


if __name__ == "__main__":
    unittest.main()

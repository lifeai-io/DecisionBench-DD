import stat
import tempfile
import unittest
from pathlib import Path

from decisionbench_dd_docking.docker_utils import (
    CONTAINER_OUT,
    CONTAINER_REPO,
    build_volume_args,
    container_path,
    ensure_container_writable_dir,
    out_dir_is_inside_repo,
)


class TestDockerUtils(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo_root = Path(self.tmp.name) / "repo"
        (self.repo_root / "decisionbench_dd_configs_v1.0" / "gcase_validation").mkdir(parents=True)
        (self.repo_root / "decisionbench_dd_configs_v1.0" / "gcase_validation" / "receptors_prepared").mkdir()

    def test_out_dir_inside_repo_uses_single_mount(self):
        out_dir = self.repo_root / "docking_runs"
        self.assertTrue(out_dir_is_inside_repo(self.repo_root, out_dir))
        volumes = build_volume_args(self.repo_root, out_dir)
        self.assertEqual(volumes, ["-v", f"{self.repo_root.resolve()}:{CONTAINER_REPO}"])

    def test_out_dir_outside_repo_adds_second_mount(self):
        out_dir = Path(self.tmp.name) / "elsewhere" / "docking_runs"
        self.assertFalse(out_dir_is_inside_repo(self.repo_root, out_dir))
        volumes = build_volume_args(self.repo_root, out_dir)
        self.assertIn("-v", volumes)
        self.assertIn(f"{self.repo_root.resolve()}:{CONTAINER_REPO}", volumes)
        self.assertIn(f"{out_dir.resolve()}:{CONTAINER_OUT}", volumes)

    def test_container_path_for_repo_file(self):
        out_dir = self.repo_root / "docking_runs"
        receptor = self.repo_root / "decisionbench_dd_configs_v1.0" / "gcase_validation" / "receptors_prepared" / "9F9Z_prepared.pdb"
        cpath = container_path(receptor, self.repo_root, out_dir)
        self.assertEqual(cpath, f"{CONTAINER_REPO}/decisionbench_dd_configs_v1.0/gcase_validation/receptors_prepared/9F9Z_prepared.pdb")

    def test_container_path_for_out_dir_file_when_out_dir_inside_repo(self):
        out_dir = self.repo_root / "docking_runs"
        out_sdf = out_dir / "gnina" / "9F9Z_poses.sdf"
        cpath = container_path(out_sdf, self.repo_root, out_dir)
        self.assertEqual(cpath, f"{CONTAINER_REPO}/docking_runs/gnina/9F9Z_poses.sdf")

    def test_container_path_for_out_dir_file_when_out_dir_outside_repo(self):
        out_dir = Path(self.tmp.name) / "elsewhere" / "docking_runs"
        out_sdf = out_dir / "gnina" / "9F9Z_poses.sdf"
        cpath = container_path(out_sdf, self.repo_root, out_dir)
        self.assertEqual(cpath, f"{CONTAINER_OUT}/gnina/9F9Z_poses.sdf")


class TestEnsureContainerWritableDir(unittest.TestCase):
    def test_creates_missing_dir_and_parents(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "a" / "b" / "c"
            ensure_container_writable_dir(target)
            self.assertTrue(target.is_dir())

    def test_sets_world_writable_and_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "restrictive"
            target.mkdir(mode=0o700)
            ensure_container_writable_dir(target)
            mode = target.stat().st_mode
            for bit in (stat.S_IRWXU, stat.S_IRWXG, stat.S_IRWXO):
                self.assertEqual(mode & bit, bit)

    def test_idempotent_on_already_writable_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "already_open"
            ensure_container_writable_dir(target)
            ensure_container_writable_dir(target)  # must not raise
            self.assertTrue(target.is_dir())


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from decisionbench_dd_docking.provenance import (
    build_manifest,
    resolve_docker_image_digest,
    resolve_git_commit,
    sha256_file,
    write_manifest,
)


class TestSha256File(unittest.TestCase):
    def test_known_content_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "f.txt"
            p.write_bytes(b"hello")
            self.assertEqual(
                sha256_file(p),
                "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
            )

    def test_different_content_gives_different_hash(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "a.txt"
            b = Path(d) / "b.txt"
            a.write_bytes(b"hello")
            b.write_bytes(b"world")
            self.assertNotEqual(sha256_file(a), sha256_file(b))


class TestResolveDockerImageDigestFallback(unittest.TestCase):
    def test_returns_none_when_docker_unavailable(self):
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            self.assertIsNone(resolve_docker_image_digest("some/image"))

    def test_falls_back_to_image_id_when_no_repo_digest(self):
        class FakeResult:
            def __init__(self, out):
                self.returncode = 0
                self.stdout = out

        calls = [FakeResult("<no value>"), FakeResult("sha256:localid123")]

        def fake_run(*a, **k):
            return calls.pop(0)

        with patch("subprocess.run", side_effect=fake_run):
            self.assertEqual(resolve_docker_image_digest("local/image"), "sha256:localid123")


class TestResolveGitCommit(unittest.TestCase):
    def test_returns_none_when_git_unavailable(self):
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            self.assertIsNone(resolve_git_commit(Path(".")))

    def test_returns_hash_for_this_repo(self):
        repo_root = Path(__file__).resolve().parent.parent.parent
        commit = resolve_git_commit(repo_root)
        self.assertIsNotNone(commit)
        self.assertEqual(len(commit), 40)


class TestBuildAndWriteManifest(unittest.TestCase):
    def test_manifest_contains_expected_top_level_keys(self):
        with tempfile.TemporaryDirectory() as d:
            f1 = Path(d) / "protocol.json"
            f1.write_text("{}")
            with patch("decisionbench_dd_docking.provenance.resolve_docker_image_digest", return_value="repo@sha256:abc"), \
                 patch("decisionbench_dd_docking.provenance.resolve_git_commit", return_value="deadbeef"):
                manifest = build_manifest(
                    tool="gnina",
                    docker_image="gnina/gnina:latest",
                    repo_root=Path(d),
                    input_files={"redocking_protocol": f1},
                    cases=[{"pdb_id": "3GXF", "success": True}],
                    run_started_at="2026-01-01T00:00:00+00:00",
                    run_finished_at="2026-01-01T00:01:00+00:00",
                    extra={"gpu": True},
                )
            self.assertEqual(manifest["tool"], "gnina")
            self.assertEqual(manifest["docker_image_digest"], "repo@sha256:abc")
            self.assertEqual(manifest["git_commit"], "deadbeef")
            self.assertIn("redocking_protocol", manifest["input_file_hashes_sha256"])
            self.assertEqual(manifest["cases"][0]["pdb_id"], "3GXF")
            self.assertTrue(manifest["gpu"])

    def test_write_manifest_round_trips_through_json(self):
        with tempfile.TemporaryDirectory() as d:
            out_path = Path(d) / "sub" / "manifest.json"
            manifest = {"tool": "diffdock", "cases": []}
            write_manifest(manifest, out_path)
            self.assertTrue(out_path.is_file())
            self.assertEqual(json.loads(out_path.read_text()), manifest)


if __name__ == "__main__":
    unittest.main()

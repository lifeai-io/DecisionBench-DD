"""Run-provenance manifests for dockerized docking runs
(decisionbench_dd_docking/run_gnina.py, run_diffdock.py).

Written to <out-dir>/<tool>/manifest.json after each run so a results
directory is self-describing: which Docker image (tag + resolved content
digest, not just the mutable tag name) actually produced these poses,
which protocol/case-list file content (by hash, not just path) it was run
against, and per-case wall-clock runtime/exit status. Added in response to
external review's valid point that docking_results/ had no record of what
generated it -- a re-run against a silently updated image or a locally
edited protocol file would otherwise be indistinguishable from this one.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_docker_image_digest(image: str) -> Optional[str]:
    """Best-effort immutable content digest for `image` (e.g.
    'repo@sha256:abcd...'). Falls back to the local image ID if the image
    has no registry RepoDigest (e.g. built locally, never pulled/pushed).
    Returns None rather than raising if docker/the image is unavailable --
    a provenance nicety must not fail the actual docking run."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{index .RepoDigests 0}}", image],
            capture_output=True, text=True, timeout=30,
        )
        out = result.stdout.strip()
        if result.returncode == 0 and out and out != "<no value>":
            return out
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.Id}}", image],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def resolve_git_commit(repo_root: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_manifest(
    tool: str,
    docker_image: str,
    repo_root: Path,
    input_files: dict[str, Path],
    cases: list[dict],
    run_started_at: str,
    run_finished_at: str,
    extra: Optional[dict] = None,
) -> dict:
    manifest = {
        "tool": tool,
        "docker_image": docker_image,
        "docker_image_digest": resolve_docker_image_digest(docker_image),
        "git_commit": resolve_git_commit(repo_root),
        "input_file_hashes_sha256": {name: sha256_file(path) for name, path in input_files.items()},
        "run_started_at_utc": run_started_at,
        "run_finished_at_utc": run_finished_at,
        "cases": cases,
    }
    if extra:
        manifest.update(extra)
    return manifest


def write_manifest(manifest: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

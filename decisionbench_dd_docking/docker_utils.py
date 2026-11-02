"""Shared helpers for invoking dockerized GNINA/DiffDock-L on the GPU
instance: computing bind mounts and translating host paths to their
in-container equivalents.

Design: the repo (all frozen inputs under decisionbench_dd_configs_v1.0/) is
always mounted at CONTAINER_REPO. The output directory is normally
REPO_ROOT/docking_runs, i.e. already inside that mount, so by default no
second mount is needed. If --out-dir points somewhere else entirely, a
second bind mount at CONTAINER_OUT is added automatically.
"""
from __future__ import annotations

import stat
from pathlib import Path

CONTAINER_REPO = "/workspace"
CONTAINER_OUT = "/out"


def out_dir_is_inside_repo(repo_root: Path, out_dir: Path) -> bool:
    try:
        out_dir.resolve().relative_to(repo_root.resolve())
        return True
    except ValueError:
        return False


def build_volume_args(repo_root: Path, out_dir: Path) -> list[str]:
    repo_root = repo_root.resolve()
    out_dir = out_dir.resolve()
    args = ["-v", f"{repo_root}:{CONTAINER_REPO}"]
    if not out_dir_is_inside_repo(repo_root, out_dir):
        args += ["-v", f"{out_dir}:{CONTAINER_OUT}"]
    return args


def container_path(host_path: Path, repo_root: Path, out_dir: Path) -> str:
    """Translate a host path (either under repo_root, or under out_dir when
    out_dir lives outside repo_root) to its in-container equivalent."""
    repo_root = repo_root.resolve()
    out_dir = out_dir.resolve()
    host_path = host_path.resolve()

    if out_dir_is_inside_repo(repo_root, out_dir):
        rel = host_path.relative_to(repo_root)
        return f"{CONTAINER_REPO}/{rel.as_posix()}"

    try:
        rel = host_path.relative_to(out_dir)
        return f"{CONTAINER_OUT}/{rel.as_posix()}"
    except ValueError:
        rel = host_path.relative_to(repo_root)
        return f"{CONTAINER_REPO}/{rel.as_posix()}"


def gpu_flags(use_gpu: bool) -> list[str]:
    return ["--gpus", "all"] if use_gpu else []


def ensure_container_writable_dir(path: Path) -> None:
    """Create `path` (and parents) and make it world-writable/-executable.

    Bind-mounted directories keep their host-side permission bits inside the
    container. GNINA/DiffDock's official images run as a non-root, fixed-UID
    user (rbgcsail/diffdock: appuser, uid 1000) that essentially never matches
    the host user who created the output directory, so a directory created
    with the host's normal umask (typically 755) denies that UID write
    access -- confirmed in practice: DiffDock's os.makedirs() on a fresh
    per-complex output directory raised PermissionError until this was added.
    0o777 is used rather than trying to guess/match the container's UID
    (via --user or otherwise), since that mapping isn't knowable in general
    and this fixes it regardless of which UID either side runs as.
    """
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(path.stat().st_mode | stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

#!/usr/bin/env python3
"""Runs the official `rbgcsail/diffdock` Docker image (DiffDock-L) over the
frozen 14-case GCase redocking set on the machine this is executed on (a GPU
instance -- DiffDock is not installed in the main dev environment for this
repo).

All facts about the image below were verified directly against the
gcorso/DiffDock repo (commit 85c49b60d3e0b0182a59ee43a34a6d7036981284) and
its Dockerfile, not assumed from the README prose alone -- the README's own
single-complex-mode description turned out to name the wrong flag
(`--ligand`, which doesn't exist; the real flag is `--ligand_description`).
Verified facts used here:
  - Image has no ENTRYPOINT, only a CMD, so `docker run ... rbgcsail/diffdock
    <anything>` fully overrides it.
  - WORKDIR is /home/appuser/DiffDock (baked into the image; persists across
    CMD overrides, so relative paths like `default_inference_args.yaml`
    resolve there without an explicit `cd`).
  - The conda/micromamba env is named "diffdock"; the Dockerfile itself uses
    `micromamba run -n diffdock <cmd>` for non-interactive execution (used in
    its own build step and default CMD), confirming that pattern works in
    this image.
  - Batch/CSV mode is the fully-documented, verified-example path (unlike
    single-complex mode, which is prose-only and was already wrong once):
    `python -m inference --config default_inference_args.yaml
    --protein_ligand_csv <csv> --out_dir <dir>`. This script builds one CSV
    for the whole (or --cases-subset) run rather than invoking the container
    once per case.
  - CSV columns (from data/protein_ligand_example.csv):
    complex_name,protein_path,ligand_description,protein_sequence --
    ligand_description accepts either a file path or a bare SMILES string.
  - Output layout: <out_dir>/<complex_name>/rank{N}_confidence{score}.sdf for
    every rank 1..samples_per_complex (sorted best-to-worst), PLUS a second,
    unsuffixed copy of the top pose only: <out_dir>/<complex_name>/rank1.sdf.
    Do not glob bare "rank*.sdf" -- it matches both rank1.sdf (the top-pose
    duplicate) and rank1_confidence*.sdf, double-counting rank 1. This script
    only reads the confidence-suffixed files, sorted by rank number.

Inputs per case (redocking_protocol_v1.0.json's task_definition / diffdock):
  - receptor: receptors_cropped_for_diffdock/<PDB_ID>_cropped.pdb (pocket-cropped,
              15 A radius around the docking-box center)
  - ligand:   the case's docking_input_protonated_smiles (SMILES string --
              DiffDock generates its own 3D pose, crystal coordinates are
              never supplied)

Output convention consumed by decisionbench_dd_docking.evaluate_docking:
  <out-dir>/diffdock/<PDB_ID>_poses.sdf   (multi-model SDF, rank order, top-1 first)

Usage:
    python -m decisionbench_dd_docking.run_diffdock --out-dir docking_runs/ --dry-run
    python -m decisionbench_dd_docking.run_diffdock --out-dir docking_runs/
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

from rdkit import Chem

from decisionbench_dd_docking.docker_utils import build_volume_args, container_path, ensure_container_writable_dir, gpu_flags
from decisionbench_dd_docking.provenance import build_manifest, utc_now_iso, write_manifest

REPO_ROOT = Path(__file__).resolve().parent.parent
GCASE_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "gcase_validation"
PROTOCOL_PATH = GCASE_DIR / "redocking_protocol_v1.0.json"
CASE_LIST_PATH = GCASE_DIR / "gcase_validation_set_v1.0.json"

CONDA_ENV_NAME = "diffdock"
RANK_CONFIDENCE_RE = re.compile(r"^rank(\d+)_confidence")


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--docker-image", default="rbgcsail/diffdock", help="DiffDock Docker image/tag (default: rbgcsail/diffdock)")
    p.add_argument("--out-dir", type=Path, default=REPO_ROOT / "docking_runs")
    p.add_argument("--no-gpu", action="store_true", help="Run without --gpus all")
    p.add_argument("--cases", nargs="*", default=None, help="Subset of PDB IDs to run (default: all 14)")
    p.add_argument("--samples-per-complex", type=int, default=None, help="Override protocol's num_samples")
    p.add_argument("--dry-run", action="store_true", help="Print the command without executing it")
    return p.parse_args(argv)


def build_batch_csv(cases: list[dict], csv_path: Path, repo_root: Path, out_dir: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["complex_name", "protein_path", "ligand_description", "protein_sequence"])
        for case in cases:
            receptor = GCASE_DIR / case["receptor_cropped_for_diffdock_file"]
            writer.writerow([
                case["pdb_id"],
                container_path(receptor, repo_root, out_dir),
                case["docking_input_protonated_smiles"],
                "",
            ])


def merge_ranked_sdfs(complex_out_dir: Path, n_samples: int, dest_sdf: Path) -> int:
    """Only rank{N}_confidence*.sdf files are read -- the extra unsuffixed
    rank1.sdf duplicate the container also writes for the top pose is
    intentionally skipped to avoid double-counting rank 1."""
    candidates = []
    for f in complex_out_dir.glob("rank*_confidence*.sdf"):
        m = RANK_CONFIDENCE_RE.match(f.name)
        if m:
            candidates.append((int(m.group(1)), f))
    candidates.sort(key=lambda pair: pair[0])

    if not candidates:
        return 0
    writer = Chem.SDWriter(str(dest_sdf))
    n_written = 0
    for _, f in candidates[:n_samples]:
        mol = Chem.SDMolSupplier(str(f))[0]
        if mol is None:
            continue
        writer.write(mol)
        n_written += 1
    writer.close()
    return n_written


def main(argv=None) -> int:
    args = parse_args(argv)

    if not args.dry_run and shutil.which("docker") is None:
        print("ERROR: 'docker' not found on PATH.", file=sys.stderr)
        return 1

    with open(PROTOCOL_PATH) as fh:
        protocol = json.load(fh)
    with open(CASE_LIST_PATH) as fh:
        case_list = json.load(fh)

    diffdock_cfg = protocol["diffdock"]
    n_samples = args.samples_per_complex or diffdock_cfg["num_samples"]

    out_diffdock_dir = args.out_dir / "diffdock"
    out_diffdock_dir.mkdir(parents=True, exist_ok=True)
    raw_out_dir = args.out_dir / "diffdock_raw"
    # World-writable: the container's non-root appuser (uid 1000) needs to
    # create per-complex subdirectories here via os.makedirs(); see
    # ensure_container_writable_dir's docstring for why plain mkdir() isn't enough.
    ensure_container_writable_dir(raw_out_dir)
    volumes = build_volume_args(REPO_ROOT, args.out_dir)

    cases = case_list["cases"]
    if args.cases:
        cases = [c for c in cases if c["pdb_id"] in args.cases]

    csv_path = args.out_dir / "diffdock_batch_input.csv"
    build_batch_csv(cases, csv_path, REPO_ROOT, args.out_dir)

    inference_cmd = (
        f"micromamba run -n {CONDA_ENV_NAME} python -m inference "
        f"--config default_inference_args.yaml "
        f"--protein_ligand_csv {container_path(csv_path, REPO_ROOT, args.out_dir)} "
        f"--out_dir {container_path(raw_out_dir, REPO_ROOT, args.out_dir)} "
        f"--samples_per_complex {n_samples}"
    )
    cmd = ["docker", "run", "--rm", *gpu_flags(not args.no_gpu), *volumes, args.docker_image, "sh", "-c", inference_cmd]

    print(f"[batch: {len(cases)} cases] {shlex.join(cmd)}")
    if args.dry_run:
        return 0

    run_started_at = utc_now_iso()
    start = time.monotonic()
    result = subprocess.run(cmd, capture_output=True, text=True)
    runtime = time.monotonic() - start
    if result.returncode != 0:
        print(f"FAILED (exit {result.returncode}, {runtime:.1f}s): {result.stderr[-4000:]}", file=sys.stderr)
        manifest = build_manifest(
            tool="diffdock",
            docker_image=args.docker_image,
            repo_root=REPO_ROOT,
            input_files={"redocking_protocol": PROTOCOL_PATH, "case_list": CASE_LIST_PATH},
            cases=[],
            run_started_at=run_started_at,
            run_finished_at=utc_now_iso(),
            extra={
                "gpu": not args.no_gpu,
                "batch_cmd": shlex.join(cmd),
                "batch_runtime_seconds": round(runtime, 2),
                "batch_returncode": result.returncode,
                "samples_per_complex": n_samples,
            },
        )
        write_manifest(manifest, out_diffdock_dir / "manifest.json")
        return 1
    print(f"Batch inference finished in {runtime:.1f}s. Merging per-case outputs...")

    failures = []
    case_manifests = []
    for case in cases:
        pdb_id = case["pdb_id"]
        complex_out_dir = raw_out_dir / pdb_id
        dest_sdf = out_diffdock_dir / f"{pdb_id}_poses.sdf"
        n_written = merge_ranked_sdfs(complex_out_dir, n_samples, dest_sdf)
        success = n_written > 0
        if not success:
            failures.append(pdb_id)
            print(f"  [{pdb_id}] FAILED: no rank*_confidence*.sdf found in {complex_out_dir}", file=sys.stderr)
        else:
            print(f"  [{pdb_id}] OK ({n_written} poses) -> {dest_sdf}")
        case_manifests.append({"pdb_id": pdb_id, "n_poses_written": n_written, "success": success})

    manifest = build_manifest(
        tool="diffdock",
        docker_image=args.docker_image,
        repo_root=REPO_ROOT,
        input_files={"redocking_protocol": PROTOCOL_PATH, "case_list": CASE_LIST_PATH},
        cases=case_manifests,
        run_started_at=run_started_at,
        run_finished_at=utc_now_iso(),
        extra={
            "gpu": not args.no_gpu,
            "batch_cmd": shlex.join(cmd),
            "batch_runtime_seconds": round(runtime, 2),
            "batch_returncode": result.returncode,
            "samples_per_complex": n_samples,
        },
    )
    write_manifest(manifest, out_diffdock_dir / "manifest.json")

    if failures:
        print(f"\n{len(failures)}/{len(cases)} cases failed to produce poses: {failures}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

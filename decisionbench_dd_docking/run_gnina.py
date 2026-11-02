#!/usr/bin/env python3
"""Runs dockerized GNINA over the frozen 14-case GCase redocking set on the
machine this is executed on (a GPU instance -- GNINA is not installed in the
main dev environment for this repo).

Invokes `docker run --gpus all <image> gnina ...`. Requires `docker` on PATH
and a pulled/built `gnina/gnina` image (or your own tag -- see --docker-image).

All docking parameters are read from the frozen protocol/case files, never
hardcoded here, so a parameter change always shows up as a diff to those
files (decisionbench_dd_configs_v1.0/gcase_validation/redocking_protocol_v1.0.json):
  - receptor: receptors_prepared/<PDB_ID>_prepared.pdb (PDB2PQR, pH 7.4)
  - ligand:   docking_input_ligands/<PDB_ID>_ligand_input.sdf (protonated at
              pH 7.4 via dimorphite-dl, 3D-embedded via RDKit ETKDGv3 --
              NOT the crystal pose)
  - box:      docking_boxes.json (6 A padding around the crystal ligand's
              heavy-atom extent)

Output convention consumed by decisionbench_dd_docking.evaluate_docking:
  <out-dir>/gnina/<PDB_ID>_poses.sdf   (multi-model SDF, rank order, top-1 first)

Usage:
    python -m decisionbench_dd_docking.run_gnina --out-dir docking_runs/ --dry-run
    python -m decisionbench_dd_docking.run_gnina --out-dir docking_runs/
"""
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

from decisionbench_dd_docking.docker_utils import build_volume_args, container_path, ensure_container_writable_dir, gpu_flags
from decisionbench_dd_docking.provenance import build_manifest, utc_now_iso, write_manifest

REPO_ROOT = Path(__file__).resolve().parent.parent
GCASE_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "gcase_validation"
PROTOCOL_PATH = GCASE_DIR / "redocking_protocol_v1.0.json"
CASE_LIST_PATH = GCASE_DIR / "gcase_validation_set_v1.0.json"
BOXES_PATH = GCASE_DIR / "docking_boxes.json"


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out-dir", type=Path, default=REPO_ROOT / "docking_runs")
    p.add_argument("--ligand-dir", type=Path, default=None,
                    help="Override directory for <PDB_ID>_ligand_input.sdf (default: GCASE_DIR, i.e. the frozen "
                         "docking_input_ligands/). Use this to dock a freshly re-embedded ligand set (e.g. "
                         "redocking_rerun_v1.0/docking_input_ligands/) without touching the frozen inputs; "
                         "receptor and box are always read from the frozen files regardless of this flag.")
    p.add_argument("--docker-image", default="gnina/gnina:latest", help="GNINA Docker image/tag (default: gnina/gnina:latest)")
    p.add_argument("--no-gpu", action="store_true", help="Run without --gpus all (CPU-only)")
    p.add_argument("--cases", nargs="*", default=None, help="Subset of PDB IDs to run (default: all 14)")
    p.add_argument("--dry-run", action="store_true", help="Print commands without executing them")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    if not args.dry_run and shutil.which("docker") is None:
        print("ERROR: 'docker' not found on PATH.", file=sys.stderr)
        return 1

    with open(PROTOCOL_PATH) as fh:
        protocol = json.load(fh)
    with open(CASE_LIST_PATH) as fh:
        case_list = json.load(fh)
    with open(BOXES_PATH) as fh:
        boxes = json.load(fh)

    gnina_cfg = protocol["gnina"]
    out_gnina_dir = args.out_dir / "gnina"
    # World-writable: some GNINA images run as a non-root user, which would
    # otherwise get PermissionError writing -o/--log into a host-created
    # directory (same root cause hit with DiffDock's appuser) -- see
    # ensure_container_writable_dir's docstring.
    ensure_container_writable_dir(out_gnina_dir)
    volumes = build_volume_args(REPO_ROOT, args.out_dir)

    cases = case_list["cases"]
    if args.cases:
        cases = [c for c in cases if c["pdb_id"] in args.cases]

    run_started_at = utc_now_iso()
    failures = []
    case_manifests = []
    for case in cases:
        pdb_id = case["pdb_id"]
        box = boxes[pdb_id]
        receptor = GCASE_DIR / case["receptor_prepared_file"]
        ligand = (args.ligand_dir / f"{pdb_id}_ligand_input.sdf") if args.ligand_dir else (GCASE_DIR / case["docking_input_ligand_file"])
        out_sdf = out_gnina_dir / f"{pdb_id}_poses.sdf"
        log_path = out_gnina_dir / f"{pdb_id}_gnina.log"

        gnina_cmd = [
            "gnina",
            "-r", container_path(receptor, REPO_ROOT, args.out_dir),
            "-l", container_path(ligand, REPO_ROOT, args.out_dir),
            "--center_x", str(box["center_x"]), "--center_y", str(box["center_y"]), "--center_z", str(box["center_z"]),
            "--size_x", str(box["size_x"]), "--size_y", str(box["size_y"]), "--size_z", str(box["size_z"]),
            "--num_modes", str(gnina_cfg["num_modes"]),
            "--exhaustiveness", str(gnina_cfg["exhaustiveness"]),
            "--seed", str(gnina_cfg["seed"]),
            "--cnn_scoring", gnina_cfg["cnn_scoring"],
            "-o", container_path(out_sdf, REPO_ROOT, args.out_dir),
            "--log", container_path(log_path, REPO_ROOT, args.out_dir),
        ]
        cmd = ["docker", "run", "--rm", *gpu_flags(not args.no_gpu), *volumes, args.docker_image, *gnina_cmd]

        print(f"[{pdb_id}] {shlex.join(cmd)}")
        if args.dry_run:
            continue

        case_started_at = utc_now_iso()
        start = time.monotonic()
        result = subprocess.run(cmd, capture_output=True, text=True)
        runtime = time.monotonic() - start
        success = result.returncode == 0 and out_sdf.is_file()
        if not success:
            failures.append(pdb_id)
            print(f"  FAILED (exit {result.returncode}, {runtime:.1f}s): {result.stderr[-2000:]}", file=sys.stderr)
        else:
            print(f"  OK ({runtime:.1f}s) -> {out_sdf}")
        case_manifests.append({
            "pdb_id": pdb_id,
            "cmd": shlex.join(cmd),
            "started_at_utc": case_started_at,
            "runtime_seconds": round(runtime, 2),
            "returncode": result.returncode,
            "success": success,
        })

    if args.dry_run:
        return 0

    manifest = build_manifest(
        tool="gnina",
        docker_image=args.docker_image,
        repo_root=REPO_ROOT,
        input_files={
            "redocking_protocol": PROTOCOL_PATH,
            "case_list": CASE_LIST_PATH,
            "docking_boxes": BOXES_PATH,
        },
        cases=case_manifests,
        run_started_at=run_started_at,
        run_finished_at=utc_now_iso(),
        extra={"gpu": not args.no_gpu, "ligand_dir_override": str(args.ligand_dir) if args.ligand_dir else None},
    )
    write_manifest(manifest, out_gnina_dir / "manifest.json")

    if failures:
        print(f"\n{len(failures)}/{len(cases)} cases failed: {failures}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

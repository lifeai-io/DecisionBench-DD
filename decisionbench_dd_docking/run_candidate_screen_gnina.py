#!/usr/bin/env python3
"""Runs the 146-job GNINA candidate screen (73 ligands x 2 receptor states)
(decisionbench_dd_configs_v1.0/candidate_screen_v1.0/downstream_gcase_screening_protocol.md,
section 6). Must be run on a GPU instance, same as decisionbench_dd_docking.run_gnina.

Per the protocol, "the engine, CNN model, binary/container digest ... must be
inherited byte-for-byte from the final 14-case GNINA redocking manifest. A
'latest' image tag is prohibited." The default --docker-image here is
therefore the DIGEST-pinned reference actually resolved for the 14-case run
(docking_runs/gnina/manifest.json:docker_image_digest), not the mutable
"gnina/gnina:latest" tag that manifest's own docker_image field recorded --
pinning to the digest is what makes "byte-for-byte identical" true even if
the "latest" tag has since moved upstream.

Inputs (all frozen, produced by earlier candidate-screen steps):
  - receptors_prepared/<3KEH|3KE0>_prepared.pdb
  - docking_boxes.json (per receptor state, from 3GXF/IFM alignment)
  - ligand_microstate_manifest.csv (per ligand_id x receptor_state ->
    prepared 3D SDF), skipping any row with microstate_ambiguous=true or
    embed_ok=false (protocol: "A failed job remains a failure; it is not
    removed from a denominator.")

Output convention consumed by decisionbench_dd_docking.score_candidate_screen:
  <out-dir>/<receptor_state>/<ligand_id>_poses.sdf

Usage:
    python -m decisionbench_dd_docking.run_candidate_screen_gnina --out-dir candidate_screen_runs/ --dry-run
    python -m decisionbench_dd_docking.run_candidate_screen_gnina --out-dir candidate_screen_runs/
    # or, for a separate candidate set (e.g. the MolMIM min_similarity sensitivity
    # rerun) without touching the frozen primary 146-job run:
    python -m decisionbench_dd_docking.run_candidate_screen_gnina \\
        --microstate-manifest decisionbench_dd_configs_v1.0/candidate_screen_v1.0/sensitivity_rerun/ligand_microstate_manifest.csv \\
        --out-dir candidate_screen_runs_sensitivity/
"""
from __future__ import annotations

import argparse
import csv
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
SCREEN_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "candidate_screen_v1.0"
BOXES_PATH = SCREEN_DIR / "docking_boxes.json"
MICROSTATE_MANIFEST = SCREEN_DIR / "ligand_microstate_manifest.csv"

# Resolved for the frozen 14-case GNINA run -- see docking_runs/gnina/manifest.json.
# Pinned by digest (not the "gnina/gnina:latest" tag) so this screen provably
# uses the byte-identical image, per the protocol's "no latest tag" rule.
FROZEN_GNINA_IMAGE = "gnina/gnina@sha256:9da3dc61eef272cecb60798933a9a977d028c47024845fdf1f05a941ce5e25a2"

GNINA_CFG = {"exhaustiveness": 8, "num_modes": 5, "seed": 42, "cnn_scoring": "rescore"}


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out-dir", type=Path, default=REPO_ROOT / "candidate_screen_runs")
    p.add_argument("--docker-image", default=FROZEN_GNINA_IMAGE, help="GNINA image (default: digest-pinned to the frozen 14-case run)")
    p.add_argument("--no-gpu", action="store_true", help="Run without --gpus all (CPU-only)")
    p.add_argument("--receptor-states", nargs="*", default=["3KEH", "3KE0"], help="Subset of receptor states to run")
    p.add_argument("--microstate-manifest", type=Path, default=MICROSTATE_MANIFEST, help="ligand_microstate_manifest.csv to dock (default: frozen primary 146-job manifest)")
    p.add_argument("--dry-run", action="store_true", help="Print commands without executing them")
    return p.parse_args(argv)


def load_ligand_jobs(receptor_states: list[str], microstate_manifest: Path) -> list[dict]:
    with open(microstate_manifest, newline="") as fh:
        rows = list(csv.DictReader(fh))
    jobs = []
    for row in rows:
        if row["receptor_state"] not in receptor_states:
            continue
        if row["microstate_ambiguous"] == "True" or row["embed_ok"] != "True":
            continue
        jobs.append(row)
    return jobs


def main(argv=None) -> int:
    args = parse_args(argv)

    if not args.dry_run and shutil.which("docker") is None:
        print("ERROR: 'docker' not found on PATH.", file=sys.stderr)
        return 1

    boxes = json.loads(BOXES_PATH.read_text())
    jobs = load_ligand_jobs(args.receptor_states, args.microstate_manifest)

    volumes = build_volume_args(REPO_ROOT, args.out_dir)
    run_started_at = utc_now_iso()
    case_manifests = []
    failures = []

    for job in jobs:
        ligand_id = job["ligand_id"]
        receptor_state = job["receptor_state"]
        box = boxes[receptor_state]
        receptor = SCREEN_DIR / "receptors_prepared" / f"{receptor_state}_prepared.pdb"
        ligand = SCREEN_DIR / job["ligand_file"]

        out_dir = args.out_dir / receptor_state
        ensure_container_writable_dir(out_dir)
        out_sdf = out_dir / f"{ligand_id}_poses.sdf"
        log_path = out_dir / f"{ligand_id}_gnina.log"

        gnina_cmd = [
            "gnina",
            "-r", container_path(receptor, REPO_ROOT, args.out_dir),
            "-l", container_path(ligand, REPO_ROOT, args.out_dir),
            "--center_x", str(box["center_x"]), "--center_y", str(box["center_y"]), "--center_z", str(box["center_z"]),
            "--size_x", str(box["size_x"]), "--size_y", str(box["size_y"]), "--size_z", str(box["size_z"]),
            "--num_modes", str(GNINA_CFG["num_modes"]),
            "--exhaustiveness", str(GNINA_CFG["exhaustiveness"]),
            "--seed", str(GNINA_CFG["seed"]),
            "--cnn_scoring", GNINA_CFG["cnn_scoring"],
            "-o", container_path(out_sdf, REPO_ROOT, args.out_dir),
            "--log", container_path(log_path, REPO_ROOT, args.out_dir),
        ]
        cmd = ["docker", "run", "--rm", *gpu_flags(not args.no_gpu), *volumes, args.docker_image, *gnina_cmd]

        print(f"[{receptor_state}/{ligand_id}] {shlex.join(cmd)}")
        if args.dry_run:
            continue

        case_started_at = utc_now_iso()
        start = time.monotonic()
        result = subprocess.run(cmd, capture_output=True, text=True)
        runtime = time.monotonic() - start
        success = result.returncode == 0 and out_sdf.is_file()
        if not success:
            failures.append(f"{receptor_state}/{ligand_id}")
            print(f"  FAILED (exit {result.returncode}, {runtime:.1f}s): {result.stderr[-2000:]}", file=sys.stderr)
        else:
            print(f"  OK ({runtime:.1f}s) -> {out_sdf}")
        case_manifests.append({
            "ligand_id": ligand_id,
            "receptor_state": receptor_state,
            "cmd": shlex.join(cmd),
            "started_at_utc": case_started_at,
            "runtime_seconds": round(runtime, 2),
            "returncode": result.returncode,
            "success": success,
        })

    if args.dry_run:
        print(f"\n[dry-run] {len(jobs)} jobs planned across {args.receptor_states}")
        return 0

    manifest = build_manifest(
        tool="gnina_candidate_screen",
        docker_image=args.docker_image,
        repo_root=REPO_ROOT,
        input_files={"docking_boxes": BOXES_PATH, "ligand_microstate_manifest": MICROSTATE_MANIFEST},
        cases=case_manifests,
        run_started_at=run_started_at,
        run_finished_at=utc_now_iso(),
        extra={"gpu": not args.no_gpu, "gnina_config": GNINA_CFG},
    )
    write_manifest(manifest, args.out_dir / "docking_run_manifest.json")

    if failures:
        print(f"\n{len(failures)}/{len(jobs)} jobs failed: {failures}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

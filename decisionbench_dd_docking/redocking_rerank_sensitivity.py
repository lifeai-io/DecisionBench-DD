#!/usr/bin/env python3
"""Redocking-benchmark half of the bounded reranking-sensitivity analysis
(decisionbench_dd_configs_v1.0/candidate_screen_v1.0/downstream_gcase_screening_protocol.md,
section 10). GNINA-only (CNNscore/CNN_VS are GNINA CNN outputs; DiffDock-L
has no equivalent).

Re-derives Success@1 across the frozen 14-case set under each of the three
pre-specified selectors, applied to the SAME already-generated poses used
for the frozen primary result -- no new docking, no new thresholds. This is
an explicitly non-primary sensitivity readout: the frozen
Success@1 = 21.4% / Success@5 = 57.1% result in docking_results/summary.md
is untouched by this analysis and remains the primary reported number.

Usage:
    python -m decisionbench_dd_docking.redocking_rerank_sensitivity \
        --poses-dir docking_runs/ --out-dir docking_results/
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

from decisionbench_dd_docking.rerank_sensitivity import SELECTORS, load_raw_pose_props, pick_index
from decisionbench_dd_docking.rmsd import RMSDError, SUCCESS_THRESHOLD_ANGSTROM, load_reference, symmetry_aware_rmsd

REPO_ROOT = Path(__file__).resolve().parent.parent
GCASE_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "gcase_validation"
DEFAULT_CASE_LIST = GCASE_DIR / "gcase_validation_set_v1.0.json"


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--poses-dir", type=Path, required=True)
    p.add_argument("--case-list", type=Path, default=DEFAULT_CASE_LIST)
    p.add_argument("--gcase-dir", type=Path, default=GCASE_DIR)
    p.add_argument("--out-dir", type=Path, default=REPO_ROOT / "docking_results")
    p.add_argument("--threshold", type=float, default=SUCCESS_THRESHOLD_ANGSTROM)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    cases = json.loads(args.case_list.read_text())["cases"]

    rows = []
    for case in cases:
        pdb_id = case["pdb_id"]
        reference = load_reference(args.gcase_dir / case["reference_ligand_file"])
        pose_path = args.poses_dir / "gnina" / f"{pdb_id}_poses.sdf"
        raw_poses = load_raw_pose_props(pose_path)

        row = {"pdb_id": pdb_id}
        for selector in SELECTORS:
            idx = pick_index(raw_poses, selector)
            rmsd = None
            if idx is not None:
                try:
                    rmsd = symmetry_aware_rmsd(raw_poses[idx]["mol"], reference)
                except RMSDError:
                    rmsd = None
            row[f"{selector}_rmsd"] = round(rmsd, 3) if rmsd is not None else None
            row[f"{selector}_success_at_1"] = rmsd is not None and rmsd <= args.threshold
        rows.append(row)

    fieldnames = ["pdb_id"] + [f"{s}_{suffix}" for s in SELECTORS for suffix in ("rmsd", "success_at_1")]
    out_csv = args.out_dir / "redocking_rerank_sensitivity.csv"
    with open(out_csv, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Redocking Success@1 under fixed, pre-specified pose selectors",
        "",
        "Sensitivity analysis only -- does not change the frozen primary result "
        "(docking_results/summary.md: GNINA Success@1 = 21.4%, Success@5 = 57.1%). "
        "No selector was chosen based on these outcomes; all three were "
        "pre-specified in redocking_protocol_v1.0.json/downstream_gcase_screening_protocol.md "
        "section 10 before this analysis was run.",
        "",
        "| Selector | Success@1 (n=14) | Median RMSD |",
        "| --- | ---: | ---: |",
    ]
    for selector in SELECTORS:
        n_success = sum(1 for r in rows if r[f"{selector}_success_at_1"])
        rmsds = [r[f"{selector}_rmsd"] for r in rows if r[f"{selector}_rmsd"] is not None]
        n_scored = len(rmsds)
        median_rmsd = f"{statistics.median(rmsds):.2f} A" if rmsds else "N/A"
        lines.append(f"| {selector} | {n_success}/14 ({100*n_success/14:.1f}%), scored={n_scored}/14 | {median_rmsd} |")
    (args.out_dir / "redocking_rerank_sensitivity.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote results to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

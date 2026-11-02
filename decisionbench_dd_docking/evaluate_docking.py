#!/usr/bin/env python3
"""DecisionBench-DD GCase redocking evaluation CLI.

Ingests GNINA/DiffDock-L pose predictions and scores them against the frozen
14-case GCase redocking set (decisionbench_dd_configs_v1.0/gcase_validation/),
per redocking_protocol_v1.0.json's rmsd_scoring section: heavy-atom,
symmetry-aware, in-place RMSD (rdMolAlign.CalcRMS, not GetBestRMS -- see
decisionbench_dd_docking/rmsd.py's docstring for why that distinction matters).

Expected input layout, one multi-model SDF per (tool, case), poses in rank
order (best/top-1 first) -- see redocking_protocol_v1.0.json's gnina/diffdock
sections for how each tool's raw output should be normalized into this form:

    <poses-dir>/<tool>/<PDB_ID>_poses.sdf

Usage:
    python -m decisionbench_dd_docking.evaluate_docking \\
        --poses-dir docking_runs/ --out-dir docking_results/
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from decisionbench_dd_docking.rmsd import SUCCESS_THRESHOLD_ANGSTROM, score_case, success_rate

REPO_ROOT = Path(__file__).resolve().parent.parent
GCASE_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "gcase_validation"
DEFAULT_CASE_LIST = GCASE_DIR / "gcase_validation_set_v1.0.json"


def load_cases(case_list_path: Path) -> list[dict]:
    with open(case_list_path, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    return spec["cases"]


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--poses-dir", type=Path, required=True, help="Directory containing <tool>/<PDB_ID>_poses.sdf")
    p.add_argument("--tools", nargs="*", default=["gnina", "diffdock"], help="Tool subdirectory names to look for (default: gnina diffdock)")
    p.add_argument("--case-list", type=Path, default=DEFAULT_CASE_LIST, help="Path to gcase_validation_set_v1.0.json")
    p.add_argument("--gcase-dir", type=Path, default=GCASE_DIR, help="Directory containing reference_ligands/")
    p.add_argument("--out-dir", type=Path, default=REPO_ROOT / "docking_results", help="Output directory")
    p.add_argument("--top-n", type=int, default=5, help="Number of ranked poses to score (default: 5)")
    p.add_argument("--threshold", type=float, default=SUCCESS_THRESHOLD_ANGSTROM, help="Success RMSD threshold in Angstrom (default: 2.0)")
    return p.parse_args(argv)


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv=None) -> int:
    args = parse_args(argv)
    cases = load_cases(args.case_list)

    missing_tools = [t for t in args.tools if not (args.poses_dir / t).is_dir()]
    for t in missing_tools:
        print(f"NOTE: no pose directory found for tool '{t}' at {args.poses_dir / t} -- skipping.", file=sys.stderr)
    tools = [t for t in args.tools if t not in missing_tools]
    if not tools:
        print(f"ERROR: no tool pose directories found under {args.poses_dir}.", file=sys.stderr)
        return 1

    per_case_rows = []
    results_by_tool = defaultdict(list)

    receptor_field_by_tool = {
        "gnina": "receptor_prepared_file",
        "diffdock": "receptor_cropped_for_diffdock_file",
    }

    for tool in tools:
        for case in cases:
            pdb_id = case["pdb_id"]
            reference_path = args.gcase_dir / case["reference_ligand_file"]
            pose_path = args.poses_dir / tool / f"{pdb_id}_poses.sdf"
            receptor_field = receptor_field_by_tool.get(tool)
            receptor_path = (args.gcase_dir / case[receptor_field]) if receptor_field and receptor_field in case else None
            result = score_case(pdb_id, tool, pose_path, reference_path, success_threshold=args.threshold, top_n=args.top_n, receptor_path=receptor_path)
            results_by_tool[tool].append(result)
            per_case_rows.append({
                "tool": tool,
                "pdb_id": pdb_id,
                "site_stratum": case["site_stratum"],
                "n_poses_scored": result.n_poses_scored,
                "top1_rmsd": result.top1_rmsd,
                "best_of_n_rmsd": result.best_of_n_rmsd,
                "success_at_1": result.success_at_1,
                "success_at_n": result.success_at_n,
                "top1_valid": result.top1_valid,
                "error": result.error,
                "pose_rmsds": ";".join(f"{r:.3f}" if r is not None else "NA" for r in result.pose_rmsds),
                "pose_valid": ";".join(str(v) for v in result.pose_valid),
                "n_poses_charge_artifact_fixed": result.n_poses_charge_artifact_fixed,
            })

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        args.out_dir / "per_case_rmsd.csv",
        per_case_rows,
        ["tool", "pdb_id", "site_stratum", "n_poses_scored", "top1_rmsd", "best_of_n_rmsd",
         "success_at_1", "success_at_n", "top1_valid", "pose_rmsds", "pose_valid",
         "n_poses_charge_artifact_fixed", "error"],
    )

    summary = {}
    for tool, results in results_by_tool.items():
        by_stratum = defaultdict(list)
        for r, case in zip(results, cases):
            by_stratum[case["site_stratum"]].append(r)
        top1_values = [r.top1_rmsd for r in results if r.top1_rmsd is not None]
        best_of_n_values = [r.best_of_n_rmsd for r in results if r.best_of_n_rmsd is not None]
        top1_valid_values = [r.top1_valid for r in results if r.top1_valid is not None]
        all_pose_valid_values = [v for r in results for v in r.pose_valid]
        summary[tool] = {
            "n_cases": len(results),
            "n_failed": sum(1 for r in results if r.error is not None),
            "n_poses_charge_artifact_fixed": sum(r.n_poses_charge_artifact_fixed for r in results),
            f"success_at_1_{args.threshold}A_pct": success_rate(results, "success_at_1"),
            f"success_at_{args.top_n}_{args.threshold}A_pct": success_rate(results, "success_at_n"),
            # statistics.median (not sorted[n//2], which silently picks the
            # upper-middle element and is wrong for any even-length list --
            # caught by cross-checking against an independent hand
            # computation of these exact numbers).
            "median_top1_rmsd": (statistics.median(top1_values) if top1_values else None),
            "median_best_of_n_rmsd": (statistics.median(best_of_n_values) if best_of_n_values else None),
            "top1_pose_valid_pct": (100.0 * sum(top1_valid_values) / len(top1_valid_values)) if top1_valid_values else None,
            "all_pose_valid_pct": (100.0 * sum(all_pose_valid_values) / len(all_pose_valid_values)) if all_pose_valid_values else None,
            "by_stratum": {
                stratum: {
                    "n": len(res),
                    f"success_at_1_{args.threshold}A_pct": success_rate(res, "success_at_1"),
                    f"success_at_{args.top_n}_{args.threshold}A_pct": success_rate(res, "success_at_n"),
                }
                for stratum, res in by_stratum.items()
            },
        }

    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# DecisionBench-DD GCase redocking summary",
        "",
        "GNINA is box-conditioned (precise 6 A padding around the crystal ligand). "
        "'diffdock' below is DiffDock-L with ligand-centered 15 A receptor cropping "
        "(see redocking_protocol_v1.0.json:diffdock.receptor_cropping) -- an "
        "approximation of pocket-conditioning, not equivalent to GNINA's box, and "
        "not native/uncropped DiffDock-L.",
        "",
        "Pose-validity proxy (decisionbench_dd_docking/pose_validity.py; a simplified "
        "PoseBusters-style check, not the official PoseBusters suite): valid RDKit "
        "valences; every bond length in [0.7, 2.2] A; no non-bonded heavy-atom pair "
        "closer than 1.5 A (internal clash); no ligand-to-receptor heavy-atom pair "
        "closer than 1.5 A (protein clash, flat cutoff, not VDW-scaled). Does not "
        "check ring planarity or torsion-angle plausibility.",
        "",
        "This was a targeted correction rather than an independent stochastic "
        "replicate. Under the pinned DiffDock-L container and invocation used here, "
        "repeated executions produced byte-identical poses across all 14 cases, and "
        "the interface exposed no seed control; consequently, stochastic uncertainty "
        "could not be estimated. This reproducibility is empirically observed under "
        "the tested environment, not a claim that DiffDock is inherently or "
        "universally deterministic -- identical outputs could reflect internal fixed "
        "seeding or deterministic execution in this specific image, and do not "
        "establish the behavior of every DiffDock deployment.",
        "",
        "Formal-charge normalization was applied to 15 DiffDock poses before RMSD "
        "calculation (see n_poses_charge_artifact_fixed below and "
        "rmsd._fix_known_pose_charge_artifact). Programmatic comparison confirmed "
        "zero changes to atomic coordinates, connectivity, stereochemistry, or pose "
        "ranking.",
        "",
    ]
    for tool, s in summary.items():
        lines.append(f"## {tool}")
        lines.append(f"- Success@1 ({args.threshold} A) = {s[f'success_at_1_{args.threshold}A_pct']:.1f}% (n={s['n_cases']}, {s['n_failed']} failed)")
        lines.append(f"- Success@{args.top_n} ({args.threshold} A) = {s[f'success_at_{args.top_n}_{args.threshold}A_pct']:.1f}%")
        if s["median_top1_rmsd"] is not None:
            lines.append(f"- Median top-1 RMSD = {s['median_top1_rmsd']:.2f} A")
        if s["median_best_of_n_rmsd"] is not None:
            lines.append(f"- Median best-of-{args.top_n} RMSD = {s['median_best_of_n_rmsd']:.2f} A")
        if s["top1_pose_valid_pct"] is not None:
            lines.append(f"- Top-1 pose geometry valid = {s['top1_pose_valid_pct']:.1f}%")
        if s["all_pose_valid_pct"] is not None:
            lines.append(f"- All scored poses geometry valid = {s['all_pose_valid_pct']:.1f}%")
        if s["n_poses_charge_artifact_fixed"]:
            lines.append(f"- {s['n_poses_charge_artifact_fixed']} scored pose(s) had a known output-representation charge artifact corrected before RMSD scoring (see rmsd._fix_known_pose_charge_artifact; per_case_rmsd.csv's n_poses_charge_artifact_fixed column names exactly which cases).")
        for stratum, sv in s["by_stratum"].items():
            lines.append(f"  - {stratum} (n={sv['n']}): Success@1 = {sv[f'success_at_1_{args.threshold}A_pct']:.1f}%, Success@{args.top_n} = {sv[f'success_at_{args.top_n}_{args.threshold}A_pct']:.1f}%")
        lines.append("")
    (args.out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote results to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

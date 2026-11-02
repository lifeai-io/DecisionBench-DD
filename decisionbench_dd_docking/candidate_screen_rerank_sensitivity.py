#!/usr/bin/env python3
"""Candidate-screen half of the bounded reranking-sensitivity analysis
(decisionbench_dd_configs_v1.0/candidate_screen_v1.0/downstream_gcase_screening_protocol.md,
section 10 and the "Next step" of the 2026-08-27 candidate-screen review:
"use the already-generated poses to determine whether a prespecified Top-5
rescoring rule rescues additional candidates. Preserve the current 15/1
result as the frozen primary analysis").

Two independent, non-fitted questions, both against the SAME already-scored
3KEH poses (no new docking):

1. Best-of-5 rescue: holding the frozen primary pass bar fixed (geometry
   valid, active-site occupied, CNNaffinity >= Ambroxol's native-rank1
   CNNaffinity), does ANY of a candidate's 5 poses pass, not just its native
   rank-1? This is selector-agnostic -- it just asks whether the ensemble
   contains a passing pose anywhere.
2. Fixed-selector sensitivity: for each of the three pre-specified selectors
   (native rank1 / CNN_VS descending / minimizedAffinity ascending), re-pick
   a single "top-1" pose per candidate (AND recompute Ambroxol's own
   threshold under that same selector, since a different selector could
   also move which Ambroxol pose counts) and report Y_structural_proxy under
   each. No selector is chosen based on which one performs best.

Neither analysis changes the frozen primary result
(candidate_screen_results/summary.md: 15 GenMol + 1 MolMIM pass).

Usage:
    python -m decisionbench_dd_docking.candidate_screen_rerank_sensitivity \
        --runs-dir candidate_screen_runs/ --out-dir candidate_screen_results/
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from rdkit import Chem

from decisionbench_dd_docking.pose_validity import check_pose_validity
from decisionbench_dd_docking.rerank_sensitivity import SELECTORS, load_raw_pose_props, pick_index
from decisionbench_dd_docking.score_candidate_screen import (
    N_GENMOL_MOLMIM_REQUESTED,
    SCREEN_DIR,
    _active_site_occupied,
    _load_catalytic_oxygen_coords,
    exact_binomial_ci,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CANDIDATE_MANIFEST = SCREEN_DIR / "candidate_manifest.csv"
AMBROXOL_ID = "CTRL_AMBROXOL"


def _pose_verdict(pose: dict, receptor_path: Path, catalytic_oxygens) -> tuple[bool, bool, float]:
    """(valid, occupied, cnnaffinity) for one raw pose dict."""
    mol_noh = Chem.RemoveHs(pose["mol"])
    valid = check_pose_validity(mol_noh, receptor_path=receptor_path).is_valid
    occupied = _active_site_occupied(mol_noh, catalytic_oxygens)
    return valid, occupied, pose["cnnaffinity"]


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--runs-dir", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, default=REPO_ROOT / "candidate_screen_results")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    with open(CANDIDATE_MANIFEST, newline="") as fh:
        candidates = list(csv.DictReader(fh))

    receptor_path = SCREEN_DIR / "receptors_prepared" / "3KEH_prepared.pdb"
    catalytic_oxygens = _load_catalytic_oxygen_coords(receptor_path)

    def raw_poses_for(ligand_id: str) -> list[dict]:
        return load_raw_pose_props(args.runs_dir / "3KEH" / f"{ligand_id}_poses.sdf")

    ambroxol_poses = raw_poses_for(AMBROXOL_ID)
    ambroxol_native_cnnaffinity = ambroxol_poses[pick_index(ambroxol_poses, "native_rank1")]["cnnaffinity"]

    # --- 1. Best-of-5 rescue, fixed native-rank1 Ambroxol bar ---
    rescue_rows = []
    for candidate in candidates:
        cid = candidate["candidate_id"]
        poses = raw_poses_for(cid)
        native_idx = pick_index(poses, "native_rank1")
        native_valid, native_occupied, native_aff = _pose_verdict(poses[native_idx], receptor_path, catalytic_oxygens)
        native_pass = native_valid and native_occupied and native_aff >= ambroxol_native_cnnaffinity

        any_pass = False
        best_rank = None
        for pose in poses:
            valid, occupied, aff = _pose_verdict(pose, receptor_path, catalytic_oxygens)
            if valid and occupied and aff >= ambroxol_native_cnnaffinity:
                any_pass = True
                if best_rank is None:
                    best_rank = pose["rank"]
        rescue_rows.append({
            "candidate_id": cid, "tool": candidate["tool"],
            "native_rank1_pass": native_pass,
            "best_of_5_pass": any_pass,
            "rescued_by_top5": any_pass and not native_pass,
            "first_passing_rank": best_rank,
        })

    with open(args.out_dir / "best_of_5_rescue.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rescue_rows[0].keys()))
        writer.writeheader()
        writer.writerows(rescue_rows)

    n_native_pass = sum(1 for r in rescue_rows if r["native_rank1_pass"])
    n_best_of_5_pass = sum(1 for r in rescue_rows if r["best_of_5_pass"])
    n_rescued = sum(1 for r in rescue_rows if r["rescued_by_top5"])
    rescued_ids = [r["candidate_id"] for r in rescue_rows if r["rescued_by_top5"]]

    # --- 2. Fixed-selector sensitivity ---
    selector_rows = []
    for selector in SELECTORS:
        amb_idx = pick_index(ambroxol_poses, selector)
        if amb_idx is None:
            selector_rows.append({"selector": selector, "note": "selector field unavailable", "n_pass": None})
            continue
        _, _, amb_aff = _pose_verdict(ambroxol_poses[amb_idx], receptor_path, catalytic_oxygens)

        by_tool = {"genmol": 0, "molmim": 0}
        for candidate in candidates:
            cid = candidate["candidate_id"]
            poses = raw_poses_for(cid)
            idx = pick_index(poses, selector)
            if idx is None:
                continue
            valid, occupied, aff = _pose_verdict(poses[idx], receptor_path, catalytic_oxygens)
            if valid and occupied and aff >= amb_aff:
                by_tool[candidate["tool"]] += 1

        n_pass = by_tool["genmol"] + by_tool["molmim"]
        selector_rows.append({
            "selector": selector,
            "ambroxol_cnnaffinity_under_selector": round(amb_aff, 3),
            "n_pass_genmol": by_tool["genmol"],
            "n_pass_molmim": by_tool["molmim"],
            "n_pass_total": n_pass,
            "Y_structural_proxy_genmol": round(by_tool["genmol"] / N_GENMOL_MOLMIM_REQUESTED, 4),
            "Y_structural_proxy_molmim": round(by_tool["molmim"] / N_GENMOL_MOLMIM_REQUESTED, 4),
        })

    with open(args.out_dir / "selector_sensitivity.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["selector", "ambroxol_cnnaffinity_under_selector", "n_pass_genmol", "n_pass_molmim", "n_pass_total", "Y_structural_proxy_genmol", "Y_structural_proxy_molmim", "note"])
        writer.writeheader()
        writer.writerows(selector_rows)

    # --- 3. Candidate-level turnover: one row per candidate per selector,
    # so which candidates were gained/lost/retained between selectors is
    # auditable directly, not just net aggregate counts.
    ambroxol_threshold_by_selector = {}
    for selector in SELECTORS:
        idx = pick_index(ambroxol_poses, selector)
        ambroxol_threshold_by_selector[selector] = (
            _pose_verdict(ambroxol_poses[idx], receptor_path, catalytic_oxygens)[2] if idx is not None else None
        )

    turnover_rows = []
    for candidate in candidates:
        cid = candidate["candidate_id"]
        poses = raw_poses_for(cid)
        for selector in SELECTORS:
            idx = pick_index(poses, selector)
            amb_threshold = ambroxol_threshold_by_selector[selector]
            if idx is None or amb_threshold is None:
                turnover_rows.append({
                    "candidate_id": cid, "tool": candidate["tool"], "selector": selector,
                    "selected_pose_rank": None, "cnnscore": None, "cnnaffinity": None,
                    "cnn_vs": None, "minimized_affinity": None, "valid": None,
                    "occupied": None, "pass": False,
                })
                continue
            pose = poses[idx]
            valid, occupied, aff = _pose_verdict(pose, receptor_path, catalytic_oxygens)
            turnover_rows.append({
                "candidate_id": cid, "tool": candidate["tool"], "selector": selector,
                "selected_pose_rank": pose["rank"], "cnnscore": round(pose["cnnscore"], 4),
                "cnnaffinity": round(pose["cnnaffinity"], 4),
                "cnn_vs": round(pose["cnn_vs"], 4) if pose["cnn_vs"] is not None else None,
                "minimized_affinity": round(pose["minimized_affinity"], 4),
                "valid": valid, "occupied": occupied,
                "pass": valid and occupied and aff >= amb_threshold,
            })

    with open(args.out_dir / "candidate_selector_turnover.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(turnover_rows[0].keys()))
        writer.writeheader()
        writer.writerows(turnover_rows)

    lines = [
        "# Candidate-screen reranking-sensitivity analysis",
        "",
        "Sensitivity analysis only -- does not change the frozen primary result "
        "(candidate_screen_results/summary.md: 15 GenMol + 1 MolMIM structural-proxy pass). "
        "Neither the best-of-5 bar nor the three selectors below were chosen based on "
        "these outcomes.",
        "",
        "## Best-of-5 rescue (fixed pass bar: geometry valid, active-site occupied, "
        f"CNNaffinity >= Ambroxol native-rank1 = {ambroxol_native_cnnaffinity:.3f})",
        "",
        f"- Native rank-1 passes: {n_native_pass}/69",
        f"- Best-of-5 passes (any of 5 poses): {n_best_of_5_pass}/69",
        f"- Rescued by looking past rank 1: {n_rescued} ({', '.join(rescued_ids) if rescued_ids else 'none'})",
        "",
        "## Fixed-selector sensitivity (Y_structural_proxy = passes / 300 requested)",
        "",
        "| Selector | Ambroxol CNNaffinity | GenMol pass | MolMIM pass | Y_genmol | Y_molmim |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in selector_rows:
        if r.get("note"):
            lines.append(f"| {r['selector']} | -- | -- | -- | -- | -- | ({r['note']}) |")
        else:
            lines.append(f"| {r['selector']} | {r['ambroxol_cnnaffinity_under_selector']:.3f} | {r['n_pass_genmol']} | {r['n_pass_molmim']} | {r['Y_structural_proxy_genmol']*100:.2f}% | {r['Y_structural_proxy_molmim']*100:.2f}% |")
    lines += [
        "",
        "Per-candidate, per-selector detail (selected pose rank, CNNscore/CNNaffinity/"
        "CNN_VS/minimizedAffinity, geometry validity, occupancy, pass/fail) is archived "
        "in candidate_selector_turnover.csv -- one row per candidate per selector, so "
        "gains/losses/retentions between selectors are auditable directly rather than "
        "only visible as net aggregate counts.",
        "",
        "## Advancement population",
        "",
        f"- **Primary set (frozen, advance to ADMET/diversity triage): {n_native_pass} candidates** "
        "-- the native-rank-1 structural-proxy passers, unchanged by this analysis.",
        f"- **Exploratory Top-5 reserve (kept separately labelled, NOT merged into the primary "
        f"count): {n_rescued} candidates** -- {', '.join(rescued_ids) if rescued_ids else 'none'}. "
        "These have a passing pose somewhere in their Top-5 but were not selected by the frozen "
        "native-CNNscore-rank-1 rule; no reranking rule is adopted here to promote them, per the "
        "redocking evidence below showing selector performance does not transfer cleanly between "
        "the redocking and candidate-screen populations (minimizedAffinity improves redocking "
        f"Success@1 but drops candidate-screen passes from {n_native_pass} to "
        f"{next(r['n_pass_total'] for r in selector_rows if r['selector']=='minimized_affinity_asc')}).",
        f"- Do not report a combined \"{n_best_of_5_pass} qualified candidates\" headline: the 16/11 "
        "split must stay visible in any downstream reporting.",
    ]
    (args.out_dir / "rerank_sensitivity.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote results to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

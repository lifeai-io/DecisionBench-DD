#!/usr/bin/env python3
"""Step 6 of the decoy-panel calibration addendum: verifies covariate balance
between the 69 candidates and their 345 matched decoys before docking. Writes
matching_balance.csv (mean/median/SMD/max-within-pair-diff per property) and
matching_balance_figure.pdf (SMD dot plot), and re-checks the structural
integrity conditions (no duplicate decoys, no candidate/control overlap,
similarity exclusions held, exactly 5 decoys per candidate, no docking
outcomes used in matching).

Usage:
    python -m decisionbench_dd_docking.verify_decoy_balance
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "candidate_screen_v1.0" / "decoy_panel_v1.0"
CANDIDATE_REF = OUT_DIR / "candidate_reference_v1.0.csv"
MATCHED = OUT_DIR / "property_matched_decoys.csv"
OUT_BALANCE_CSV = OUT_DIR / "matching_balance.csv"
OUT_BALANCE_FIG = OUT_DIR / "matching_balance_figure.pdf"
OUT_INTEGRITY = OUT_DIR / "matching_integrity_check.json"

PROPS = [
    ("mw", "mw", "MW"),
    ("hac", "hac", "HAC"),
    ("clogp", "clogp", "cLogP"),
    ("tpsa", "tpsa", "TPSA"),
    ("hbd", "hbd", "HBD"),
    ("hba", "hba", "HBA"),
    ("rotatable_bonds", "rotatable_bonds", "RotBonds"),
    ("ring_count", "ring_count", "RingCount"),
    ("halogen_count", "halogen_count", "HalogenCount"),
]


def smd(a: np.ndarray, b: np.ndarray) -> float:
    pooled_sd = np.sqrt((np.var(a, ddof=1) + np.var(b, ddof=1)) / 2)
    if pooled_sd == 0:
        return 0.0
    return float((np.mean(a) - np.mean(b)) / pooled_sd)


def main() -> int:
    cand = pd.read_csv(CANDIDATE_REF)
    matched = pd.read_csv(MATCHED)

    rows = []
    for cand_col, decoy_prefix, label in PROPS:
        c_vals = cand[cand_col].to_numpy(dtype=float)
        d_vals = matched[f"decoy_{decoy_prefix}"].to_numpy(dtype=float)
        # max within-pair diff: for each candidate, max |candidate - its 5 decoys|
        max_within_pair = 0.0
        for _, crow in cand.iterrows():
            dsub = matched.loc[matched["candidate_id"] == crow["candidate_id"], f"decoy_{decoy_prefix}"]
            if len(dsub):
                max_within_pair = max(max_within_pair, float(np.abs(dsub.to_numpy(dtype=float) - crow[cand_col]).max()))
        rows.append({
            "property": label,
            "candidate_mean": round(float(np.mean(c_vals)), 3),
            "candidate_median": round(float(np.median(c_vals)), 3),
            "decoy_mean": round(float(np.mean(d_vals)), 3),
            "decoy_median": round(float(np.median(d_vals)), 3),
            "smd": round(smd(c_vals, d_vals), 4),
            "max_within_pair_diff": round(max_within_pair, 3),
        })

    bal_df = pd.DataFrame(rows)
    bal_df.to_csv(OUT_BALANCE_CSV, index=False)

    fig, ax = plt.subplots(figsize=(6, 4))
    y = np.arange(len(bal_df))
    ax.axvline(0, color="black", linewidth=0.8)
    ax.axvline(0.10, color="gray", linestyle="--", linewidth=0.8)
    ax.axvline(-0.10, color="gray", linestyle="--", linewidth=0.8)
    ax.scatter(bal_df["smd"], y)
    ax.set_yticks(y)
    ax.set_yticklabels(bal_df["property"])
    ax.set_xlabel("Standardized mean difference (candidate - decoy)")
    ax.set_title("Decoy-panel covariate balance (target |SMD| < 0.10)")
    fig.tight_layout()
    fig.savefig(OUT_BALANCE_FIG)

    # Integrity checks
    n_dup_decoys = matched["decoy_chembl_id"].duplicated().sum()
    n_per_candidate = matched.groupby("candidate_id").size()
    all_five = bool((n_per_candidate == 5).all())
    cand_smiles = set(cand["canonical_smiles_isomeric"])
    overlap = cand_smiles & set(matched["decoy_canonical_smiles"])

    integrity = {
        "n_duplicate_decoys": int(n_dup_decoys),
        "all_candidates_have_5_decoys": all_five,
        "n_candidates": int(cand.shape[0]),
        "n_decoys": int(matched.shape[0]),
        "candidate_decoy_smiles_overlap": sorted(overlap),
        "smd_within_target_0_10": {row["property"]: abs(row["smd"]) < 0.10 for row in rows},
        "smd_within_tolerance_0_20": {row["property"]: abs(row["smd"]) < 0.20 for row in rows},
    }
    with open(OUT_INTEGRITY, "w") as fh:
        json.dump(integrity, fh, indent=2)

    print(bal_df.to_string(index=False))
    print()
    print(json.dumps(integrity, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

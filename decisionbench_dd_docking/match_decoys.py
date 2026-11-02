#!/usr/bin/env python3
"""Step 5 of the decoy-panel calibration addendum: matches 5 decoys per
candidate (69 x 5 = 345) from the eligible pool (build_decoy_pool.py output,
~1.26M rows for ChEMBL 37), without replacement, using hard calipers + a
weighted standardized distance, with a documented relaxation ladder when a
candidate has <5 eligible matches at the base calipers. Matching never looks
at docking scores or structural-proxy labels (none exist yet for decoys).

Vectorized with numpy/pandas -- the pool is ~1.26M rows, too large for a
per-candidate pure-Python scan.

Usage:
    python -m decisionbench_dd_docking.match_decoys
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "candidate_screen_v1.0" / "decoy_panel_v1.0"
CANDIDATE_REF = OUT_DIR / "candidate_reference_v1.0.csv"
ELIGIBLE_POOL = OUT_DIR / "eligible_pool_v1.0.csv"
OUT_MATCHED = OUT_DIR / "property_matched_decoys.csv"
OUT_RELAX_LOG = OUT_DIR / "matching_relaxation_log.json"

N_PER_CANDIDATE = 5
RNG_SEED = 42

BASE_CALIPERS = {"hac": 2, "mw_pct": 0.10, "mw_abs": 25, "clogp": 0.5, "tpsa": 10,
                 "hbd": 1, "hba": 1, "rotb": 1, "ring": 1, "halogen": 1}
RELAXATION_LADDER = [
    {"mw_pct": 0.15, "tpsa": 15, "clogp": 0.75},
    {"mw_pct": 0.15, "tpsa": 15, "clogp": 0.75, "hac": 2, "hbd": 2, "hba": 2, "rotb": 2, "ring": 2, "halogen": 99},
]

WEIGHTS = {"hac": 3.0, "clogp": 3.0, "mw": 1.5, "tpsa": 1.0, "hbd": 0.5, "hba": 0.5, "rotb": 0.5, "ring": 0.5, "halogen": 0.5}
SCALES = {"hac": 5.0, "clogp": 1.0, "mw": 60.0, "tpsa": 20.0, "hbd": 1.0, "hba": 1.5, "rotb": 2.0, "ring": 1.0, "halogen": 1.5}


def main() -> int:
    candidates = pd.read_csv(CANDIDATE_REF)
    pool = pd.read_csv(ELIGIBLE_POOL)
    # numpy arrays for fast vectorized caliper/distance math
    p_hac = pool["hac"].to_numpy(dtype=np.float64)
    p_mw = pool["mw"].to_numpy(dtype=np.float64)
    p_clogp = pool["clogp"].to_numpy(dtype=np.float64)
    p_tpsa = pool["tpsa"].to_numpy(dtype=np.float64)
    p_hbd = pool["hbd"].to_numpy(dtype=np.float64)
    p_hba = pool["hba"].to_numpy(dtype=np.float64)
    p_rotb = pool["rotatable_bonds"].to_numpy(dtype=np.float64)
    p_ring = pool["ring_count"].to_numpy(dtype=np.float64)
    p_halogen = pool["halogen_count"].to_numpy(dtype=np.float64)
    p_charge = pool["formal_charge"].to_numpy(dtype=np.float64)
    available = np.ones(len(pool), dtype=bool)

    rng = np.random.default_rng(RNG_SEED)
    order = rng.permutation(len(candidates))

    matched_rows = []
    relaxation_log = []

    for idx in order:
        cand = candidates.iloc[idx]
        chosen_positions: list[int] = []
        relax_level = 0
        calipers = dict(BASE_CALIPERS)

        while len(chosen_positions) < N_PER_CANDIDATE:
            mw_tol = max(calipers["mw_pct"] * cand["mw"], calipers["mw_abs"])
            mask = (
                available
                & (p_charge == cand["formal_charge"])
                & (np.abs(p_hac - cand["hac"]) <= calipers["hac"])
                & (np.abs(p_mw - cand["mw"]) <= mw_tol)
                & (np.abs(p_clogp - cand["clogp"]) <= calipers["clogp"])
                & (np.abs(p_tpsa - cand["tpsa"]) <= calipers["tpsa"])
                & (np.abs(p_hbd - cand["hbd"]) <= calipers["hbd"])
                & (np.abs(p_hba - cand["hba"]) <= calipers["hba"])
                & (np.abs(p_rotb - cand["rotatable_bonds"]) <= calipers["rotb"])
                & (np.abs(p_ring - cand["ring_count"]) <= calipers["ring"])
                & (np.abs(p_halogen - cand["halogen_count"]) <= calipers["halogen"])
            )
            cand_positions = np.flatnonzero(mask)
            if cand_positions.size > 0:
                dist = (
                    WEIGHTS["hac"] * np.abs(p_hac[cand_positions] - cand["hac"]) / SCALES["hac"]
                    + WEIGHTS["clogp"] * np.abs(p_clogp[cand_positions] - cand["clogp"]) / SCALES["clogp"]
                    + WEIGHTS["mw"] * np.abs(p_mw[cand_positions] - cand["mw"]) / SCALES["mw"]
                    + WEIGHTS["tpsa"] * np.abs(p_tpsa[cand_positions] - cand["tpsa"]) / SCALES["tpsa"]
                    + WEIGHTS["hbd"] * np.abs(p_hbd[cand_positions] - cand["hbd"]) / SCALES["hbd"]
                    + WEIGHTS["hba"] * np.abs(p_hba[cand_positions] - cand["hba"]) / SCALES["hba"]
                    + WEIGHTS["rotb"] * np.abs(p_rotb[cand_positions] - cand["rotatable_bonds"]) / SCALES["rotb"]
                    + WEIGHTS["ring"] * np.abs(p_ring[cand_positions] - cand["ring_count"]) / SCALES["ring"]
                    + WEIGHTS["halogen"] * np.abs(p_halogen[cand_positions] - cand["halogen_count"]) / SCALES["halogen"]
                )
                need = N_PER_CANDIDATE - len(chosen_positions)
                order_by_dist = cand_positions[np.argsort(dist)]
                take = order_by_dist[:need]
                for pos in take:
                    available[pos] = False
                    chosen_positions.append((pos, relax_level))

            if len(chosen_positions) >= N_PER_CANDIDATE:
                break
            if relax_level >= len(RELAXATION_LADDER):
                break
            calipers.update(RELAXATION_LADDER[relax_level])
            relax_level += 1

        if relax_level > 0:
            relaxation_log.append({"candidate_id": cand["candidate_id"], "relax_level": relax_level,
                                    "n_matched": len(chosen_positions)})
        if len(chosen_positions) < N_PER_CANDIDATE:
            relaxation_log.append({"candidate_id": cand["candidate_id"], "SHORT_MATCH": True,
                                    "n_matched": len(chosen_positions), "requested": N_PER_CANDIDATE})

        for rank, (pos, rl) in enumerate(chosen_positions, start=1):
            d = pool.iloc[pos]
            dist_val = (
                WEIGHTS["hac"] * abs(d["hac"] - cand["hac"]) / SCALES["hac"]
                + WEIGHTS["clogp"] * abs(d["clogp"] - cand["clogp"]) / SCALES["clogp"]
                + WEIGHTS["mw"] * abs(d["mw"] - cand["mw"]) / SCALES["mw"]
                + WEIGHTS["tpsa"] * abs(d["tpsa"] - cand["tpsa"]) / SCALES["tpsa"]
            )
            matched_rows.append({
                "candidate_id": cand["candidate_id"], "candidate_tool": cand["tool"],
                "match_rank": rank, "relaxation_level": rl,
                "decoy_chembl_id": d["chembl_id"], "decoy_canonical_smiles": d["canonical_smiles"],
                "decoy_mw": d["mw"], "decoy_hac": d["hac"], "decoy_clogp": d["clogp"], "decoy_tpsa": d["tpsa"],
                "decoy_hbd": d["hbd"], "decoy_hba": d["hba"], "decoy_rotatable_bonds": d["rotatable_bonds"],
                "decoy_formal_charge": d["formal_charge"], "decoy_ring_count": d["ring_count"],
                "decoy_aromatic_ring_count": d["aromatic_ring_count"], "decoy_halogen_count": d["halogen_count"],
                "weighted_distance": round(float(dist_val), 4),
            })

    out_df = pd.DataFrame(matched_rows)
    out_df.to_csv(OUT_MATCHED, index=False)

    n_relaxed = sum(1 for r in relaxation_log if not r.get("SHORT_MATCH"))
    n_short = sum(1 for r in relaxation_log if r.get("SHORT_MATCH"))
    with open(OUT_RELAX_LOG, "w") as fh:
        json.dump({"n_candidates": len(candidates), "n_decoys_matched": len(matched_rows),
                    "n_short_matches": n_short, "n_relaxed": n_relaxed,
                    "details": relaxation_log}, fh, indent=2)

    print(f"Matched {len(matched_rows)} decoys across {len(candidates)} candidates -> {OUT_MATCHED}")
    print(f"Relaxation needed for {n_relaxed} candidates; {n_short} short matches (see {OUT_RELAX_LOG})")
    if len(matched_rows) != len(candidates) * N_PER_CANDIDATE:
        print(f"WARNING: expected {len(candidates) * N_PER_CANDIDATE} total decoys, got {len(matched_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

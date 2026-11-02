#!/usr/bin/env python3
"""Step 7 of the decoy-panel calibration addendum: blinds and randomly
interleaves the 345 decoys, 69 candidates, and 4 existing controls into a
single docking-order manifest with neutral PMD_#### IDs. The candidates are
included (re-docked fresh in the same blinded batch, not reusing the frozen
primary poses) as an internal consistency check against the frozen 16/69
primary result -- this also controls for the kind of cross-machine GNINA
floating-point drift already documented for this project (the Ambroxol
CNNaffinity reference differed by 0.0009 between two machines in an earlier
sensitivity rerun; Appendix H). The primary decoy-vs-candidate comparison
still uses the frozen 16/69 rate as p_candidate per decoy_addendum_v1.0.md --
the redock is a robustness check, not a replacement.

The candidate/decoy identity mapping is written to a SEPARATE file
(decoy_panel_mapping.csv) that the docking and gate-scoring scripts must
never read. The 4 controls are deliberately NOT blinded (kept as
CTRL_AMBROXOL/CTRL_IFM/CTRL_P9V/CTRL_P8Y): score_candidate_screen.py
hardcodes the literal ID "CTRL_AMBROXOL" to locate the pass/fail CNNaffinity
threshold, and blinding it would silently break scoring. This does not
compromise the blinding's purpose -- the controls are fixed physicochemical
reference standards, not experimental units whose candidate/decoy class
membership needs to be hidden -- but their docking-batch ORDER is still
randomly interleaved along with everything else.

Usage:
    python -m decisionbench_dd_docking.blind_decoy_panel
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREEN_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "candidate_screen_v1.0"
OUT_DIR = SCREEN_DIR / "decoy_panel_v1.0"
CANDIDATE_REF = OUT_DIR / "candidate_reference_v1.0.csv"
MATCHED = OUT_DIR / "property_matched_decoys.csv"
OUT_BLIND_MANIFEST = OUT_DIR / "decoy_panel_candidate_manifest.csv"  # candidate_id,tool,canonical_smiles -- consumable by prepare_candidate_screen_ligands.py
OUT_MAPPING = OUT_DIR / "decoy_panel_mapping.csv"  # SEPARATE, not read by docking/gate scripts

CONTROLS = [
    ("CTRL_AMBROXOL", "control", "C1=C(C(=C(C=C1Br)Br)N)CNC2CCC(CC2)O"),
    ("CTRL_IFM", "control", "C1[C@@H]([C@H]([C@@H](CN1)O)O)CO"),
    ("CTRL_P9V", "control", "CSCC[C@H]1NC[C@@H](O)[C@H](O)[C@H]1O"),
    ("CTRL_P8Y", "control", "CC(C)CCC[S](=O)(=O)C[C@H]1NC[C@@H](O)[C@H](O)[C@H]1O"),
]

RNG_SEED = 1337


def main() -> int:
    cand_df = pd.read_csv(CANDIDATE_REF)
    matched_df = pd.read_csv(MATCHED)

    entries = []  # (true_id, role, tool_or_role, canonical_smiles, extra)
    for _, r in cand_df.iterrows():
        entries.append({"true_id": r["candidate_id"], "role": "candidate", "tool": r["tool"],
                         "canonical_smiles": r["canonical_smiles_isomeric"]})
    for _, r in matched_df.iterrows():
        entries.append({"true_id": r["decoy_chembl_id"], "role": "decoy", "tool": "decoy",
                         "canonical_smiles": r["decoy_canonical_smiles"],
                         "matched_to_candidate": r["candidate_id"], "match_rank": r["match_rank"]})
    rng = np.random.default_rng(RNG_SEED)
    order = rng.permutation(len(entries))  # blinded entries (candidates + decoys) only

    blind_rows = []
    mapping_rows = []
    for rank, idx in enumerate(order, start=1):
        e = entries[idx]
        pmd_id = f"PMD_{rank:04d}"
        blind_rows.append({"candidate_id": pmd_id, "tool": e["tool"], "canonical_smiles": e["canonical_smiles"]})
        mapping_rows.append({
            "blinded_id": pmd_id, "true_id": e["true_id"], "role": e["role"],
            "matched_to_candidate": e.get("matched_to_candidate", ""),
            "match_rank": e.get("match_rank", ""),
        })

    # Controls keep their real IDs (see module docstring); interleave their manifest
    # POSITION randomly among the blinded rows rather than appending them at the end.
    control_entries = [{"true_id": cid, "role": "control", "tool": "control", "canonical_smiles": smi}
                        for cid, role, smi in CONTROLS]
    insert_positions = sorted(rng.integers(0, len(blind_rows) + 1, size=len(control_entries)), reverse=True)
    for pos, e in zip(insert_positions, control_entries):
        blind_rows.insert(pos, {"candidate_id": e["true_id"], "tool": e["tool"], "canonical_smiles": e["canonical_smiles"]})
        mapping_rows.insert(pos, {"blinded_id": e["true_id"], "true_id": e["true_id"], "role": "control",
                                   "matched_to_candidate": "", "match_rank": ""})

    with open(OUT_BLIND_MANIFEST, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["candidate_id", "tool", "canonical_smiles"])
        writer.writeheader()
        writer.writerows(blind_rows)

    with open(OUT_MAPPING, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["blinded_id", "true_id", "role", "matched_to_candidate", "match_rank"])
        writer.writeheader()
        writer.writerows(mapping_rows)

    n_by_role = {}
    for r in mapping_rows:
        n_by_role[r["role"]] = n_by_role.get(r["role"], 0) + 1
    print(f"Blinded {len(blind_rows)} total entries: {n_by_role}")
    print(f"Docking-order manifest (blinded, safe for docking/gate scripts): {OUT_BLIND_MANIFEST}")
    print(f"Identity mapping (NOT for docking/gate scripts): {OUT_MAPPING}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Honest-reporting check, not part of the frozen chemical-qualification
gate itself: how many of the 258 catalogue-arm qualifiers are genuinely
distinct chemical entities vs. stereoisomers/analogs of the same skeleton?

The frozen Morgan/ECFP4 fingerprint (radius 2, 2048 bits, no chirality
flag -- same convention already used everywhere else in this project,
e.g. decisionbench_dd_eval/chem_metrics.py's _morgan_gen) does not
distinguish stereoisomers, so several ZINC entries that are stereoisomers
of one underlying 2D skeleton receive identical similarity/QED/SA/MW/
cLogP/TPSA and can each independently qualify. Reuses this project's own
Murcko-scaffold extraction and the exact greedy single-linkage ECFP4
clustering already applied to the 16 primary GenMol/MolMIM passers
(decisionbench_dd_docking/triage_primary_candidates.py, threshold 0.60),
so the diversity read is apples-to-apples with that existing table.

Usage: python3 scaffold_diversity_check.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold

FPGEN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
CLUSTER_TANIMOTO_THRESHOLD = 0.60


def cluster_by_ecfp4(candidate_ids, fps, threshold=CLUSTER_TANIMOTO_THRESHOLD):
    cluster_of = {}
    cluster_members = []
    for cid in sorted(candidate_ids):
        fp = fps[cid]
        placed = False
        for cluster_id, members in enumerate(cluster_members):
            if any(DataStructs.TanimotoSimilarity(fp, fps[m]) >= threshold for m in members):
                members.append(cid)
                cluster_of[cid] = cluster_id
                placed = True
                break
        if not placed:
            cluster_of[cid] = len(cluster_members)
            cluster_members.append([cid])
    return cluster_of


def main():
    here = Path(__file__).resolve().parent
    rows = list(csv.DictReader((here / "catalogue_candidate_manifest.csv").open()))

    fps = {}
    scaffolds = {}
    for row in rows:
        mol = Chem.MolFromSmiles(row["canonical_smiles"])
        fps[row["candidate_id"]] = FPGEN.GetFingerprint(mol)
        scaffold_mol = MurckoScaffold.GetScaffoldForMol(mol)
        scaffolds[row["candidate_id"]] = Chem.MolToSmiles(scaffold_mol) if scaffold_mol is not None else ""

    candidate_ids = [r["candidate_id"] for r in rows]
    cluster_of = cluster_by_ecfp4(candidate_ids, fps)
    n_clusters = len(set(cluster_of.values()))
    unique_scaffolds = set(scaffolds.values())

    # Group by scaffold to show the stereoisomer-inflation pattern explicitly.
    by_scaffold = {}
    for cid in candidate_ids:
        by_scaffold.setdefault(scaffolds[cid], []).append(cid)
    inflated = {s: ids for s, ids in by_scaffold.items() if len(ids) > 1}

    result = {
        "n_qualified_rows": len(rows),
        "n_distinct_murcko_scaffolds": len(unique_scaffolds),
        "n_ecfp4_clusters_at_0.60_tanimoto": n_clusters,
        "n_scaffolds_with_multiple_qualified_rows": len(inflated),
        "n_rows_that_are_extra_copies_of_an_already_counted_scaffold": len(rows) - len(unique_scaffolds),
        "example_inflated_scaffold_groups": {
            s: ids for s, ids in list(inflated.items())[:5]
        },
    }
    (here / "scaffold_diversity_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

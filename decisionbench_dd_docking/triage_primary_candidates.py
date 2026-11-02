#!/usr/bin/env python3
"""ADMET-adjacent and scaffold-diversity triage of the 16 frozen primary
candidate-screen passers
(decisionbench_dd_configs_v1.0/candidate_screen_v1.0/downstream_gcase_screening_protocol.md,
section 11 "Advancement to ADMET").

Scope, stated plainly rather than implied: this is a physicochemical
drug-likeness and structural-diversity panel built entirely from data this
project already computed (RDKit QED/SA/MW/cLogP/TPSA/HBD/HBA from the
Experiment A generator run, GNINA CNNaffinity/CNNscore/minimizedAffinity
from the candidate screen). It is NOT predictive ADMET -- see
decisionbench_dd_docking/predict_admet.py (ADMET-AI: hERG, AMES, DILI,
BBB/HIA/Caco2/PAMPA permeability, CYP450 inhibition, clearance, half-life,
solubility) for that half of the protocol's "Evaluate ADMET ... and patent
proximity" instruction. The patent-proximity half is
decisionbench_dd_docking/check_patent_membership.py (molbloom/SureChEMBL
exact-structure membership -- see that module's docstring for exactly what
it does and does not establish).

Ranking rule (section 11, applied verbatim, not tuned): CNNaffinity
descending, then CNNscore descending, then minimizedAffinity ascending,
then candidate ID. Since exactly 16 <= 20 candidates pass, all 16 advance
per the protocol's own rule ("If 20 or fewer candidates pass, advance
all.") -- clustering below is reported for chemical-diversity narrative and
downstream selection, not to truncate this population.

Ligand efficiency here is CNNaffinity / heavy-atom count -- an exploratory
proxy (CNNaffinity is GNINA's learned affinity-like score, not an
experimental pKd/pKi), not a validated ligand-efficiency metric.

Usage:
    python -m decisionbench_dd_docking.triage_primary_candidates
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from rdkit import Chem, DataStructs

from decisionbench_dd_eval.chem_metrics import morgan_fingerprint

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREEN_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "candidate_screen_v1.0"
CANDIDATE_MANIFEST = SCREEN_DIR / "candidate_manifest.csv"
CANDIDATE_RESULTS = REPO_ROOT / "candidate_screen_results" / "candidate_results.csv"
POSE_SCORES = REPO_ROOT / "candidate_screen_results" / "pose_scores.csv"
MOLECULE_LEVEL = REPO_ROOT / "results" / "molecule_level.csv"
OUT_DIR = REPO_ROOT / "candidate_screen_results"

CLUSTER_TANIMOTO_THRESHOLD = 0.60


def load_passing_candidates() -> list[dict]:
    with open(CANDIDATE_RESULTS, newline="") as fh:
        # Sorted, not a bare set: set iteration order is not guaranteed
        # stable across Python processes (PYTHONHASHSEED randomization),
        # which was silently making every downstream CSV/table's row order
        # non-reproducible run-to-run despite identical content.
        passing_ids = sorted({r["candidate_id"] for r in csv.DictReader(fh) if r["structural_proxy_pass"] == "True"})

    with open(CANDIDATE_MANIFEST, newline="") as fh:
        manifest = {r["candidate_id"]: r for r in csv.DictReader(fh)}

    with open(POSE_SCORES, newline="") as fh:
        pose_by_id = {r["ligand_id"]: r for r in csv.DictReader(fh) if r["receptor_state"] == "3KEH"}

    with open(MOLECULE_LEVEL, newline="") as fh:
        mol_level_by_smiles = {r["canonical_smiles"]: r for r in csv.DictReader(fh)}

    rows = []
    for cid in passing_ids:
        m = manifest[cid]
        smiles = m["canonical_smiles"]
        pose = pose_by_id[cid]
        mol_props = mol_level_by_smiles.get(smiles)
        mol = Chem.MolFromSmiles(smiles)
        n_heavy = mol.GetNumHeavyAtoms()

        row = {
            "candidate_id": cid,
            "tool": m["tool"],
            "canonical_smiles": smiles,
            "cnnaffinity_3keh": float(pose["top1_cnnaffinity"]),
            "cnnscore_3keh": float(pose["top1_cnnscore"]) if pose.get("top1_cnnscore") else None,
            "minimized_affinity_3keh": float(pose["top1_minimized_affinity"]) if pose.get("top1_minimized_affinity") else None,
            "n_heavy_atoms": n_heavy,
            "ligand_efficiency_proxy": round(float(pose["top1_cnnaffinity"]) / n_heavy, 4),
        }
        if mol_props:
            row.update({
                "qed": round(float(mol_props["qed"]), 4),
                "sa_score": round(float(mol_props["sa_score"]), 4),
                "mw": round(float(mol_props["mw"]), 2),
                "clogp": round(float(mol_props["clogp"]), 3),
                "tpsa": round(float(mol_props["tpsa"]), 2),
                "hbd": int(mol_props["hbd"]),
                "hba": int(mol_props["hba"]),
                "tanimoto_to_ambroxol": round(float(mol_props["tanimoto_to_seed"]), 4),
                "murcko_scaffold_smiles": mol_props["murcko_scaffold_smiles"],
                "lipinski_ro5_violations": sum([
                    float(mol_props["mw"]) > 500,
                    float(mol_props["clogp"]) > 5,
                    int(mol_props["hbd"]) > 5,
                    int(mol_props["hba"]) > 10,
                ]),
            })
        else:
            row.update({k: None for k in (
                "qed", "sa_score", "mw", "clogp", "tpsa", "hbd", "hba",
                "tanimoto_to_ambroxol", "murcko_scaffold_smiles", "lipinski_ro5_violations",
            )})
        rows.append(row)
    return rows


def rank_key(row: dict):
    # Section 11: CNNaffinity desc, CNNscore desc, minimizedAffinity asc, candidate ID.
    return (
        -row["cnnaffinity_3keh"],
        -(row["cnnscore_3keh"] if row["cnnscore_3keh"] is not None else float("-inf")),
        row["minimized_affinity_3keh"] if row["minimized_affinity_3keh"] is not None else float("inf"),
        row["candidate_id"],
    )


def cluster_by_ecfp4(rows: list[dict], threshold: float = CLUSTER_TANIMOTO_THRESHOLD) -> dict[str, int]:
    """Simple greedy single-linkage clustering at the frozen 0.60 ECFP4
    Tanimoto cutoff (protocol section 11's own specified method): each
    candidate joins the first existing cluster with a member above
    threshold, else starts a new cluster. Order-independent for the small
    (n=16) population here; not a tuned/optimal clustering, matching the
    protocol's own simple round-robin-by-cluster intent."""
    fps = {r["candidate_id"]: morgan_fingerprint(r["canonical_smiles"]) for r in rows}
    cluster_of: dict[str, int] = {}
    cluster_members: list[list[str]] = []
    for row in sorted(rows, key=lambda r: r["candidate_id"]):
        cid = row["candidate_id"]
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


def main(argv=None) -> int:
    rows = load_passing_candidates()
    if len(rows) != 16:
        print(f"WARNING: expected 16 primary passers, found {len(rows)}", file=sys.stderr)

    rows.sort(key=rank_key)
    for i, row in enumerate(rows, start=1):
        row["rank"] = i

    cluster_of = cluster_by_ecfp4(rows)
    for row in rows:
        row["ecfp4_cluster_id"] = cluster_of[row["candidate_id"]]
    n_clusters = len(set(cluster_of.values()))

    unique_scaffolds = {r["murcko_scaffold_smiles"] for r in rows if r["murcko_scaffold_smiles"]}

    fieldnames = [
        "rank", "candidate_id", "tool", "canonical_smiles",
        "cnnaffinity_3keh", "cnnscore_3keh", "minimized_affinity_3keh",
        "ligand_efficiency_proxy", "n_heavy_atoms",
        "qed", "sa_score", "mw", "clogp", "tpsa", "hbd", "hba",
        "lipinski_ro5_violations", "tanimoto_to_ambroxol",
        "murcko_scaffold_smiles", "ecfp4_cluster_id",
    ]
    out_csv = OUT_DIR / "primary_candidate_triage.csv"
    with open(out_csv, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# ADMET-adjacent and scaffold-diversity triage: 16 primary candidate-screen passers",
        "",
        "Scope: physicochemical drug-likeness (QED/SA/MW/cLogP/TPSA/HBD/HBA, all already "
        "computed in Experiment A) and structural diversity (Murcko scaffold, ECFP4 "
        "clustering at the protocol's frozen 0.60 Tanimoto cutoff), plus a docking-derived "
        "ligand-efficiency PROXY (CNNaffinity / heavy-atom count -- not a validated LE "
        "metric, since CNNaffinity is a learned score, not experimental pKd/pKi).",
        "",
        "Predictive ADMET (hERG/AMES/DILI/BBB/CYP450/clearance/etc., via ADMET-AI) and an "
        "exact-structure patent-literature/purchasable-catalog membership check (via molbloom/"
        "SureChEMBL) are separate deliverables: see admet_predictions.md and "
        "patent_membership.md. The latter is explicitly NOT a similarity-based patent-"
        "proximity search or a freedom-to-operate opinion -- see that file's own scope note.",
        "",
        f"All 16 candidates advance (protocol section 11: 'If 20 or fewer candidates pass, "
        f"advance all.'). They span {n_clusters} ECFP4 clusters (0.60 Tanimoto cutoff) and "
        f"{len(unique_scaffolds)} distinct Murcko scaffolds -- see primary_candidate_triage.csv "
        "for the full per-candidate table, ranked by CNNaffinity desc / CNNscore desc / "
        "minimizedAffinity asc / candidate ID (protocol section 11's ranking rule).",
        "",
        "| Rank | Candidate | Tool | CNNaffinity | LE proxy | QED | SA | MW | cLogP | Ro5 violations | Scaffold cluster |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in rows:
        lines.append(
            f"| {r['rank']} | {r['candidate_id']} | {r['tool']} | {r['cnnaffinity_3keh']:.3f} | "
            f"{r['ligand_efficiency_proxy']:.3f} | {r['qed']} | {r['sa_score']} | {r['mw']} | "
            f"{r['clogp']} | {r['lipinski_ro5_violations']} | {r['ecfp4_cluster_id']} |"
        )
    (OUT_DIR / "primary_candidate_triage.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv} and primary_candidate_triage.md ({len(rows)} candidates, {n_clusters} clusters, {len(unique_scaffolds)} scaffolds)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

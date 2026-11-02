#!/usr/bin/env python3
"""Catalogue/purchasable-library similarity-search baseline (Level 1 only:
chemical qualification, no docking). See CATALOGUE_BASELINE_SCOPE_v1.0.md
for the full design rationale and the pre-specified selection rule this
script implements exactly.

Reuses the frozen seed, ECFP4/Morgan fingerprint definition, PAINS/Brenk
catalogs, and gate functions from build_candidate_manifest.py (imported,
not reimplemented) so the catalogue arm is evaluated against the byte-
identical v1.2 chemical contract already applied to GenMol and MolMIM.

Source: ZINC (files.docking.org) 2D tranches, reactivity in {A,B,C,E}
(anodyne/bother/clean/mild -- ZINC's own historical "Mild" default tier,
progressively inclusive), purchasability in {A,B} ("in stock"), restricted
to the MW-row letters B-K (200 Da to unbounded-above-500, later filtered
to <=550 by recomputed MW) and LogP-column letters C-J (0 to 5), i.e. the
80 first-level tranches whose stated ranges overlap this project's own
frozen MW [200,550] / cLogP [0,5] windows exactly. Tranche boundaries are
used ONLY to bound which files are worth downloading -- every accept/
reject decision below is made by recomputing MW/cLogP/etc. with this
project's own RDKit pipeline, never by trusting ZINC's tranche assignment
or its own deduplication.

Usage (run from this directory, after zinc_tranches/*.smi are downloaded):
    python3 build_catalogue_baseline.py
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rdkit import Chem, DataStructs, rdBase
from rdkit.Chem import Crippen, Descriptors, rdMolDescriptors, QED
from rdkit.Contrib.SA_Score import sascorer

import build_candidate_manifest as bcm

SEED_SMILES = bcm.SEED_SMILES
SEED_CANONICAL = bcm.SEED_CANONICAL
SEED_FP = bcm.SEED_FP
FPGEN = bcm.FPGEN
PAINS = bcm.PAINS
brenk_alerts = bcm.brenk_alerts
inherited_alert_pass = bcm.inherited_alert_pass

TRANCHE_DIR = Path(__file__).resolve().parent / "zinc_tranches"
OUT_DIR = Path(__file__).resolve().parent
TOP_N = 300
SIM_MIN_INCLUSIVE = 0.30
SIM_MAX_EXCLUSIVE = 0.95


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_and_dedup_by_similarity():
    """Stream every tranche file, canonicalize with this project's own
    RDKit settings, globally deduplicate by canonical SMILES (first
    occurrence retained; ZINC's own per-file dedup is not trusted), score
    ECFP4 Tanimoto similarity to the seed, and keep a running top-TOP_N
    pool restricted to the pre-specified similarity band. Returns the
    ranked top-300 list and bookkeeping counts for the funnel.
    """
    seen_canonical = {}  # canonical_smiles -> (zinc_id, source_file)
    in_band = []  # (similarity, zinc_id, canonical_smiles, source_file)
    n_lines = 0
    n_parse_ok = 0
    n_new_canonical = 0
    n_in_band = 0

    files = sorted(TRANCHE_DIR.glob("*.smi"))
    if not files:
        raise RuntimeError(f"No .smi files found in {TRANCHE_DIR}")

    for i, path in enumerate(files, start=1):
        with path.open() as handle:
            header = handle.readline()  # "smiles zinc_id"
            for line in handle:
                n_lines += 1
                parts = line.split()
                if len(parts) < 2:
                    continue
                raw_smiles, zinc_id = parts[0], parts[1]
                mol = Chem.MolFromSmiles(raw_smiles)
                if mol is None:
                    continue
                n_parse_ok += 1
                canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
                if canonical in seen_canonical:
                    continue
                seen_canonical[canonical] = (zinc_id, path.name)
                n_new_canonical += 1
                if canonical == SEED_CANONICAL:
                    continue
                similarity = DataStructs.TanimotoSimilarity(SEED_FP, FPGEN.GetFingerprint(mol))
                if SIM_MIN_INCLUSIVE <= similarity < SIM_MAX_EXCLUSIVE:
                    n_in_band += 1
                    in_band.append((similarity, zinc_id, canonical, path.name))
        if i % 40 == 0 or i == len(files):
            print(
                f"  [{i}/{len(files)} files] lines={n_lines} parsed={n_parse_ok} "
                f"unique_canonical={n_new_canonical} in_band={n_in_band}",
                flush=True,
            )

    # Deterministic ranking: similarity descending, ZINC ID ascending as tiebreak.
    in_band.sort(key=lambda row: (-row[0], row[1]))
    top = in_band[:TOP_N]
    return top, {
        "raw_lines_all_tranches": n_lines,
        "rdkit_parseable": n_parse_ok,
        "unique_by_project_canonical_smiles": n_new_canonical,
        "in_similarity_band_before_top300_cut": n_in_band,
        "top_n_taken": len(top),
    }


def evaluate_catalogue(top):
    """Run the pre-specified top-300 catalogue hits through the remaining
    frozen v1.2 gate sequence (everything after the similarity band, which
    was already applied during selection above), reusing the identical
    per-molecule checks build_candidate_manifest.py applies to GenMol and
    MolMIM.
    """
    stage_order = [
        "valid", "unique", "not_exact_seed", "similarity_band_0.30_to_0.95",
        "qed", "sa_score", "molecular_weight", "clogp", "tpsa", "no_pains",
        "chemically_qualified",
    ]
    audit = []
    qualified = []
    counts = {stage: 0 for stage in stage_order}

    for similarity, zinc_id, canonical, source_file in top:
        mol = Chem.MolFromSmiles(canonical)
        row = {
            "zinc_id": zinc_id,
            "source_tranche_file": source_file,
            "canonical_smiles": canonical,
            "ecfp4_tanimoto": similarity,
        }
        row.update({stage: False for stage in stage_order})
        row["failed_at"] = ""

        # valid / unique / not_exact_seed / similarity band are true by
        # construction of `top` (parsed, deduplicated, non-seed, in-band);
        # recorded here for audit-column parity with the generator funnel.
        row["valid"] = True
        counts["valid"] += 1
        row["unique"] = True
        counts["unique"] += 1
        row["not_exact_seed"] = True
        counts["not_exact_seed"] += 1
        row["similarity_band_0.30_to_0.95"] = True
        counts["similarity_band_0.30_to_0.95"] += 1

        qed = QED.qed(mol)
        sa = sascorer.calculateScore(mol)
        mw = Descriptors.MolWt(mol)
        clogp = Crippen.MolLogP(mol)
        tpsa = rdMolDescriptors.CalcTPSA(mol)
        alerts = brenk_alerts(mol)
        row.update({
            "qed_value": qed, "sa_value": sa, "mw_da": mw,
            "clogp_value": clogp, "tpsa_a2": tpsa,
            "brenk_alerts": ";".join(alerts),
        })

        checks = [
            ("qed", qed >= 0.50),
            ("sa_score", sa <= 5.0),
            ("molecular_weight", 200 <= mw <= 550),
            ("clogp", 0 <= clogp <= 5),
            ("tpsa", tpsa <= 100),
            ("no_pains", not PAINS.HasMatch(mol)),
        ]
        failed = False
        for stage, passed in checks:
            if not passed:
                row["failed_at"] = stage
                failed = True
                break
            row[stage] = True
            counts[stage] += 1
        if failed:
            audit.append(row)
            continue

        if not inherited_alert_pass(mol, alerts):
            row["failed_at"] = "new_brenk_alert"
            audit.append(row)
            continue

        row["chemically_qualified"] = True
        counts["chemically_qualified"] += 1
        qualified.append(row)
        audit.append(row)

    return audit, qualified, counts


def cross_check_existing_pool(qualified):
    """Flag any catalogue qualifier that is an exact-structure match to one
    of the existing 69 frozen GenMol/MolMIM chemical qualifiers, so it is
    not silently double-counted as a novel catalogue-only qualifier."""
    existing_path = OUT_DIR.parent / "candidate_manifest.csv"
    existing_smiles = set()
    if existing_path.exists():
        with existing_path.open() as handle:
            for row in csv.DictReader(handle):
                existing_smiles.add(row["canonical_smiles"])
    overlap = [row for row in qualified if row["canonical_smiles"] in existing_smiles]
    return overlap, len(existing_smiles)


def main():
    print("Loading tranche files, canonicalizing, scoring similarity to seed...")
    top, load_counts = load_and_dedup_by_similarity()
    print(f"Top-{TOP_N} selection complete: {load_counts}")

    print("Evaluating remaining frozen chemical gates on the top-300...")
    audit, qualified, gate_counts = evaluate_catalogue(top)

    overlap, existing_pool_size = cross_check_existing_pool(qualified)

    for index, row in enumerate(qualified, start=1):
        row["candidate_id"] = f"ZC_{index:03d}"

    audit_fields = [
        "zinc_id", "source_tranche_file", "canonical_smiles", "ecfp4_tanimoto",
        "qed_value", "sa_value", "mw_da", "clogp_value", "tpsa_a2", "brenk_alerts",
        "failed_at", "valid", "unique", "not_exact_seed",
        "similarity_band_0.30_to_0.95", "qed", "sa_score", "molecular_weight",
        "clogp", "tpsa", "no_pains", "chemically_qualified",
    ]
    candidate_fields = ["candidate_id"] + audit_fields

    with (OUT_DIR / "catalogue_gate_audit.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=audit_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(audit)

    with (OUT_DIR / "catalogue_candidate_manifest.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=candidate_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(qualified)

    summary = {
        "schema_version": "DecisionBench-DD_catalogue_baseline_v1.0",
        "level": "1 (chemical qualification only; no docking run in this script)",
        "seed_smiles": SEED_SMILES,
        "seed_canonical_smiles": SEED_CANONICAL,
        "rdkit_version": rdBase.rdkitVersion,
        "source": "ZINC (files.docking.org/2D), reactivity A/B/C/E, purchasability A/B (in stock)",
        "selection_rule": (
            f"top {TOP_N} by ECFP4/Morgan Tanimoto similarity to seed (radius 2, "
            f"2048 bits), descending, ties broken by ZINC ID ascending, restricted "
            f"to [{SIM_MIN_INCLUSIVE}, {SIM_MAX_EXCLUSIVE}) -- pre-specified and "
            f"frozen in CATALOGUE_BASELINE_SCOPE_v1.0.md before this script was run"
        ),
        "requested": TOP_N,
        "load_and_selection_counts": load_counts,
        "gate_stage_counts": gate_counts,
        "qualified_unique": len(qualified),
        "qualified_yield_of_requested": len(qualified) / TOP_N,
        "overlap_with_existing_69_candidate_pool": {
            "existing_pool_size": existing_pool_size,
            "n_catalogue_qualifiers_also_in_existing_pool": len(overlap),
            "overlapping_canonical_smiles": [row["canonical_smiles"] for row in overlap],
        },
        "gates": bcm_gates_snapshot(),
    }
    (OUT_DIR / "catalogue_manifest_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(json.dumps(summary, indent=2))


def bcm_gates_snapshot():
    return {
        "valid": "RDKit MolFromSmiles succeeds",
        "deduplication": "globally across all downloaded tranches, by this project's own isomeric canonical SMILES; first occurrence retained (ZINC's own dedup/property metadata not trusted)",
        "not_exact_seed": True,
        "ecfp4": {"radius": 2, "n_bits": 2048, "tanimoto_min_inclusive": SIM_MIN_INCLUSIVE, "tanimoto_max_exclusive": SIM_MAX_EXCLUSIVE},
        "qed_min_inclusive": 0.50,
        "sa_max_inclusive": 5.0,
        "mw_da": [200, 550],
        "clogp": [0, 5],
        "tpsa_a2_max_inclusive": 100,
        "pains": "none",
        "brenk": "only the single seed-position dibrominated-core aniline occurrence is allowlisted",
    }


if __name__ == "__main__":
    main()

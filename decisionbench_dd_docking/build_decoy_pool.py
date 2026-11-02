#!/usr/bin/env python3
"""Steps 3-4 of the decoy-panel calibration addendum: filters the ChEMBL 37
chemreps source pool down to an eligible, property-range-restricted,
similarity-excluded background pool for 5:1 matching against the 69 frozen
chemical qualifiers.

Staged for tractability against ~2.4M source rows:
  Stage A (cheap, string-level): single organic fragment, no metals/unwanted
    elements, plausible size, no obvious salts/mixtures.
  Stage B (RDKit): sanitize + compute the full property set (same functions/
    fingerprint config as build_decoy_candidate_reference.py).
  Stage C: restrict to the union of the 69 candidates' property envelope
    under the WIDEST relaxation the matching protocol allows (so nothing
    useful for matching is discarded here, but the far tail of chemical
    space is dropped before the expensive similarity step).
  Stage D: exclude by ECFP4 Tanimoto similarity to any of the 69 candidates
    (>=0.35) or to Ambroxol (>=0.30); exclude exact-SMILES matches to the
    candidates/Ambroxol/four controls.

Usage:
    python -m decisionbench_dd_docking.build_decoy_pool --chemreps <path to chembl_37_chemreps.txt.gz>
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
from pathlib import Path

from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import Descriptors, Lipinski, rdMolDescriptors

from decisionbench_dd_eval.chem_metrics import canonicalize, morgan_fingerprint

RDLogger.DisableLog("rdApp.*")

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREEN_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "candidate_screen_v1.0"
OUT_DIR = SCREEN_DIR / "decoy_panel_v1.0"
CANDIDATE_REF = OUT_DIR / "candidate_reference_v1.0.csv"
OUT_ELIGIBLE = OUT_DIR / "eligible_pool_v1.0.csv"
OUT_LOG = OUT_DIR / "decoy_pool_filter_log.json"

ALLOWED_ELEMENTS = {"C", "H", "N", "O", "S", "P", "F", "Cl", "Br", "I"}
AMBROXOL_SMILES = "C1=C(C(=C(C=C1Br)Br)N)CNC2CCC(CC2)O"
CONTROL_SMILES = {
    "CTRL_AMBROXOL": AMBROXOL_SMILES,
    "CTRL_IFM": "C1[C@@H]([C@H]([C@@H](CN1)O)O)CO",
    "CTRL_P9V": "CSCC[C@H]1NC[C@@H](O)[C@H](O)[C@H]1O",
    "CTRL_P8Y": "CC(C)CCC[S](=O)(=O)C[C@H]1NC[C@@H](O)[C@H](O)[C@H]1O",
}

SIM_EXCLUDE_CANDIDATE = 0.35
SIM_EXCLUDE_AMBROXOL = 0.30

# Stage C envelope: outer bound across the widest caliper relaxation the
# matching protocol allows (MW +/-15%, TPSA +/-15, cLogP +/-0.75, HAC +/-2),
# applied around the 69 candidates' own [min,max], not per-candidate --
# this is a coarse prefilter only; per-candidate caliper matching happens later.


def load_candidate_envelope() -> dict:
    with open(CANDIDATE_REF, newline="") as fh:
        rows = list(csv.DictReader(fh))
    mw = [float(r["mw"]) for r in rows]
    hac = [int(r["hac"]) for r in rows]
    clogp = [float(r["clogp"]) for r in rows]
    tpsa = [float(r["tpsa"]) for r in rows]
    return {
        "mw_lo": min(mw) * 0.85, "mw_hi": max(mw) * 1.15,
        "hac_lo": min(hac) - 2, "hac_hi": max(hac) + 2,
        "clogp_lo": min(clogp) - 0.75, "clogp_hi": max(clogp) + 0.75,
        "tpsa_lo": max(0.0, min(tpsa) - 15), "tpsa_hi": max(tpsa) + 15,
    }


def load_candidate_fps():
    with open(CANDIDATE_REF, newline="") as fh:
        rows = list(csv.DictReader(fh))
    fps = [morgan_fingerprint(r["canonical_smiles_isomeric"]) for r in rows]
    exact_smiles = {r["canonical_smiles_isomeric"] for r in rows}
    return fps, exact_smiles


def stage_a_cheap_filter(smiles: str) -> bool:
    if not smiles or "." in smiles:  # multi-fragment / salt
        return False
    if len(smiles) > 120 or len(smiles) < 8:
        return False
    return True


def stage_b_sanitize_and_props(smiles: str):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    frags = Chem.GetMolFrags(mol)
    if len(frags) != 1:
        return None
    elements = {atom.GetSymbol() for atom in mol.GetAtoms()}
    if not elements.issubset(ALLOWED_ELEMENTS):
        return None
    if Chem.GetFormalCharge(mol) != 0:
        return None
    canon = Chem.MolToSmiles(mol)
    return {
        "canonical_smiles": canon,
        "mw": Descriptors.MolWt(mol),
        "hac": mol.GetNumHeavyAtoms(),
        "clogp": Descriptors.MolLogP(mol),
        "tpsa": rdMolDescriptors.CalcTPSA(mol),
        "hbd": Lipinski.NumHDonors(mol),
        "hba": Lipinski.NumHAcceptors(mol),
        "rotatable_bonds": Lipinski.NumRotatableBonds(mol),
        "formal_charge": 0,
        "ring_count": rdMolDescriptors.CalcNumRings(mol),
        "aromatic_ring_count": rdMolDescriptors.CalcNumAromaticRings(mol),
        "halogen_count": sum(1 for a in mol.GetAtoms() if a.GetSymbol() in {"F", "Cl", "Br", "I"}),
    }


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--chemreps", type=Path, required=True, help="Path to chembl_XX_chemreps.txt(.gz)")
    p.add_argument("--limit", type=int, default=None, help="Optional cap on source rows scanned (debugging)")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    envelope = load_candidate_envelope()
    candidate_fps, exact_exclude_smiles = load_candidate_fps()
    ambroxol_fp = morgan_fingerprint(canonicalize(AMBROXOL_SMILES))
    exact_exclude_smiles |= {canonicalize(s) for s in CONTROL_SMILES.values()}

    opener = gzip.open if str(args.chemreps).endswith(".gz") else open
    counts = {
        "source_rows": 0, "stage_a_pass": 0, "stage_b_parsed": 0,
        "stage_c_in_envelope": 0, "excluded_exact_match": 0,
        "excluded_sim_to_candidate": 0, "excluded_sim_to_ambroxol": 0,
        "eligible_final": 0,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with opener(args.chemreps, "rt", encoding="utf-8", errors="replace") as fh, \
         open(OUT_ELIGIBLE, "w", newline="") as out_fh:
        reader = csv.reader(fh, delimiter="\t")
        header = next(reader)
        # chembl_id, canonical_smiles, standard_inchi, standard_inchi_key
        writer = csv.writer(out_fh)
        writer.writerow(["chembl_id", "canonical_smiles", "mw", "hac", "clogp", "tpsa",
                          "hbd", "hba", "rotatable_bonds", "formal_charge",
                          "ring_count", "aromatic_ring_count", "halogen_count"])

        for i, row in enumerate(reader):
            if args.limit and i >= args.limit:
                break
            counts["source_rows"] += 1
            if len(row) < 2:
                continue
            chembl_id, smiles = row[0], row[1]
            if not stage_a_cheap_filter(smiles):
                continue
            counts["stage_a_pass"] += 1

            props = stage_b_sanitize_and_props(smiles)
            if props is None:
                continue
            counts["stage_b_parsed"] += 1

            if not (envelope["mw_lo"] <= props["mw"] <= envelope["mw_hi"]
                    and envelope["hac_lo"] <= props["hac"] <= envelope["hac_hi"]
                    and envelope["clogp_lo"] <= props["clogp"] <= envelope["clogp_hi"]
                    and envelope["tpsa_lo"] <= props["tpsa"] <= envelope["tpsa_hi"]):
                continue
            counts["stage_c_in_envelope"] += 1

            if props["canonical_smiles"] in exact_exclude_smiles:
                counts["excluded_exact_match"] += 1
                continue

            fp = morgan_fingerprint(props["canonical_smiles"])
            sims = DataStructs.BulkTanimotoSimilarity(fp, candidate_fps)
            if max(sims) >= SIM_EXCLUDE_CANDIDATE:
                counts["excluded_sim_to_candidate"] += 1
                continue
            if DataStructs.TanimotoSimilarity(fp, ambroxol_fp) >= SIM_EXCLUDE_AMBROXOL:
                counts["excluded_sim_to_ambroxol"] += 1
                continue

            counts["eligible_final"] += 1
            writer.writerow([chembl_id, props["canonical_smiles"], round(props["mw"], 4),
                              props["hac"], round(props["clogp"], 4), round(props["tpsa"], 4),
                              props["hbd"], props["hba"], props["rotatable_bonds"],
                              props["formal_charge"], props["ring_count"],
                              props["aromatic_ring_count"], props["halogen_count"]])

            if counts["source_rows"] % 200000 == 0:
                print(f"  ...scanned {counts['source_rows']:,} source rows, "
                      f"{counts['eligible_final']:,} eligible so far", file=sys.stderr)

    with open(OUT_LOG, "w") as fh:
        json.dump({
            "candidate_envelope_used_for_stage_c": envelope,
            "similarity_exclusion_thresholds": {
                "vs_any_candidate_ecfp4_tanimoto_gte": SIM_EXCLUDE_CANDIDATE,
                "vs_ambroxol_ecfp4_tanimoto_gte": SIM_EXCLUDE_AMBROXOL,
            },
            "allowed_elements": sorted(ALLOWED_ELEMENTS),
            "stage_counts": counts,
        }, fh, indent=2)

    print(json.dumps(counts, indent=2))
    print(f"Wrote eligible pool to {OUT_ELIGIBLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

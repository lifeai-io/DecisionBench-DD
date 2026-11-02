#!/usr/bin/env python3
"""Step 2 of the post-hoc decoy-panel calibration addendum (decoy_addendum_v1.0.md):
builds the frozen 69-candidate reference set (66 GenMol + 3 primary MolMIM chemical
qualifiers) with the full property set needed for 5:1 matching, computed with the
same RDKit version/canonicalization used by the frozen chemical-gate audit
(decisionbench_dd_eval/chem_metrics.py:canonicalize, morgan_fingerprint).

Does NOT touch the frozen candidate_manifest.csv -- reads it, writes a new enriched
file alongside it under decoy_panel_v1.0/.

Usage:
    python -m decisionbench_dd_docking.build_decoy_candidate_reference
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, rdMolDescriptors

from decisionbench_dd_eval.chem_metrics import canonicalize, morgan_fingerprint

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREEN_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "candidate_screen_v1.0"
CANDIDATE_MANIFEST = SCREEN_DIR / "candidate_manifest.csv"
OUT_DIR = SCREEN_DIR / "decoy_panel_v1.0"
OUT_CSV = OUT_DIR / "candidate_reference_v1.0.csv"

HALOGENS = {"F", "Cl", "Br", "I"}

FIELDS = [
    "candidate_id", "tool", "canonical_smiles_isomeric",
    "mw", "hac", "clogp", "tpsa", "hbd", "hba", "rotatable_bonds",
    "formal_charge", "ring_count", "aromatic_ring_count", "halogen_count",
    "ecfp4_bits_set",  # sorted list of set-bit indices, json-encoded (sparse repr of the 2048-bit ECFP4)
]


def compute_row(candidate_id: str, tool: str, raw_smiles: str) -> dict:
    canon = canonicalize(raw_smiles)
    if canon is None:
        raise ValueError(f"{candidate_id}: canonical_smiles {raw_smiles!r} failed to parse with the frozen canonicalize()")
    mol = Chem.MolFromSmiles(canon)
    fp = morgan_fingerprint(canon)
    on_bits = sorted(fp.GetOnBits())

    halogen_count = sum(1 for atom in mol.GetAtoms() if atom.GetSymbol() in HALOGENS)

    return {
        "candidate_id": candidate_id,
        "tool": tool,
        "canonical_smiles_isomeric": canon,
        "mw": round(Descriptors.MolWt(mol), 4),
        "hac": mol.GetNumHeavyAtoms(),
        "clogp": round(Descriptors.MolLogP(mol), 4),
        "tpsa": round(rdMolDescriptors.CalcTPSA(mol), 4),
        "hbd": Lipinski.NumHDonors(mol),
        "hba": Lipinski.NumHAcceptors(mol),
        "rotatable_bonds": Lipinski.NumRotatableBonds(mol),
        "formal_charge": Chem.GetFormalCharge(mol),
        "ring_count": rdMolDescriptors.CalcNumRings(mol),
        "aromatic_ring_count": rdMolDescriptors.CalcNumAromaticRings(mol),
        "halogen_count": halogen_count,
        "ecfp4_bits_set": json.dumps(on_bits),
    }


def main() -> int:
    with open(CANDIDATE_MANIFEST, newline="") as fh:
        candidates = list(csv.DictReader(fh))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [compute_row(c["candidate_id"], c["tool"], c["canonical_smiles"]) for c in candidates]

    with open(OUT_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    n_genmol = sum(1 for r in rows if r["tool"] == "genmol")
    n_molmim = sum(1 for r in rows if r["tool"] == "molmim")
    print(f"Wrote {len(rows)} candidates ({n_genmol} GenMol, {n_molmim} MolMIM) to {OUT_CSV}")
    if len(rows) != 69 or n_genmol != 66 or n_molmim != 3:
        print(f"WARNING: expected 69 (66 GenMol + 3 MolMIM), got {len(rows)} ({n_genmol}+{n_molmim})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

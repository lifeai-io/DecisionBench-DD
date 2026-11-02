#!/usr/bin/env python3
"""Prepares ligand microstates for the candidate-screen experiment
(decisionbench_dd_configs_v1.0/candidate_screen_v1.0/downstream_gcase_screening_protocol.md,
section 5).

For each of the 69 chemically-qualified generated candidates
(candidate_manifest.csv) plus 4 controls (Ambroxol, isofagomine/IFM, P9V,
P8Y), prepares one dominant microspecies at pH 7.4 (matched to the 3KEH
neutral-state receptor) and one at pH 5.4 (matched to the 3KE0 acidic-state
receptor), using the exact same protonation-selection machinery as the
corrected 14-case redocking run (decisionbench_dd_docking/prepare_ligands.py:
dimorphite-dl enumeration + BAD_SULFONAMIDE_CHARGE-excluding pick_variant),
just parameterized over two pH values instead of one.

Per the protocol: if no single dominant microspecies can be assigned (no
valid dimorphite-dl variant at all), the molecule is flagged
microstate_ambiguous=true but stays in the primary denominator; only its
pH-difference result is excluded from interpretation (handled downstream in
score_candidate_screen.py, not here).

Usage:
    python -m decisionbench_dd_docking.prepare_candidate_screen_ligands
    # or, for a separate candidate set (e.g. the MolMIM min_similarity sensitivity
    # rerun) without touching the frozen primary manifest/ligand directory:
    python -m decisionbench_dd_docking.prepare_candidate_screen_ligands \\
        --candidate-manifest decisionbench_dd_configs_v1.0/candidate_screen_v1.0/sensitivity_rerun/candidate_manifest.csv \\
        --ligand-dir decisionbench_dd_configs_v1.0/candidate_screen_v1.0/sensitivity_rerun/docking_input_ligands \\
        --out-csv decisionbench_dd_configs_v1.0/candidate_screen_v1.0/sensitivity_rerun/ligand_microstate_manifest.csv \\
        --no-controls
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from dimorphite_dl import protonate_smiles
from rdkit import Chem

from decisionbench_dd_docking.prepare_ligands import embed_ligand, pick_variant

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREEN_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "candidate_screen_v1.0"
CANDIDATE_MANIFEST = SCREEN_DIR / "candidate_manifest.csv"
LIGAND_DIR = SCREEN_DIR / "docking_input_ligands"

PH_STATES = [("3KEH", 7.4), ("3KE0", 5.4)]

CONTROLS = [
    # control_id, tool, neutral input SMILES (same convention as
    # docking_input_smiles for the 14-case set: pre-protonation, as deposited
    # / as used elsewhere in this project -- NOT the candidate/gate SMILES).
    ("CTRL_AMBROXOL", "control", "C1=C(C(=C(C=C1Br)Br)N)CNC2CCC(CC2)O"),
    ("CTRL_IFM", "control", "C1[C@@H]([C@H]([C@@H](CN1)O)O)CO"),
    ("CTRL_P9V", "control", "CSCC[C@H]1NC[C@@H](O)[C@H](O)[C@H]1O"),
    ("CTRL_P8Y", "control", "CC(C)CCC[S](=O)(=O)C[C@H]1NC[C@@H](O)[C@H](O)[C@H]1O"),
]


def load_candidates(candidate_manifest: Path) -> list[tuple[str, str, str]]:
    with open(candidate_manifest, newline="") as fh:
        rows = list(csv.DictReader(fh))
    return [(r["candidate_id"], r["tool"], r["canonical_smiles"]) for r in rows]


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--candidate-manifest", type=Path, default=CANDIDATE_MANIFEST, help="candidate_id,tool,canonical_smiles CSV (default: frozen primary 69-candidate manifest)")
    p.add_argument("--ligand-dir", type=Path, default=LIGAND_DIR, help="Output directory for prepared SDFs (default: frozen primary docking_input_ligands/)")
    p.add_argument("--out-csv", type=Path, default=None, help="Output ligand_microstate_manifest.csv path (default: alongside --candidate-manifest's parent, ligand_microstate_manifest.csv)")
    p.add_argument("--no-controls", action="store_true", help="Skip the 4 frozen controls (Ambroxol/IFM/P9V/P8Y) -- only use when reusing another run's control poses")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    ligand_dir = args.ligand_dir.resolve()
    out_csv = args.out_csv if args.out_csv is not None else args.candidate_manifest.parent / "ligand_microstate_manifest.csv"

    ligands = load_candidates(args.candidate_manifest) + ([] if args.no_controls else CONTROLS)
    ligand_dir.mkdir(parents=True, exist_ok=True)

    report = []
    for ligand_id, tool, input_smiles in ligands:
        for receptor_state, ph in PH_STATES:
            variants = protonate_smiles(input_smiles, ph_min=ph, ph_max=ph)
            chosen, flag = pick_variant(variants)
            microstate_ambiguous = chosen is None

            row = {
                "ligand_id": ligand_id,
                "tool": tool,
                "receptor_state": receptor_state,
                "ph": ph,
                "input_smiles": input_smiles,
                "n_variants": len(variants),
                "selection_flag": flag,
                "protonated_smiles": chosen,
                "formal_charge": None,
                "embed_ok": False,
                "mmff_converged": False,
                "microstate_ambiguous": microstate_ambiguous,
                "ligand_file": None,
            }

            if not microstate_ambiguous:
                mol = Chem.MolFromSmiles(chosen)
                row["formal_charge"] = Chem.GetFormalCharge(mol)
                out_sdf = ligand_dir / f"{ligand_id}_{receptor_state}.sdf"
                embed_ok, mmff_ok = embed_ligand(chosen, out_sdf)
                row["embed_ok"] = embed_ok
                row["mmff_converged"] = mmff_ok
                row["ligand_file"] = str(out_sdf.relative_to(SCREEN_DIR))
                if not embed_ok:
                    print(f"WARNING [{ligand_id}/{receptor_state}]: 3D embedding failed", file=sys.stderr)
            else:
                print(f"WARNING [{ligand_id}/{receptor_state}]: no valid protonation variant ({flag}) -- microstate_ambiguous=true", file=sys.stderr)

            report.append(row)
            status = "AMBIGUOUS" if microstate_ambiguous else ("OK" if row["embed_ok"] else "EMBED_FAILED")
            print(f"[{ligand_id}/{receptor_state}] {status}: {chosen}")

    fields = [
        "ligand_id", "tool", "receptor_state", "ph", "input_smiles", "n_variants",
        "selection_flag", "protonated_smiles", "formal_charge", "embed_ok",
        "mmff_converged", "microstate_ambiguous", "ligand_file",
    ]
    with open(out_csv, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report)

    n_ambiguous = sum(1 for r in report if r["microstate_ambiguous"])
    n_embed_failed = sum(1 for r in report if not r["microstate_ambiguous"] and not r["embed_ok"])
    print(f"\nWrote {len(report)} rows to {out_csv}")
    print(f"{n_ambiguous} microstate_ambiguous, {n_embed_failed} embed failures (of {len(report)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

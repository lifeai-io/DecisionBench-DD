#!/usr/bin/env python3
"""Tests whether the primary 14-complex GCase redocking benchmark
(decisionbench_dd_configs_v1.0/gcase_validation/) shares the RDKit ETKDGv3
ligand-embedding non-determinism found in the decoy panel (candidate GM_009:
identical SMILES/atom count, starting-conformer coordinates differing by up
to 1.70 A between two separate `prepare_ligands.py` invocations, despite a
fixed randomSeed=42).

Reuses `pick_variant` and `embed_ligand` from prepare_ligands.py UNCHANGED
(same protonation-selection and ETKDGv3 logic that produced the frozen
inputs) but writes fresh output to a new directory and never touches the
frozen `docking_input_ligands/`, `reference_ligands/`, or
`gcase_validation_set_v1.0.json` -- this is a read-only diagnostic against
the frozen case list, not a re-preparation.

DiffDock-L is out of scope for this check: it consumes the case's
`docking_input_protonated_smiles` (a bare SMILES string) directly and never
sees RDKit's embedded conformer at all (redocking_protocol_v1.0.json:
"DiffDock generates its own 3D pose, crystal coordinates are never
supplied"), so this specific embedding-reproducibility risk cannot transfer
to the DiffDock-L arm. Only GNINA's `-l` input is a function of the embedded
conformer, so only GNINA needs a redocking rerun once this diagnostic runs.

Usage:
    python -m decisionbench_dd_docking.redocking_reembed_rerun
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from rdkit import Chem
from dimorphite_dl import protonate_smiles

from decisionbench_dd_docking.prepare_ligands import GCASE_DIR, PH, embed_ligand, pick_variant

REPO_ROOT = Path(__file__).resolve().parent.parent
CASE_LIST_PATH = GCASE_DIR / "gcase_validation_set_v1.0.json"
RERUN_DIR = GCASE_DIR / "redocking_rerun_v1.0"
RERUN_LIGAND_DIR = RERUN_DIR / "docking_input_ligands"


def max_coord_delta(frozen_path: Path, rerun_path: Path) -> tuple[float | None, float | None, str | None]:
    """Returns (max_delta_all_atoms, max_delta_heavy_atoms, note). None/None
    if the two files don't have matching atom counts (a same-atom-count
    check first, per rmsd.py's own documented reason a mismatch here breaks
    downstream comparisons)."""
    frozen_mol = Chem.SDMolSupplier(str(frozen_path), removeHs=False)[0]
    rerun_mol = Chem.SDMolSupplier(str(rerun_path), removeHs=False)[0]
    if frozen_mol is None or rerun_mol is None:
        return None, None, "unparseable_sdf"
    if frozen_mol.GetNumAtoms() != rerun_mol.GetNumAtoms():
        return None, None, f"atom_count_mismatch ({frozen_mol.GetNumAtoms()} vs {rerun_mol.GetNumAtoms()})"

    frozen_conf = frozen_mol.GetConformer()
    rerun_conf = rerun_mol.GetConformer()
    max_all = 0.0
    max_heavy = 0.0
    for i in range(frozen_mol.GetNumAtoms()):
        p0, p1 = frozen_conf.GetAtomPosition(i), rerun_conf.GetAtomPosition(i)
        d = ((p0.x - p1.x) ** 2 + (p0.y - p1.y) ** 2 + (p0.z - p1.z) ** 2) ** 0.5
        max_all = max(max_all, d)
        if frozen_mol.GetAtomWithIdx(i).GetAtomicNum() > 1:
            max_heavy = max(max_heavy, d)
    return max_all, max_heavy, None


def main(argv=None) -> int:
    with open(CASE_LIST_PATH) as fh:
        cases = json.load(fh)["cases"]

    RERUN_LIGAND_DIR.mkdir(parents=True, exist_ok=True)
    report = []
    for case in cases:
        pdb_id = case["pdb_id"]
        frozen_smiles = case["docking_input_protonated_smiles"]
        variants = protonate_smiles(case["docking_input_smiles"], ph_min=PH, ph_max=PH)
        chosen, flag = pick_variant(variants)
        if chosen is None:
            print(f"ERROR [{pdb_id}]: {flag}", file=sys.stderr)
            return 1

        rerun_sdf = RERUN_LIGAND_DIR / f"{pdb_id}_ligand_input.sdf"
        embed_ok, mmff_ok = embed_ligand(chosen, rerun_sdf)
        frozen_sdf = GCASE_DIR / case["docking_input_ligand_file"]

        smiles_changed = chosen != frozen_smiles
        max_all, max_heavy, note = (None, None, "embed_failed") if not embed_ok else max_coord_delta(frozen_sdf, rerun_sdf)

        row = {
            "pdb_id": pdb_id,
            "frozen_smiles": frozen_smiles,
            "rerun_smiles": chosen,
            "smiles_changed": smiles_changed,
            "rerun_embed_ok": embed_ok,
            "rerun_mmff_converged": mmff_ok,
            "max_coord_delta_all_atoms_A": round(max_all, 4) if max_all is not None else None,
            "max_coord_delta_heavy_atoms_A": round(max_heavy, 4) if max_heavy is not None else None,
            "note": note,
        }
        report.append(row)
        marker = "IDENTICAL" if (max_all is not None and max_all < 1e-6) else "DIFFERS"
        print(f"[{pdb_id}] smiles_changed={smiles_changed} embed_ok={embed_ok} "
              f"max_delta_all={max_all} max_delta_heavy={max_heavy} -> {marker}")

    (RERUN_DIR / "embedding_reproducibility_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    n_smiles_changed = sum(1 for r in report if r["smiles_changed"])
    n_coord_differs = sum(1 for r in report if r["max_coord_delta_all_atoms_A"] not in (None, 0.0) and r["max_coord_delta_all_atoms_A"] >= 1e-6)
    max_delta_overall = max((r["max_coord_delta_all_atoms_A"] for r in report if r["max_coord_delta_all_atoms_A"] is not None), default=None)

    lines = [
        "# Primary 14-complex redocking benchmark: embedding-reproducibility check",
        "",
        "Re-runs the frozen protonation-selection + RDKit ETKDGv3 embedding "
        "pipeline (prepare_ligands.py's pick_variant/embed_ligand, unchanged) "
        "in a fresh process, writing output to redocking_rerun_v1.0/ without "
        "touching the frozen docking_input_ligands/, reference_ligands/, or "
        "gcase_validation_set_v1.0.json. Tests whether the same ETKDGv3 "
        "non-determinism found in the decoy panel (GM_009, up to 1.70 A "
        "despite randomSeed=42) also affects the primary 14-case set.",
        "",
        f"- Protonated-SMILES selection changed: {n_smiles_changed}/{len(report)}",
        f"- Embedded coordinates differ (>=1e-6 A) from the frozen input: {n_coord_differs}/{len(report)}",
        f"- Max coordinate delta across all 14 cases: {max_delta_overall} A" if max_delta_overall is not None else "- Max coordinate delta: n/a",
        "",
        "| PDB | SMILES changed | Embed OK | Max delta, all atoms (A) | Max delta, heavy atoms (A) |",
        "|---|---|---|---|---|",
    ]
    for r in report:
        lines.append(
            f"| {r['pdb_id']} | {r['smiles_changed']} | {r['rerun_embed_ok']} | "
            f"{r['max_coord_delta_all_atoms_A']} | {r['max_coord_delta_heavy_atoms_A']} |"
        )
    lines += [
        "",
        "DiffDock-L is out of scope: it consumes docking_input_protonated_smiles "
        "directly (a bare SMILES string), never the embedded conformer, so this "
        "risk cannot transfer to its arm regardless of the result above. Only "
        "GNINA's `-l` input depends on the embedded conformer.",
        "",
        ("If any case shows a nonzero coordinate delta, GNINA must be re-run "
         "on the freshly-embedded ligands in redocking_rerun_v1.0/docking_input_ligands/ "
         "(receptor and box unchanged) to test whether Success@1/5 and per-case "
         "RMSD change relative to the frozen Table 2/10 result -- see "
         "decisionbench_dd_docking/RUNNING_ON_GPU_INSTANCE.md for the rerun command.")
        if n_coord_differs
        else "No embedding non-determinism reproduced across these 14 cases in this run.",
    ]
    (RERUN_DIR / "embedding_reproducibility_report.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"\n{n_smiles_changed}/{len(report)} SMILES changed; {n_coord_differs}/{len(report)} coordinate sets differ.")
    print(f"Wrote {RERUN_DIR / 'embedding_reproducibility_report.json'} and .md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

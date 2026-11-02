#!/usr/bin/env python3
"""Protonates each case's docking-input SMILES at pH 7.4 and 3D-embeds it for
GNINA (decisionbench_dd_configs_v1.0/gcase_validation/docking_input_ligands/),
and keeps reference_ligands/*.sdf's bond-order/formal-charge template in sync
with the same protonation state (required for RMSD scoring -- see
decisionbench_dd_docking/rmsd.py's docstring on why a charge mismatch there
breaks CalcRMS's substructure matching).

Idempotent and safe to re-run over all 14 cases: correctly-handled cases
reproduce the same output; only cases the selection rule gets wrong change.

v1.1 fix (2026-08-xx): the original selection rule only excluded a
DEPROTONATED sulfonamide nitrogen ([N-] attached to S(=O)(=O)) and otherwise
maximized the count of "good ammonium" sites ([NH3+]/[NH2+]/[NH+]) without
checking what that nitrogen was attached to. A PROTONATED sulfonamide
nitrogen ([NH+] attached to S(=O)(=O)) matches that same pattern, but a
sulfonamide nitrogen -- even a tertiary one -- is far too weak a base to be
protonated at pH 7.4 (the sulfonyl group's electron withdrawal suppresses its
basicity); a genuine aliphatic amine (pKaH ~9-10) is the correct site. This
mis-scored three cases (9FAY, 9FAZ, 9FB2) to net charge +2 (both the real
amine AND the sulfonamide nitrogen protonated) instead of the chemically
correct +1. Fixed by excluding ANY charged nitrogen (either sign) attached to
a sulfonyl group before counting "good ammonium" sites, not just the
anionic case.

v1.3 fix (2026-08-26): found while preparing ligand microstates for the
candidate-screen experiment's 69 novel generated molecules (none of the
original 14 redocking cases exercised this path). pick_variant's tie-break
among variants sharing the same GOOD_AMMONIUM count sorted by SMILES string
alphabetically -- chemically meaningless. For molecules containing azole
rings (tetrazole, imidazole, isoxazole), dimorphite-dl's per-site pKa rules
can independently propose protonating 2-3 ring nitrogens; the alphabetical
tie-break sometimes picked one of those over-protonated variants (observed:
net charge +5, with a tetrazole ring triple-protonated) even though a
variant with the SAME two genuine aliphatic-amine sites protonated and the
azole ring left neutral (net charge +2, the chemically correct answer) was
also available from dimorphite-dl. Fixed by tie-breaking on minimum |net
formal charge| before falling back to alphabetical order: this penalizes
implausible extra protonation without affecting molecules whose multiple
genuinely-independent basic sites are legitimately co-protonated (those
don't tie among candidates in the first place, since only one variant
achieves the maximum good-ammonium count). Verified this does not change any
of the 14 already-frozen redocking cases (0/14 changed on re-run); 19/146
prepared candidate-screen ligand microstates changed (all previously showing
|net charge| of 3-5 from over-protonated heteroaromatic rings, now 1-2).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dimorphite_dl import protonate_smiles
from rdkit import Chem
from rdkit.Chem import AllChem, rdDetermineBonds

REPO_ROOT = Path(__file__).resolve().parent.parent
GCASE_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "gcase_validation"
CASE_LIST_PATH = GCASE_DIR / "gcase_validation_set_v1.0.json"

PH = 7.4
EMBED_SEED = 42

# Excludes a charged nitrogen (either sign) directly bonded to a sulfonyl
# group -- a sulfonamide nitrogen (even N,N-disubstituted) is not a plausible
# protonation/deprotonation site at physiological pH.
BAD_SULFONAMIDE_CHARGE = Chem.MolFromSmarts("[#7;$([#7+]),$([#7-])]-[SX4](=[OX1])(=[OX1])")
GOOD_AMMONIUM = Chem.MolFromSmarts("[N+;$([NH3+,NH2+,NH+])]")


def pick_variant(variants: list[str]) -> tuple[str, str]:
    parsed = []
    for v in variants:
        m = Chem.MolFromSmiles(v)
        if m is None:
            continue
        bad = m.HasSubstructMatch(BAD_SULFONAMIDE_CHARGE)
        n_good = len(m.GetSubstructMatches(GOOD_AMMONIUM))
        abs_charge = abs(Chem.GetFormalCharge(m))
        parsed.append((v, bad, n_good, abs_charge))
    if not parsed:
        return None, "no_valid_variant"

    clean = [p for p in parsed if not p[1]]
    pool = clean if clean else parsed
    flag = "ok" if clean else "all_variants_had_bad_sulfonamide_charge_fallback_used"

    # Tie-break v1.3: among variants tied on n_good ammonium sites, prefer
    # the LOWEST |net charge|, not alphabetical SMILES order. Alphabetical
    # order is chemically arbitrary and, on candidate-screen molecules
    # containing azole rings (tetrazole, imidazole, isoxazole), was found
    # picking variants with 2-3 *extra* protonated heteroaromatic nitrogens
    # beyond the genuinely basic aliphatic amine sites -- e.g. net charge +5
    # instead of the chemically correct +2 for the same aliphatic-amine
    # protonation state, purely because that SMILES string sorted first.
    # Minimizing |net charge| among ties penalizes exactly that kind of
    # implausible extra protonation without touching cases where multiple
    # genuinely independent basic sites really are all protonated (those
    # don't tie in n_good in the first place).
    pool.sort(key=lambda p: (-p[2], p[3], p[0]))
    return pool[0][0], flag


def embed_ligand(smiles: str, out_path: Path) -> tuple[bool, bool]:
    mol = Chem.MolFromSmiles(smiles)
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = EMBED_SEED
    cid = AllChem.EmbedMolecule(mol, params)
    embed_ok = cid >= 0
    ff_result = AllChem.MMFFOptimizeMolecule(mol, maxIters=2000) if embed_ok else None
    out_path.parent.mkdir(parents=True, exist_ok=True)
    writer = Chem.SDWriter(str(out_path))
    mol.SetProp("_Name", out_path.stem)
    writer.write(mol)
    writer.close()
    return embed_ok, (ff_result == 0)


def resync_reference_ligand(case: dict, protonated_smiles: str) -> float:
    """Rebuild reference_ligands/*.sdf's bond-order/charge template from the
    new protonated SMILES, WITHOUT touching the deposited experimental
    coordinates. Returns the max heavy-atom coordinate delta (should be 0.0)
    as a correctness check."""
    sdf_path = GCASE_DIR / case["reference_ligand_file"]
    old_ref = Chem.SDMolSupplier(str(sdf_path))[0]

    heavy_mol = Chem.RWMol()
    for atom in old_ref.GetAtoms():
        heavy_mol.AddAtom(Chem.Atom(atom.GetSymbol()))
    conf = Chem.Conformer(heavy_mol.GetNumAtoms())
    orig_conf = old_ref.GetConformer()
    for i in range(old_ref.GetNumAtoms()):
        conf.SetAtomPosition(i, orig_conf.GetAtomPosition(i))
    heavy_mol.AddConformer(conf)
    mol = heavy_mol.GetMol()
    rdDetermineBonds.DetermineConnectivity(mol)

    template = Chem.MolFromSmiles(protonated_smiles)
    new_ref = AllChem.AssignBondOrdersFromTemplate(template, mol)
    Chem.SanitizeMol(new_ref)

    max_delta = 0.0
    new_conf = new_ref.GetConformer()
    for i in range(new_ref.GetNumAtoms()):
        p_old, p_new = orig_conf.GetAtomPosition(i), new_conf.GetAtomPosition(i)
        d = ((p_old.x - p_new.x) ** 2 + (p_old.y - p_new.y) ** 2 + (p_old.z - p_new.z) ** 2) ** 0.5
        max_delta = max(max_delta, d)

    new_ref.SetProp("_Name", f"{case['pdb_id']}_{case['ligand_comp_id']}")
    writer = Chem.SDWriter(str(sdf_path))
    writer.write(new_ref)
    writer.close()
    return max_delta


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cases", nargs="*", default=None, help="Subset of PDB IDs to (re)prepare (default: all 14)")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    with open(CASE_LIST_PATH) as fh:
        spec = json.load(fh)

    cases = spec["cases"]
    if args.cases:
        cases = [c for c in cases if c["pdb_id"] in args.cases]

    changed = []
    report = []
    for case in cases:
        pdb_id = case["pdb_id"]
        old_smiles = case.get("docking_input_protonated_smiles")
        variants = protonate_smiles(case["docking_input_smiles"], ph_min=PH, ph_max=PH)
        chosen, flag = pick_variant(variants)
        if chosen is None:
            print(f"ERROR [{pdb_id}]: {flag}", file=sys.stderr)
            return 1

        out_sdf = GCASE_DIR / f"docking_input_ligands/{pdb_id}_ligand_input.sdf"
        embed_ok, mmff_ok = embed_ligand(chosen, out_sdf)
        max_coord_delta = resync_reference_ligand(case, chosen)

        case["docking_input_protonated_smiles"] = chosen
        did_change = (old_smiles != chosen)
        if did_change:
            changed.append(pdb_id)

        report.append({
            "pdb_id": pdb_id, "n_variants": len(variants), "selection_flag": flag,
            "old_smiles": old_smiles, "new_smiles": chosen, "changed": did_change,
            "embed_ok": embed_ok, "mmff_converged": mmff_ok,
            "reference_ligand_max_coord_delta": max_coord_delta,
        })
        marker = "CHANGED" if did_change else "unchanged"
        print(f"[{pdb_id}] {marker}: {chosen}")

    with open(CASE_LIST_PATH, "w") as fh:
        json.dump(spec, fh, indent=2)
    with open(GCASE_DIR / "ligand_docking_input_report.json", "w") as fh:
        json.dump(report, fh, indent=2)

    print(f"\n{len(changed)}/{len(cases)} cases changed: {changed}")
    if changed:
        print("NOTE: GNINA and DiffDock must be re-run for these cases -- their docking "
              "input changed. Existing docking_runs/ output for them is stale.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

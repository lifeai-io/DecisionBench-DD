"""Pose-validity sanity checks for docked GCase poses
(decisionbench_dd_configs_v1.0/gcase_validation/redocking_protocol_v1.0.json:
rmsd_scoring.pose_validity).

This is a deliberately simplified, honestly-scoped proxy for a full
PoseBusters-style geometry audit, not a reimplementation of it: cheap,
RDKit/BioPython-only checks that catch the most common docking-output
pathologies (broken valences, bond lengths outside any plausible covalent
range, severe internal steric clashes, and severe protein-ligand clashes).
It does NOT check ring planarity, torsion-angle plausibility, per-element
van-der-Waals-radius-scaled clash thresholds, or the many other things real
PoseBusters covers -- the clash thresholds here are flat heavy-atom distance
cutoffs, not element-pair-specific. Frozen before any further result
inspection, per external review's point that this endpoint should exist and
be pre-registered rather than left as an unimplemented TODO while RMSD
results are already being reported.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from rdkit import Chem

MIN_BOND_LENGTH_ANGSTROM = 0.7
MAX_BOND_LENGTH_ANGSTROM = 2.2
MIN_NONBONDED_DISTANCE_ANGSTROM = 1.5  # severe steric clash threshold between non-bonded heavy atoms
MIN_PROTEIN_LIGAND_DISTANCE_ANGSTROM = 1.5  # severe protein-ligand clash threshold (flat cutoff, not VDW-scaled)


@dataclass
class PoseValidityResult:
    valid_valences: bool
    bond_lengths_ok: bool
    no_severe_internal_clash: bool
    bad_bonds: list = field(default_factory=list)
    clashing_pairs: list = field(default_factory=list)
    no_severe_protein_clash: Optional[bool] = None  # None = not checked (no receptor given)
    protein_clashes: list = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        base = self.valid_valences and self.bond_lengths_ok and self.no_severe_internal_clash
        if self.no_severe_protein_clash is None:
            return base
        return base and self.no_severe_protein_clash


_RECEPTOR_CACHE: dict = {}


def _load_receptor_heavy_atom_coords(receptor_path: Path):
    key = str(receptor_path)
    if key not in _RECEPTOR_CACHE:
        from Bio.PDB import PDBParser

        parser = PDBParser(QUIET=True)
        structure = parser.get_structure("receptor", str(receptor_path))
        coords = [atom.coord for atom in structure.get_atoms() if atom.element != "H"]
        _RECEPTOR_CACHE[key] = coords
    return _RECEPTOR_CACHE[key]


def check_pose_validity(mol, receptor_path: Optional[Path] = None) -> PoseValidityResult:
    """`mol` must be a heavy-atom RDKit Mol with a 3D conformer (i.e. what
    decisionbench_dd_docking.rmsd already loads for each pose). If
    `receptor_path` is given (the prepared receptor PDB used for this same
    docking run), also checks for severe ligand-protein clashes."""
    try:
        Chem.SanitizeMol(Chem.Mol(mol))
        valid_valences = True
    except Exception:
        valid_valences = False

    conf = mol.GetConformer()
    bad_bonds = []
    for bond in mol.GetBonds():
        i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        d = conf.GetAtomPosition(i).Distance(conf.GetAtomPosition(j))
        if not (MIN_BOND_LENGTH_ANGSTROM <= d <= MAX_BOND_LENGTH_ANGSTROM):
            bad_bonds.append((i, j, round(d, 3)))

    bonded_pairs = {frozenset((b.GetBeginAtomIdx(), b.GetEndAtomIdx())) for b in mol.GetBonds()}
    n = mol.GetNumAtoms()
    clashing_pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            if frozenset((i, j)) in bonded_pairs:
                continue
            d = conf.GetAtomPosition(i).Distance(conf.GetAtomPosition(j))
            if d < MIN_NONBONDED_DISTANCE_ANGSTROM:
                clashing_pairs.append((i, j, round(d, 3)))

    no_severe_protein_clash = None
    protein_clashes = []
    if receptor_path is not None:
        import numpy as np

        receptor_coords = np.array(_load_receptor_heavy_atom_coords(Path(receptor_path)))
        for i in range(n):
            p = conf.GetAtomPosition(i)
            lig_xyz = np.array([p.x, p.y, p.z])
            dists = np.linalg.norm(receptor_coords - lig_xyz, axis=1)
            min_idx = int(np.argmin(dists))
            if dists[min_idx] < MIN_PROTEIN_LIGAND_DISTANCE_ANGSTROM:
                protein_clashes.append((i, min_idx, round(float(dists[min_idx]), 3)))
        no_severe_protein_clash = (len(protein_clashes) == 0)

    return PoseValidityResult(
        valid_valences=valid_valences,
        bond_lengths_ok=(len(bad_bonds) == 0),
        no_severe_internal_clash=(len(clashing_pairs) == 0),
        bad_bonds=bad_bonds,
        clashing_pairs=clashing_pairs,
        no_severe_protein_clash=no_severe_protein_clash,
        protein_clashes=protein_clashes,
    )

"""Symmetry-aware docking-pose RMSD scoring for the GCase redocking benchmark
(decisionbench_dd_configs_v1.0/gcase_validation/redocking_protocol_v1.0.json).

Uses RDKit's rdMolAlign.CalcRMS, NOT GetBestRMS. GetBestRMS re-aligns (rotates
and translates) the probe molecule onto the reference before computing RMSD,
which would silently discard exactly the pose/placement error a redocking
benchmark exists to measure -- both structures are already in the same
receptor-fixed crystal coordinate frame, and any additional superposition
would artificially shrink RMSD. CalcRMS computes RMSD "in place": it still
searches over symmetry-equivalent atom-label permutations (so a docked pose
with a rotated/flipped symmetric ring isn't penalized for an arbitrary
labeling choice), but performs no rigid-body realignment. RDKit's own
docstring for CalcRMS names this exact use case: "compute the RMSD between
docking poses and the co-crystallized ligand."

Gotcha hit in practice (gcase_validation_set_v1.0.json's 2026-08-25
amendment): CalcRMS's substructure-match-based atom correspondence requires
matching formal charges atom-for-atom, not just element/connectivity. If the
reference ligand and the docked pose were built from different protonation
states (e.g. reference from a neutral SMILES, pose from the pH-7.4-protonated
SMILES actually fed to the docking tool), it raises "No sub-structure match
found" even though the two structures represent the same physical molecule.
Both reference_ligands/*.sdf and docking_input_ligands/*.sdf must be built
from the SAME protonated SMILES for this reason.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rdkit import Chem
from rdkit.Chem import rdMolAlign

from decisionbench_dd_docking.pose_validity import check_pose_validity
from decisionbench_dd_docking.prepare_ligands import BAD_SULFONAMIDE_CHARGE

SUCCESS_THRESHOLD_ANGSTROM = 2.0
DEFAULT_MAX_MATCHES = 100_000


class RMSDError(ValueError):
    pass


def _fix_known_pose_charge_artifact(mol):
    """Neutralize a specific, empirically-confirmed DiffDock-L output
    artifact: for 9FAY/9FAZ/9FB2 (net charge +1 per
    docking_input_protonated_smiles -- a neutral tertiary sulfonamide N plus
    one protonated amine), DiffDock's rank*.sdf output instead comes back
    with BOTH nitrogens showing formal charge +1 (net +2), verified by direct
    inspection of the SDF's `M  CHG` block. Neutralizing just the spurious
    sulfonamide-N charge (same substructure prepare_ligands.py's
    BAD_SULFONAMIDE_CHARGE already excludes when *choosing* a protonation
    state) and re-sanitizing restores a full substructure match against the
    reference with an unchanged conformer -- confirmed no atom is added,
    removed, or moved; only the charge label changes. This is scored as a
    known output-representation bug in the docking tool, not a real pose
    difference: neither tool is asked to predict protonation state, both are
    given a fixed, pre-registered ligand identity as input.

    Returns (possibly-copied mol, whether a correction was applied) so
    callers can report exactly which/how many poses were touched -- this
    must stay auditable, not a silent rewrite.
    """
    if not mol.HasSubstructMatch(BAD_SULFONAMIDE_CHARGE):
        return mol, False
    fixed = Chem.Mol(mol)
    for match in fixed.GetSubstructMatches(BAD_SULFONAMIDE_CHARGE):
        fixed.GetAtomWithIdx(match[0]).SetFormalCharge(0)
    Chem.SanitizeMol(fixed)
    return fixed, True


def symmetry_aware_rmsd(pose_mol, reference_mol, max_matches: int = DEFAULT_MAX_MATCHES) -> float:
    """Heavy-atom, symmetry-aware, in-place RMSD between a single docked pose
    and the crystal reference ligand. Both must be heavy-atom-only molecules
    with the same connectivity (element composition and bonding), differing
    only in conformer/atom-order -- exactly what
    decisionbench_dd_eval-style SDF pose files and the frozen
    reference_ligands/*.sdf files provide.
    """
    pose_noh = Chem.RemoveHs(pose_mol)
    ref_noh = Chem.RemoveHs(reference_mol)
    if pose_noh.GetNumAtoms() != ref_noh.GetNumAtoms():
        raise RMSDError(
            f"Atom count mismatch: pose has {pose_noh.GetNumAtoms()} heavy atoms, "
            f"reference has {ref_noh.GetNumAtoms()}. Not the same ligand/instance."
        )
    try:
        return rdMolAlign.CalcRMS(pose_noh, ref_noh, maxMatches=max_matches)
    except RuntimeError as exc:
        # CalcRMS raises a bare RuntimeError (not a documented exception type)
        # when it can't find any substructure correspondence at all -- e.g.
        # same atom count but mismatched formal charges (see this module's
        # docstring). Wrapped so callers can catch RMSDError uniformly rather
        # than needing to know about this RDKit implementation detail.
        raise RMSDError(f"No substructure correspondence between pose and reference: {exc}") from exc


@dataclass
class CaseResult:
    pdb_id: str
    tool: str
    n_poses_scored: int
    pose_rmsds: list  # in rank order, rank 1 first
    pose_valid: list  # in rank order; PoseValidityResult.is_valid per pose (see pose_validity.py)
    top1_rmsd: Optional[float]
    best_of_n_rmsd: Optional[float]
    top1_valid: Optional[bool]
    success_at_1: bool
    success_at_n: bool
    error: Optional[str] = None
    n_poses_charge_artifact_fixed: int = 0  # see _fix_known_pose_charge_artifact -- must stay auditable


def load_poses(pose_sdf_path: Path) -> list:
    """A multi-model SDF, poses in rank order (rank 1 / top score first) --
    the frozen output convention for both GNINA and DiffDock-L
    (redocking_protocol_v1.0.json)."""
    suppl = Chem.SDMolSupplier(str(pose_sdf_path), removeHs=False)
    mols = [m for m in suppl if m is not None]
    return mols


def load_reference(reference_sdf_path: Path):
    mol = Chem.SDMolSupplier(str(reference_sdf_path))[0]
    if mol is None:
        raise RMSDError(f"Could not parse reference ligand SDF: {reference_sdf_path}")
    return mol


def score_case(
    pdb_id: str,
    tool: str,
    pose_sdf_path: Path,
    reference_sdf_path: Path,
    success_threshold: float = SUCCESS_THRESHOLD_ANGSTROM,
    top_n: int = 5,
    receptor_path: Optional[Path] = None,
) -> CaseResult:
    try:
        reference = load_reference(reference_sdf_path)
        poses = load_poses(pose_sdf_path)
    except (RMSDError, OSError) as exc:
        return CaseResult(
            pdb_id=pdb_id, tool=tool, n_poses_scored=0, pose_rmsds=[], pose_valid=[],
            top1_rmsd=None, best_of_n_rmsd=None, top1_valid=None, success_at_1=False, success_at_n=False,
            error=str(exc),
        )
    if not poses:
        return CaseResult(
            pdb_id=pdb_id, tool=tool, n_poses_scored=0, pose_rmsds=[], pose_valid=[],
            top1_rmsd=None, best_of_n_rmsd=None, top1_valid=None, success_at_1=False, success_at_n=False,
            error="no poses in pose_sdf_path",
        )

    scored = poses[:top_n]
    rmsds = []
    pose_valid = []
    n_charge_fixed = 0
    for pose in scored:
        pose_for_rmsd, was_fixed = _fix_known_pose_charge_artifact(Chem.RemoveHs(pose))
        n_charge_fixed += int(was_fixed)
        try:
            rmsds.append(symmetry_aware_rmsd(pose_for_rmsd, reference))
        except RMSDError:
            rmsds.append(None)
        pose_valid.append(check_pose_validity(Chem.RemoveHs(pose), receptor_path=receptor_path).is_valid)

    valid = [r for r in rmsds if r is not None]
    top1 = rmsds[0] if rmsds and rmsds[0] is not None else None
    best_of_n = min(valid) if valid else None
    top1_valid = pose_valid[0] if pose_valid else None

    return CaseResult(
        pdb_id=pdb_id,
        tool=tool,
        n_poses_scored=len(scored),
        pose_rmsds=rmsds,
        pose_valid=pose_valid,
        top1_rmsd=top1,
        best_of_n_rmsd=best_of_n,
        top1_valid=top1_valid,
        success_at_1=(top1 is not None and top1 <= success_threshold),
        success_at_n=(best_of_n is not None and best_of_n <= success_threshold),
        n_poses_charge_artifact_fixed=n_charge_fixed,
    )


def success_rate(results: list, key: str) -> float:
    if not results:
        return float("nan")
    return 100.0 * sum(1 for r in results if getattr(r, key)) / len(results)

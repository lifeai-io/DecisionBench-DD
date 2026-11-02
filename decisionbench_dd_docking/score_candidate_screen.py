#!/usr/bin/env python3
"""Scores the 146-job GNINA candidate screen against the frozen primary
structural-prioritization proxy
(decisionbench_dd_configs_v1.0/candidate_screen_v1.0/downstream_gcase_screening_protocol.md,
sections 7-9). Unlike decisionbench_dd_docking.evaluate_docking (redocking:
compares a pose to a known crystal answer via RMSD), there is no ground-truth
pose for a generated candidate -- "success" here is a structural-plausibility
proxy: geometry validity, active-site occupancy, and CNNaffinity relative to
the Ambroxol control, all under the identical 3KEH/3KE0 invocation.

CNNscore/CNNaffinity/CNN_VS/minimizedAffinity are read directly from each
pose's SD tags (confirmed present in the real 14-case redocking output,
e.g. docking_runs/gnina/3GXF_poses.sdf) -- not scraped from the GNINA log.
With --cnn_scoring rescore, poses already come out of GNINA pre-sorted by
CNNscore descending (verified against that same real log), so "native rank
1" already is "highest CNNscore"; this module re-sorts explicitly anyway
(protocol's tie-break: CNNscore desc, then CNNaffinity desc, then
minimizedAffinity asc, then original rank) rather than trusting GNINA's
output order blindly.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
from rdkit import Chem
from scipy import stats

from decisionbench_dd_docking.pose_validity import check_pose_validity

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREEN_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "candidate_screen_v1.0"
CANDIDATE_MANIFEST = SCREEN_DIR / "candidate_manifest.csv"
MICROSTATE_MANIFEST = SCREEN_DIR / "ligand_microstate_manifest.csv"

CATALYTIC_RESIDUES = [235, 340]
CATALYTIC_OXYGEN_NAMES = {"OE1", "OE2"}
ACTIVE_SITE_DISTANCE_ANGSTROM = 4.5
N_GENMOL_MOLMIM_REQUESTED = 300
AMBROXOL_ID = "CTRL_AMBROXOL"


@dataclass
class PoseScore:
    rank: int
    cnnscore: float
    cnnaffinity: float
    cnn_vs: Optional[float]
    minimized_affinity: float
    valid: bool
    active_site_occupied: bool


@dataclass
class CandidateResult:
    ligand_id: str
    receptor_state: str
    tool: str
    n_poses: int
    top1: Optional[PoseScore]
    all_five_poses_returned: bool
    error: Optional[str] = None


def _load_catalytic_oxygen_coords(receptor_path: Path) -> np.ndarray:
    from Bio.PDB import PDBParser

    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("receptor", str(receptor_path))
    chain = structure[0]["A"]
    coords = []
    for resnum in CATALYTIC_RESIDUES:
        residue = chain[resnum]
        for atom in residue:
            if atom.name in CATALYTIC_OXYGEN_NAMES:
                coords.append(atom.coord)
    if not coords:
        raise ValueError(f"No catalytic-residue carboxylate oxygens found in {receptor_path}")
    return np.array(coords)


def _active_site_occupied(mol, catalytic_oxygens: np.ndarray) -> bool:
    conf = mol.GetConformer()
    for i in range(mol.GetNumAtoms()):
        p = conf.GetAtomPosition(i)
        xyz = np.array([p.x, p.y, p.z])
        if np.any(np.linalg.norm(catalytic_oxygens - xyz, axis=1) <= ACTIVE_SITE_DISTANCE_ANGSTROM):
            return True
    return False


def score_pose_file(pose_sdf_path: Path, receptor_path: Path, catalytic_oxygens: np.ndarray) -> tuple[list[PoseScore], Optional[str]]:
    if not pose_sdf_path.is_file():
        return [], "missing pose file"
    suppl = Chem.SDMolSupplier(str(pose_sdf_path), removeHs=False)
    mols = [m for m in suppl if m is not None]
    if not mols:
        return [], "no poses parsed"

    scored = []
    for i, mol in enumerate(mols):
        try:
            cnnscore = float(mol.GetProp("CNNscore"))
            cnnaffinity = float(mol.GetProp("CNNaffinity"))
            minimized_affinity = float(mol.GetProp("minimizedAffinity"))
            cnn_vs = float(mol.GetProp("CNN_VS")) if mol.HasProp("CNN_VS") else None
        except KeyError as exc:
            return [], f"pose {i} missing expected SD tag: {exc}"
        mol_noh = Chem.RemoveHs(mol)
        valid = check_pose_validity(mol_noh, receptor_path=receptor_path).is_valid
        occupied = _active_site_occupied(mol_noh, catalytic_oxygens)
        scored.append(PoseScore(
            rank=i + 1, cnnscore=cnnscore, cnnaffinity=cnnaffinity, cnn_vs=cnn_vs,
            minimized_affinity=minimized_affinity, valid=valid, active_site_occupied=occupied,
        ))

    # Protocol's tie-break: CNNscore desc, CNNaffinity desc, minimizedAffinity asc, original rank asc.
    scored.sort(key=lambda p: (-p.cnnscore, -p.cnnaffinity, p.minimized_affinity, p.rank))
    return scored, None


def score_candidate(ligand_id: str, tool: str, receptor_state: str, runs_dir: Path, receptor_path: Path, catalytic_oxygens: np.ndarray, expected_n_poses: int = 5) -> CandidateResult:
    pose_path = runs_dir / receptor_state / f"{ligand_id}_poses.sdf"
    scored, error = score_pose_file(pose_path, receptor_path, catalytic_oxygens)
    if error is not None:
        return CandidateResult(ligand_id, receptor_state, tool, 0, None, False, error=error)
    top1 = scored[0]
    return CandidateResult(
        ligand_id=ligand_id, receptor_state=receptor_state, tool=tool,
        n_poses=len(scored), top1=top1,
        all_five_poses_returned=(len(scored) == expected_n_poses),
    )


def structural_proxy_pass(result: CandidateResult, ambroxol_cnnaffinity_3keh: float) -> bool:
    if result.receptor_state != "3KEH" or result.error is not None or result.top1 is None:
        return False
    return (
        result.all_five_poses_returned
        and result.top1.valid
        and result.top1.active_site_occupied
        and result.top1.cnnaffinity >= ambroxol_cnnaffinity_3keh
    )


def exact_binomial_ci(successes: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    ci = stats.binomtest(successes, n).proportion_ci(method="exact")
    return (round(float(ci.low), 4), round(float(ci.high), 4))


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--runs-dir", type=Path, required=True, help="Directory containing <3KEH|3KE0>/<ligand_id>_poses.sdf")
    p.add_argument("--out-dir", type=Path, default=REPO_ROOT / "candidate_screen_results")
    p.add_argument("--candidate-manifest", type=Path, default=CANDIDATE_MANIFEST, help="candidate_id,tool,canonical_smiles CSV (default: frozen primary 69-candidate manifest)")
    p.add_argument("--microstate-manifest", type=Path, default=MICROSTATE_MANIFEST, help="ligand_microstate_manifest.csv matching --runs-dir (default: frozen primary manifest)")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    with open(args.candidate_manifest, newline="") as fh:
        candidates = list(csv.DictReader(fh))
    ligand_tool = {c["candidate_id"]: c["tool"] for c in candidates}
    ligand_tool[AMBROXOL_ID] = "control"
    for cid in ("CTRL_IFM", "CTRL_P9V", "CTRL_P8Y"):
        ligand_tool[cid] = "control"

    with open(args.microstate_manifest, newline="") as fh:
        microstates = list(csv.DictReader(fh))
    prepared_ligands = {(m["ligand_id"], m["receptor_state"]) for m in microstates if m["microstate_ambiguous"] != "True" and m["embed_ok"] == "True"}
    microstate_ambiguous = {m["ligand_id"] for m in microstates if m["microstate_ambiguous"] == "True"}

    all_ligand_ids = sorted(ligand_tool.keys())

    catalytic_oxygens = {
        state: _load_catalytic_oxygen_coords(SCREEN_DIR / "receptors_prepared" / f"{state}_prepared.pdb")
        for state in ("3KEH", "3KE0")
    }
    receptor_paths = {state: SCREEN_DIR / "receptors_prepared" / f"{state}_prepared.pdb" for state in ("3KEH", "3KE0")}

    pose_rows = []
    results_by_ligand_state: dict[tuple[str, str], CandidateResult] = {}
    for ligand_id in all_ligand_ids:
        tool = ligand_tool[ligand_id]
        for state in ("3KEH", "3KE0"):
            if (ligand_id, state) not in prepared_ligands:
                result = CandidateResult(ligand_id, state, tool, 0, None, False, error="microstate_ambiguous or embed failed")
            else:
                result = score_candidate(ligand_id, tool, state, args.runs_dir, receptor_paths[state], catalytic_oxygens[state])
            results_by_ligand_state[(ligand_id, state)] = result
            pose_rows.append({
                "ligand_id": ligand_id, "tool": tool, "receptor_state": state,
                "n_poses": result.n_poses, "all_five_poses_returned": result.all_five_poses_returned,
                "top1_cnnscore": result.top1.cnnscore if result.top1 else None,
                "top1_cnnaffinity": result.top1.cnnaffinity if result.top1 else None,
                "top1_minimized_affinity": result.top1.minimized_affinity if result.top1 else None,
                "top1_valid": result.top1.valid if result.top1 else None,
                "top1_active_site_occupied": result.top1.active_site_occupied if result.top1 else None,
                "error": result.error,
            })

    ambroxol_3keh = results_by_ligand_state.get((AMBROXOL_ID, "3KEH"))
    if ambroxol_3keh is None or ambroxol_3keh.top1 is None:
        print("ERROR: Ambroxol 3KEH control result missing -- cannot evaluate structural proxy.", file=sys.stderr)
        return 1
    ambroxol_cnnaffinity_3keh = ambroxol_3keh.top1.cnnaffinity

    candidate_rows = []
    for candidate in candidates:
        cid = candidate["candidate_id"]
        result_3keh = results_by_ligand_state[(cid, "3KEH")]
        passes = structural_proxy_pass(result_3keh, ambroxol_cnnaffinity_3keh)

        result_3ke0 = results_by_ligand_state[(cid, "3KE0")]
        delta_cnnaffinity = None
        interpretable = (
            cid not in microstate_ambiguous
            and result_3keh.top1 is not None and result_3keh.top1.valid and result_3keh.top1.active_site_occupied
            and result_3ke0.top1 is not None and result_3ke0.top1.valid and result_3ke0.top1.active_site_occupied
        )
        if interpretable:
            delta_cnnaffinity = result_3keh.top1.cnnaffinity - result_3ke0.top1.cnnaffinity

        candidate_rows.append({
            "candidate_id": cid, "tool": candidate["tool"],
            "structural_proxy_pass": passes,
            "cnnaffinity_3keh": result_3keh.top1.cnnaffinity if result_3keh.top1 else None,
            "cnnaffinity_3ke0": result_3ke0.top1.cnnaffinity if result_3ke0.top1 else None,
            "delta_cnnaffinity_neutral_minus_acidic": delta_cnnaffinity,
            "ph_interpretable": interpretable,
        })

    def _control_delta(control_id: str) -> Optional[float]:
        r_keh = results_by_ligand_state[(control_id, "3KEH")]
        r_ke0 = results_by_ligand_state[(control_id, "3KE0")]
        if r_keh.top1 is None or r_ke0.top1 is None:
            return None
        return r_keh.top1.cnnaffinity - r_ke0.top1.cnnaffinity

    # All four controls, not just Ambroxol: a single control passing its own
    # directional sanity check does not, by itself, establish that the
    # neutral-vs-acidic score difference is a validated pH-sensitivity
    # endpoint for every candidate -- see the other three controls below,
    # three of which point the other way.
    controls_delta = {
        "CTRL_AMBROXOL": _control_delta("CTRL_AMBROXOL"),
        "CTRL_IFM": _control_delta("CTRL_IFM"),
        "CTRL_P9V": _control_delta("CTRL_P9V"),
        "CTRL_P8Y": _control_delta("CTRL_P8Y"),
    }
    ambroxol_delta = controls_delta["CTRL_AMBROXOL"]
    ambroxol_directional_sanity_check_passed = ambroxol_delta is not None and ambroxol_delta > 0

    other_control_deltas = [controls_delta[c] for c in ("CTRL_IFM", "CTRL_P9V", "CTRL_P8Y") if controls_delta[c] is not None]
    n_other_controls_positive = sum(1 for d in other_control_deltas if d > 0)

    candidate_deltas = [r["delta_cnnaffinity_neutral_minus_acidic"] for r in candidate_rows if r["ph_interpretable"]]
    n_candidates_interpretable = len(candidate_deltas)
    n_candidates_positive = sum(1 for d in candidate_deltas if d > 0)

    # Directionally supported only if Ambroxol's own check passes AND most of
    # the OTHER controls agree AND most interpretable candidates agree --
    # otherwise this is exploratory, not a validated endpoint, regardless of
    # what Ambroxol alone shows. With the evidence on hand (3/4 controls and
    # <50% of candidates favor the acidic state) this deliberately resolves
    # to "exploratory_unvalidated", not "informative", for this run.
    ph_sensitivity_endpoint_status = (
        "directionally_supported"
        if (
            ambroxol_directional_sanity_check_passed
            and other_control_deltas and n_other_controls_positive / len(other_control_deltas) > 0.5
            and n_candidates_interpretable and n_candidates_positive / n_candidates_interpretable > 0.5
        )
        else "exploratory_unvalidated"
    )

    funnel_rows = []
    generator_summary = {}
    for tool in ("genmol", "molmim"):
        tool_candidates = [r for r in candidate_rows if r["tool"] == tool]
        n_passing = sum(1 for r in tool_candidates if r["structural_proxy_pass"])
        n_qualified = len(tool_candidates)
        y_ci = exact_binomial_ci(n_passing, N_GENMOL_MOLMIM_REQUESTED)
        r_ci = exact_binomial_ci(n_passing, n_qualified) if n_qualified else (float("nan"), float("nan"))
        generator_summary[tool] = {
            "n_chemically_qualified": n_qualified,
            "n_structural_proxy_pass": n_passing,
            "Y_structural_proxy": round(n_passing / N_GENMOL_MOLMIM_REQUESTED, 4),
            "Y_structural_proxy_95pct_exact_binomial_ci": y_ci,
            "R_structural_given_chemical": round(n_passing / n_qualified, 4) if n_qualified else None,
            "R_structural_given_chemical_95pct_exact_binomial_ci": r_ci,
        }
        funnel_rows.append({"tool": tool, "stage": "chemically_qualified", "count": n_qualified, "of_requested": N_GENMOL_MOLMIM_REQUESTED})
        funnel_rows.append({"tool": tool, "stage": "structural_proxy_pass", "count": n_passing, "of_requested": N_GENMOL_MOLMIM_REQUESTED})

    with open(args.out_dir / "pose_scores.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(pose_rows[0].keys()))
        writer.writeheader()
        writer.writerows(pose_rows)

    with open(args.out_dir / "candidate_results.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(candidate_rows[0].keys()))
        writer.writeheader()
        writer.writerows(candidate_rows)

    with open(args.out_dir / "generator_funnel.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["tool", "stage", "count", "of_requested"])
        writer.writeheader()
        writer.writerows(funnel_rows)

    summary = {
        "ambroxol_cnnaffinity_3keh": ambroxol_cnnaffinity_3keh,
        "controls_delta_cnnaffinity_neutral_minus_acidic": controls_delta,
        "ambroxol_directional_sanity_check_passed": ambroxol_directional_sanity_check_passed,
        "ph_sensitivity_endpoint_status": ph_sensitivity_endpoint_status,
        "ph_sensitivity_evidence": {
            "n_other_controls_positive": n_other_controls_positive,
            "n_other_controls_total": len(other_control_deltas),
            "n_candidates_favoring_neutral": n_candidates_positive,
            "n_candidates_interpretable": n_candidates_interpretable,
        },
        "ph_sensitivity_note": (
            "Ambroxol's own directional sanity check passes (positive neutral-minus-acidic "
            "CNNaffinity delta), but this does not by itself validate the pH-sensitivity endpoint: "
            f"only {n_other_controls_positive}/{len(other_control_deltas)} of the other controls "
            f"(isofagomine, P9V, P8Y) agree, and only {n_candidates_positive}/{n_candidates_interpretable} "
            "interpretable candidates favor the neutral state. Status is reported as "
            f"'{ph_sensitivity_endpoint_status}': these score differences may inform exploratory "
            "prioritization but do not establish pH-dependent binding, lysosomal release, or "
            "pharmacological-chaperone behavior. The primary neutral-state structural-proxy endpoint "
            "is unaffected and remains the frozen primary result."
        ),
        "generators": generator_summary,
    }
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = ["# DecisionBench-DD candidate screen summary", ""]
    lines.append(f"Ambroxol CNNaffinity @ 3KEH (pass/fail threshold for all candidates) = {ambroxol_cnnaffinity_3keh:.3f}")
    lines.append("")
    lines.append("Control neutral-minus-acidic CNNaffinity deltas (positive = favors neutral/3KEH):")
    control_names = {"CTRL_AMBROXOL": "Ambroxol", "CTRL_IFM": "Isofagomine (IFM)", "CTRL_P9V": "P9V", "CTRL_P8Y": "P8Y"}
    for cid, name in control_names.items():
        d = controls_delta[cid]
        lines.append(f"  - {name}: {d:+.3f}" if d is not None else f"  - {name}: N/A")
    lines.append("")
    lines.append(f"pH-sensitivity endpoint status: **{ph_sensitivity_endpoint_status}**. {summary['ph_sensitivity_note']}")
    lines.append("")
    for tool, s in generator_summary.items():
        lines.append(f"## {tool}")
        lines.append(f"- Chemically qualified: {s['n_chemically_qualified']}")
        lines.append(f"- Structural-proxy pass: {s['n_structural_proxy_pass']} (R_structural|chemical = {s['R_structural_given_chemical']})")
        lines.append(f"- Y_structural_proxy = {s['Y_structural_proxy']*100:.2f}% (95% exact binomial CI {s['Y_structural_proxy_95pct_exact_binomial_ci']})")
        lines.append("")
    (args.out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote results to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Diagnoses exactly where RDKit ETKDGv3 embedding non-determinism can and
cannot be reproduced, prompted by a reviewer's request not to claim RDKit
embedding is "universally nondeterministic" without checking the actual call
path (EmbedMolecule vs. EmbedMultipleConfs, numThreads, useRandomCoords,
etc.) and without isolating whether differences occur within one process,
across fresh processes, or only across machines/environments.

Read-only: never touches any frozen file. Uses prepare_ligands.embed_ligand
unchanged (the same function that prepared the frozen primary redocking
inputs) so this tests the real call path, not a reimplementation.

Findings this script establishes (see diagnose_embedding_determinism_report.md
for the actual run's numbers):
  1. Call-path facts: prepare_ligands.py uses AllChem.EmbedMolecule (not
     EmbedMultipleConfs), so RDKit's numThreads parameter -- which only
     applies to EmbedMultipleConfs and defaults to 1 -- is not in play here
     at all. randomSeed is explicitly set (42); useRandomCoords,
     enforceChirality, and pruning are left at ETKDGv3()'s documented
     defaults (never overridden). MMFFOptimizeMolecule (maxIters=2000) runs
     after embedding.
  2. Within-process repeat: two embeddings of the same molecule/seed in one
     Python process (both with and without the MMFF step).
  3. Cross-process repeat: N independent `python3` subprocess invocations of
     the identical code path, compared to each other.
  4. Comparison against a named frozen SDF already committed in the repo
     (e.g. a gcase_validation docking_input_ligands/*.sdf), to test whether
     THIS environment's reproducible result matches what was checked in.

This script cannot test "only across machines" directly (this sandbox is one
machine/environment) -- that remains an open, disclosed limitation, not
something this script can confirm or rule out.

Usage:
    python -m decisionbench_dd_docking.diagnose_embedding_determinism \\
        --smiles "[NH3+]C[C@@H](O)CNS(=O)(=O)c1ccccc1F" \\
        --compare-frozen decisionbench_dd_configs_v1.0/gcase_validation/docking_input_ligands/9FA6_ligand_input.sdf \\
        --n-subprocess 5
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from rdkit import Chem

import rdkit
from rdkit.Chem import AllChem

from decisionbench_dd_docking.prepare_ligands import EMBED_SEED, embed_ligand

REPO_ROOT = Path(__file__).resolve().parent.parent
_SINGLE_FLAG = "--_single-embed-worker"


def call_path_facts() -> dict:
    params = AllChem.ETKDGv3()
    return {
        "rdkit_version": rdkit.__version__,
        "embedding_function": "AllChem.EmbedMolecule (not EmbedMultipleConfs)",
        "randomSeed_set_explicitly_to": EMBED_SEED,
        "numThreads_default_ETKDGv3": params.numThreads,
        "numThreads_note": "numThreads only affects EmbedMultipleConfs; EmbedMolecule does not use it, so this parameter is not in play for this pipeline.",
        "useRandomCoords_default": params.useRandomCoords,
        "enforceChirality_default": params.enforceChirality,
        "pruneRmsThresh_default": params.pruneRmsThresh,
        "post_embedding_optimization": "AllChem.MMFFOptimizeMolecule(mol, maxIters=2000)",
        "overridden_from_ETKDGv3_defaults": ["randomSeed"],
    }


def coords_of(sdf_path: Path) -> list[tuple[float, float, float]]:
    mol = Chem.SDMolSupplier(str(sdf_path), removeHs=False)[0]
    conf = mol.GetConformer()
    return [tuple(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())]


def max_delta(a: list[tuple[float, float, float]], b: list[tuple[float, float, float]]) -> float | None:
    if len(a) != len(b):
        return None
    return max(((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2) ** 0.5 for (ax, ay, az), (bx, by, bz) in zip(a, b))


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--smiles", required=True, help="Protonated SMILES to embed (e.g. a case's docking_input_protonated_smiles)")
    p.add_argument("--compare-frozen", type=Path, default=None, help="A committed frozen *_ligand_input.sdf to compare this environment's reproduction against")
    p.add_argument("--n-subprocess", type=int, default=5, help="Number of fresh python3 subprocess invocations to compare")
    p.add_argument("--out-dir", type=Path, default=REPO_ROOT / "embedding_determinism_diagnostic")
    p.add_argument(_SINGLE_FLAG, action="store_true", help=argparse.SUPPRESS)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    if getattr(args, "_single_embed_worker"):
        # Internal worker mode: embed once, print coords as JSON to stdout, exit.
        tmp = Path("/tmp") / f"_embed_worker_{__import__('os').getpid()}.sdf"
        embed_ligand(args.smiles, tmp)
        print(json.dumps(coords_of(tmp)))
        tmp.unlink(missing_ok=True)
        return 0

    facts = call_path_facts()

    # 1. Within-process repeat.
    tmp1 = args.out_dir / "_within_process_1.sdf"
    tmp2 = args.out_dir / "_within_process_2.sdf"
    args.out_dir.mkdir(parents=True, exist_ok=True)
    embed_ligand(args.smiles, tmp1)
    embed_ligand(args.smiles, tmp2)
    within_process_delta = max_delta(coords_of(tmp1), coords_of(tmp2))

    # 2. Cross-process repeats (fresh `python3` invocations of this same script).
    cross_process_coords = []
    for _ in range(args.n_subprocess):
        result = subprocess.run(
            [sys.executable, "-m", "decisionbench_dd_docking.diagnose_embedding_determinism",
             "--smiles", args.smiles, _SINGLE_FLAG],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        )
        cross_process_coords.append(json.loads(result.stdout))
    cross_process_deltas = [max_delta(cross_process_coords[0], c) for c in cross_process_coords[1:]]

    # 3. Comparison against a named frozen file, if given.
    frozen_comparison = None
    if args.compare_frozen and args.compare_frozen.is_file():
        frozen_coords = coords_of(args.compare_frozen)
        frozen_comparison = {
            "frozen_file": str(args.compare_frozen),
            "delta_vs_this_environment": max_delta(cross_process_coords[0], frozen_coords),
        }

    report = {
        "call_path_facts": facts,
        "within_process_repeat_max_delta_A": within_process_delta,
        "cross_process_max_deltas_A": cross_process_deltas,
        "cross_process_all_identical": all(d == 0.0 for d in cross_process_deltas) if cross_process_deltas else None,
        "frozen_file_comparison": frozen_comparison,
        "interpretation": (
            "If within-process and cross-process deltas are both 0, embedding is fully "
            "reproducible in THIS environment for this molecule. A nonzero delta against "
            "the frozen file then indicates the frozen file was produced under a different "
            "environment (RDKit build, OS-level math library, or hardware) at a different "
            "time -- not that RDKit's seeded embedding is inherently nondeterministic. This "
            "script cannot test 'only across machines' directly (this sandbox is one "
            "environment); that remains a disclosed, unconfirmed possibility, not a "
            "established cause."
        ),
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "diagnose_embedding_determinism_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# Embedding-determinism diagnostic",
        "",
        "## Call-path facts",
        "",
    ]
    for k, v in facts.items():
        lines.append(f"- **{k}**: {v}")
    lines += [
        "",
        "## Reproducibility tests",
        "",
        f"- Within-process repeat (2 embeddings, same process): max delta = {within_process_delta} A",
        f"- Cross-process repeats ({args.n_subprocess} fresh `python3` invocations): "
        f"max deltas vs. the first = {cross_process_deltas} A "
        f"({'all identical' if report['cross_process_all_identical'] else 'DIFFER'})",
    ]
    if frozen_comparison:
        lines.append(
            f"- Comparison against committed frozen file `{frozen_comparison['frozen_file']}`: "
            f"delta = {frozen_comparison['delta_vs_this_environment']} A"
        )
    lines += ["", report["interpretation"]]
    (args.out_dir / "diagnose_embedding_determinism_report.md").write_text("\n".join(lines), encoding="utf-8")

    for f in (tmp1, tmp2):
        f.unlink(missing_ok=True)

    print(f"Within-process delta: {within_process_delta} A")
    print(f"Cross-process deltas: {cross_process_deltas} A")
    if frozen_comparison:
        print(f"Delta vs. frozen file: {frozen_comparison['delta_vs_this_environment']} A")
    print(f"Wrote {args.out_dir / 'diagnose_embedding_determinism_report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

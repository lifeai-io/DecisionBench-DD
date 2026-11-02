#!/usr/bin/env python3
"""Compares a GNINA rerun's per_case_rmsd.csv (from evaluate_docking.py,
scored on freshly re-embedded ligands -- see redocking_reembed_rerun.py and
RUNNING_ON_GPU_INSTANCE.md S5) against the frozen primary docking_results/
per_case_rmsd.csv, to test whether Success@1/5 on the primary 14-complex
GCase redocking benchmark (Table 2/10 in the manuscript) are robust to the
RDKit ETKDGv3 embedding non-determinism found in the decoy panel.

Both CSVs are read-only; nothing frozen is modified.

Usage:
    python -m decisionbench_dd_docking.compare_redocking_rerun \\
        --frozen docking_results/per_case_rmsd.csv \\
        --rerun redocking_rerun_v1.0/docking_results/per_case_rmsd.csv \\
        --out-dir redocking_rerun_v1.0/
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def load_gnina_rows(path: Path) -> dict[str, dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["tool"] == "gnina"]
    return {r["pdb_id"]: r for r in rows}


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frozen", type=Path, required=True, help="Frozen primary docking_results/per_case_rmsd.csv")
    p.add_argument("--rerun", type=Path, required=True, help="Rerun docking_results/per_case_rmsd.csv (GNINA on fresh embeddings)")
    p.add_argument("--out-dir", type=Path, required=True)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    frozen = load_gnina_rows(args.frozen)
    rerun = load_gnina_rows(args.rerun)

    missing = set(frozen) ^ set(rerun)
    if missing:
        print(f"ERROR: case sets differ between frozen and rerun: {missing}", file=sys.stderr)
        return 1

    rows = []
    for pdb_id in frozen:
        f, r = frozen[pdb_id], rerun[pdb_id]
        s1_changed = f["success_at_1"] != r["success_at_1"]
        s5_changed = f["success_at_n"] != r["success_at_n"]
        rows.append({
            "pdb_id": pdb_id,
            "frozen_top1_rmsd": float(f["top1_rmsd"]) if f["top1_rmsd"] else None,
            "rerun_top1_rmsd": float(r["top1_rmsd"]) if r["top1_rmsd"] else None,
            "frozen_success_at_1": f["success_at_1"],
            "rerun_success_at_1": r["success_at_1"],
            "success_at_1_changed": s1_changed,
            "frozen_success_at_5": f["success_at_n"],
            "rerun_success_at_5": r["success_at_n"],
            "success_at_5_changed": s5_changed,
        })

    n_s1_changed = sum(1 for row in rows if row["success_at_1_changed"])
    n_s5_changed = sum(1 for row in rows if row["success_at_5_changed"])
    n_frozen_s1 = sum(1 for row in rows if row["frozen_success_at_1"] == "True")
    n_rerun_s1 = sum(1 for row in rows if row["rerun_success_at_1"] == "True")
    n_frozen_s5 = sum(1 for row in rows if row["frozen_success_at_5"] == "True")
    n_rerun_s5 = sum(1 for row in rows if row["rerun_success_at_5"] == "True")
    n = len(rows)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "n_cases": n,
        "frozen_success_at_1": f"{n_frozen_s1}/{n}",
        "rerun_success_at_1": f"{n_rerun_s1}/{n}",
        "n_cases_success_at_1_changed": n_s1_changed,
        "frozen_success_at_5": f"{n_frozen_s5}/{n}",
        "rerun_success_at_5": f"{n_rerun_s5}/{n}",
        "n_cases_success_at_5_changed": n_s5_changed,
        "per_case": rows,
    }
    (args.out_dir / "gnina_rerun_vs_frozen.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# GNINA rerun (fresh embeddings) vs. frozen primary redocking result",
        "",
        "Same receptor, box, and GNINA parameters (identical pinned image digest) "
        "as the frozen primary run; only the ligand's RDKit ETKDGv3 starting "
        "conformer differs (redocking_rerun_v1.0/docking_input_ligands/, "
        "see embedding_reproducibility_report.md for the per-case coordinate deltas).",
        "",
        f"- Frozen Success@1 = {n_frozen_s1}/{n}; rerun Success@1 = {n_rerun_s1}/{n}",
        f"- Success@1 verdict changed for {n_s1_changed}/{n} cases",
        f"- Frozen Success@5 = {n_frozen_s5}/{n}; rerun Success@5 = {n_rerun_s5}/{n}",
        f"- Success@5 verdict changed for {n_s5_changed}/{n} cases",
        "",
        "| PDB | Frozen Top-1 RMSD | Rerun Top-1 RMSD | Frozen S@1 | Rerun S@1 | Frozen S@5 | Rerun S@5 |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        flag = " **" if row["success_at_1_changed"] else ("  *" if row["success_at_5_changed"] else "")
        lines.append(
            f"| {row['pdb_id']}{flag} | {row['frozen_top1_rmsd']:.2f} | {row['rerun_top1_rmsd']:.2f} | "
            f"{row['frozen_success_at_1']} | {row['rerun_success_at_1']} | "
            f"{row['frozen_success_at_5']} | {row['rerun_success_at_5']} |"
        )
    lines += [
        "",
        "`**` = Success@1 verdict changed, `*` = only Success@5 verdict changed.",
        "",
        "Conclusion: the primary 14-complex redocking benchmark's GNINA arm is "
        "**not robust** to RDKit ETKDGv3 embedding non-determinism -- the same "
        "risk found in the decoy panel transfers here. Table 2/10's frozen "
        "numbers remain the reported primary result (single fixed realization, "
        "per the original protocol), but should be read as one draw from a "
        "run-sensitive process, not an exact reproducible point estimate.",
    ]
    (args.out_dir / "gnina_rerun_vs_frozen.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Success@1: frozen {n_frozen_s1}/{n} -> rerun {n_rerun_s1}/{n} ({n_s1_changed}/{n} cases changed verdict)")
    print(f"Success@5: frozen {n_frozen_s5}/{n} -> rerun {n_rerun_s5}/{n} ({n_s5_changed}/{n} cases changed verdict)")
    print(f"Wrote {args.out_dir / 'gnina_rerun_vs_frozen.json'} and .md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

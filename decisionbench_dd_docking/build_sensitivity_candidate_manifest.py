#!/usr/bin/env python3
"""Builds a candidate_manifest.csv (same schema as decisionbench_dd_configs_v1.0/
candidate_screen_v1.0/candidate_manifest.csv) for the MolMIM min_similarity=0.5/0.7
sensitivity rerun's chemically-qualified molecules, so they can be pushed through the
same candidate-screen docking/scoring pipeline as the frozen primary 69 candidates
WITHOUT touching any frozen primary file.

Reads results_sensitivity/molmim_sim<X>/molecule_level.csv (written by
decisionbench_dd_eval.evaluate_generators against the sensitivity reruns) and keeps
rows with qualified=True, in their original per-replicate order (row order in that
CSV matches the raw API response order, since evaluate_generators.py appends rows in
iteration order over run.molecules).

Candidate IDs use a distinct prefix (MM5_/MM7_) so they cannot collide with or be
confused with the frozen primary MM_001-MM_003 candidates.

Writes THREE files: a combined candidate_manifest.csv (all 12; convenient for the
one-shot ligand-preparation/docking batch, which doesn't care about denominators)
and two per-setting candidate_manifest_sim<X>.csv files (2 and 10 rows respectively;
use these, not the combined file, when SCORING with score_candidate_screen.py --
each setting independently requested 300 molecules, so mixing them under one
candidate_manifest at scoring time would silently compute Y_structural_proxy against
the wrong/mixed denominator).

Usage:
    python -m decisionbench_dd_docking.build_sensitivity_candidate_manifest
"""
from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "candidate_screen_v1.0" / "sensitivity_rerun"
OUT_CSV_COMBINED = OUT_DIR / "candidate_manifest.csv"

SOURCES = [
    ("MM5", "sim0.5", REPO_ROOT / "results_sensitivity" / "molmim_sim0.5" / "molecule_level.csv"),
    ("MM7", "sim0.7", REPO_ROOT / "results_sensitivity" / "molmim_sim0.7" / "molecule_level.csv"),
]

FIELDS = [
    "candidate_id", "tool", "run", "returned_rank", "canonical_smiles",
    "generator_score", "ecfp4_tanimoto", "qed_value", "sa_value", "mw_da",
    "clogp_value", "tpsa_a2", "brenk_alerts",
]

RUN_ID_TO_INT = {"replicate_01": 1, "replicate_02": 2, "replicate_03": 3}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    combined_rows = []

    for prefix, setting_label, csv_path in SOURCES:
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = list(csv.DictReader(fh))

        per_run_rank: dict[str, int] = {}
        n = 0
        setting_rows = []
        for row in reader:
            run_id = row["run_id"]
            per_run_rank[run_id] = per_run_rank.get(run_id, 0) + 1
            if row["qualified"] != "True":
                continue
            n += 1
            setting_rows.append({
                "candidate_id": f"{prefix}_{n:03d}",
                "tool": "molmim",
                "run": RUN_ID_TO_INT.get(run_id, run_id),
                "returned_rank": per_run_rank[run_id],
                "canonical_smiles": row["canonical_smiles"],
                "generator_score": row["api_score"],
                "ecfp4_tanimoto": row["tanimoto_to_seed"],
                "qed_value": row["qed"],
                "sa_value": row["sa_score"],
                "mw_da": row["mw"],
                "clogp_value": row["clogp"],
                "tpsa_a2": row["tpsa"],
                "brenk_alerts": row["brenk_alerts_all"],
            })

        per_setting_csv = OUT_DIR / f"candidate_manifest_{setting_label}.csv"
        with open(per_setting_csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(setting_rows)
        print(f"Wrote {len(setting_rows)} candidates to {per_setting_csv} (score with --candidate-manifest, denominator=300)")

        combined_rows.extend(setting_rows)

    with open(OUT_CSV_COMBINED, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(combined_rows)
    print(f"Wrote {len(combined_rows)} combined candidates to {OUT_CSV_COMBINED} (ligand-prep/docking convenience file only -- do NOT use for scoring)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

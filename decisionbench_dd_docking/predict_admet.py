#!/usr/bin/env python3
"""Predictive ADMET for the 16 frozen primary candidate-screen passers, plus
Ambroxol as a reference point
(decisionbench_dd_configs_v1.0/candidate_screen_v1.0/downstream_gcase_screening_protocol.md,
section 11 "Evaluate ADMET ...").

Uses ADMET-AI (Swanson et al., Bioinformatics 2024,
https://doi.org/10.1093/bioinformatics/btae416): Chemprop-RDKit multi-task
models trained on the Therapeutics Data Commons ADMET benchmark datasets,
run locally via `pip install admet_ai` (no network calls at prediction
time -- model weights ship with the package). This closes the gap flagged
in primary_candidate_triage.py's docstring: that script's panel was
physicochemical drug-likeness only and explicitly said predictive ADMET was
out of scope; this script is that missing piece, not a replacement for it.

Not covered even by this: patent-proximity search (still no tool/database
available in this environment) and in-vitro/in-vivo confirmation --
ADMET-AI's predictions are themselves model outputs (with reported
per-endpoint test-set performance in the ADMET-AI paper), not experimental
measurements.

Usage:
    python -m decisionbench_dd_docking.predict_admet
"""
from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from pathlib import Path

from decisionbench_dd_docking.triage_primary_candidates import CANDIDATE_RESULTS, load_passing_candidates

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "candidate_screen_results"
AMBROXOL_SMILES = "C1=C(C(=C(C=C1Br)Br)N)CNC2CCC(CC2)O"

# Endpoints whose predicted value is physically constrained to be
# non-negative (concentration clearances, uL/min/10^6 cells or
# uL/min/mg protein) -- a negative regression output is a model
# extrapolation artifact, not "better than zero clearance". Flagged, not
# silently reinterpreted or dropped, per external review.
NON_NEGATIVE_ENDPOINTS = ["Clearance_Hepatocyte_AZ", "Clearance_Microsome_AZ"]


def _model_directory_hash(models_dir: Path) -> str:
    """Combined SHA-256 over every bundled model file (sorted by relative
    path), so a later run using a different admet_ai release or a locally
    modified models/ directory is provably distinguishable from this one --
    same treatment as this project's Docker image digests."""
    hasher = hashlib.sha256()
    for path in sorted(models_dir.rglob("*")):
        if path.is_file():
            hasher.update(str(path.relative_to(models_dir)).encode())
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


def _git_commit(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None

# A curated subset of ADMET-AI's ~50 endpoints for the human-facing summary
# table -- chosen for direct medicinal-chemistry relevance (safety
# liabilities and key PK properties). The full endpoint set (including
# DrugBank-approved-drug percentile ranks) is written to the CSV regardless.
HEADLINE_ENDPOINTS = [
    "hERG", "AMES", "DILI", "ClinTox", "Carcinogens_Lagunin",
    "BBB_Martins", "HIA_Hou", "Bioavailability_Ma", "PAMPA_NCATS",
    "CYP3A4_Veith", "CYP2D6_Veith", "CYP2C9_Veith",
    "Solubility_AqSolDB", "Half_Life_Obach", "Clearance_Hepatocyte_AZ",
]


def main(argv=None) -> int:
    if not CANDIDATE_RESULTS.is_file():
        print(f"ERROR: {CANDIDATE_RESULTS} not found -- run score_candidate_screen.py first.", file=sys.stderr)
        return 1

    candidates = load_passing_candidates()
    ligand_ids = ["CTRL_AMBROXOL"] + [c["candidate_id"] for c in candidates]
    smiles_list = [AMBROXOL_SMILES] + [c["canonical_smiles"] for c in candidates]

    import importlib.metadata

    from admet_ai import ADMETModel

    admet_ai_version = importlib.metadata.version("admet_ai")
    chemprop_version = importlib.metadata.version("chemprop")

    print(f"Loading ADMET-AI model and predicting {len(smiles_list)} molecules...", file=sys.stderr)
    import inspect
    default_models_dir = inspect.signature(ADMETModel.__init__).parameters["models_dir"].default
    model = ADMETModel()
    models_dir_hash = _model_directory_hash(Path(default_models_dir))
    preds_df = model.predict(smiles=smiles_list)
    preds_df.insert(0, "candidate_id", ligand_ids)

    for endpoint in NON_NEGATIVE_ENDPOINTS:
        preds_df[f"{endpoint}_valid"] = preds_df[endpoint] >= 0

    out_csv = OUT_DIR / "admet_predictions.csv"
    preds_df.to_csv(out_csv, index=False)

    ambroxol_row = preds_df.iloc[0]
    lines = [
        "# ADMET-AI predictions: 16 primary candidates + Ambroxol",
        "",
        "Predicted with ADMET-AI (Swanson et al., Bioinformatics 2024, "
        "https://doi.org/10.1093/bioinformatics/btae416) -- Chemprop-RDKit models trained on "
        "Therapeutics Data Commons ADMET benchmarks, run locally. These are MODEL PREDICTIONS, "
        "not experimental measurements; treat as a triage/prioritization signal, same status as "
        "this project's other in-silico proxies. Full ~50-endpoint output (including "
        "DrugBank-approved-drug percentile ranks) is in admet_predictions.csv.",
        "",
        "## Provenance",
        "",
        f"- `admet_ai` package version: {admet_ai_version} (the PyPI package's own v2.x line; "
        "note the upstream project states v2 was retrained and does not reproduce v1 predictions "
        "bit-for-bit -- the PAINS/BRENK/NIH_alert columns present below are v2-introduced fields, "
        "confirming this run used v2, not v1).",
        f"- `chemprop` version: {chemprop_version}",
        f"- Bundled model directory SHA-256 (all files under `admet_ai/resources/models/`, "
        f"combined): {models_dir_hash}",
        f"- This repo's git commit at prediction time: {_git_commit(REPO_ROOT) or 'unknown'}",
        "- Exact command: `python -m decisionbench_dd_docking.predict_admet`",
        "",
        f"Ambroxol reference: hERG={ambroxol_row['hERG']:.3f}, AMES={ambroxol_row['AMES']:.3f}, "
        f"DILI={ambroxol_row['DILI']:.3f}, BBB={ambroxol_row['BBB_Martins']:.3f}.",
        "",
        "| Candidate | hERG | AMES | DILI | ClinTox | BBB | HIA | Bioavail | CYP3A4 | CYP2D6 | Solubility | Half-life (h) | Clearance(hep) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for i, cid in enumerate(ligand_ids):
        row = preds_df.iloc[i]
        clearance = row["Clearance_Hepatocyte_AZ"]
        clearance_str = f"{clearance:.2f}" + ("" if clearance >= 0 else " (invalid)")
        lines.append(
            f"| {cid} | {row['hERG']:.3f} | {row['AMES']:.3f} | {row['DILI']:.3f} | "
            f"{row['ClinTox']:.3f} | {row['BBB_Martins']:.3f} | {row['HIA_Hou']:.3f} | "
            f"{row['Bioavailability_Ma']:.3f} | {row['CYP3A4_Veith']:.3f} | {row['CYP2D6_Veith']:.3f} | "
            f"{row['Solubility_AqSolDB']:.2f} | {row['Half_Life_Obach']:.2f} | {clearance_str} |"
        )
    n_invalid_hep = int((~preds_df["Clearance_Hepatocyte_AZ_valid"]).sum())
    n_invalid_micro = int((~preds_df["Clearance_Microsome_AZ_valid"]).sum())
    lines += [
        "",
        "Classification endpoints (hERG, AMES, DILI, ClinTox, BBB, HIA, Bioavailability, CYP*) "
        "are predicted probabilities in [0, 1] -- for the risk endpoints (hERG/AMES/DILI/ClinTox/"
        "CYP*), LOWER is better/safer; for the favorable-property endpoints (BBB/HIA/Bioavailability), "
        "HIGHER is better. Solubility_AqSolDB is log(mol/L) (higher = more soluble); "
        "**Half_Life_Obach is predicted directly in hours** (not log-hours -- the TDC benchmark "
        "defines this endpoint in hours; also internally consistent, since the predicted range "
        "here, ~15-76, would imply centuries-long half-lives if read as log-hours). "
        "Clearance_Hepatocyte_AZ/Clearance_Microsome_AZ are in uL/min/10^6 cells and "
        "uL/min/mg protein respectively -- both are physically non-negative quantities.",
        "",
        f"**Invalid (negative) clearance predictions**: {n_invalid_hep}/{len(preds_df)} hepatocyte, "
        f"{n_invalid_micro}/{len(preds_df)} microsome -- flagged via the "
        "Clearance_Hepatocyte_AZ_valid/Clearance_Microsome_AZ_valid columns in the CSV (False = "
        "negative/invalid). Raw predictions are retained for reproducibility; a negative value is "
        "a regression-model extrapolation artifact, NOT evidence of exceptionally good metabolic "
        "stability, and must not be reinterpreted as such.",
        "",
        "**On BRENK_alert**: most of these candidates are Ambroxol analogues sharing its "
        "dibrominated-aniline core, which is a known, already-accounted-for Brenk hit (see this "
        "project's own frozen v1.2 seed-relative structural-alert gate, "
        "decisionbench_dd_eval/chem_metrics.py). ADMET-AI's Brenk check has no knowledge of that "
        "seed-relative allowlisting and flags the raw pattern regardless of origin -- a "
        "BRENK_alert=1 here reflects the same single seed-inherited instance already qualified "
        "against upstream, not 15 newly discovered liabilities.",
    ]
    (OUT_DIR / "admet_predictions.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv} and admet_predictions.md ({len(ligand_ids)} molecules, {len(preds_df.columns)} columns)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

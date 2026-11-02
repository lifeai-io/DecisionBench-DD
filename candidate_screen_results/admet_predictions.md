# ADMET-AI predictions: 16 primary candidates + Ambroxol

Predicted with ADMET-AI (Swanson et al., Bioinformatics 2024, https://doi.org/10.1093/bioinformatics/btae416) -- Chemprop-RDKit models trained on Therapeutics Data Commons ADMET benchmarks, run locally. These are MODEL PREDICTIONS, not experimental measurements; treat as a triage/prioritization signal, same status as this project's other in-silico proxies. Full ~50-endpoint output (including DrugBank-approved-drug percentile ranks) is in admet_predictions.csv.

## Provenance

- `admet_ai` package version: 2.0.1 (the PyPI package's own v2.x line; note the upstream project states v2 was retrained and does not reproduce v1 predictions bit-for-bit -- the PAINS/BRENK/NIH_alert columns present below are v2-introduced fields, confirming this run used v2, not v1).
- `chemprop` version: 2.3.1
- Bundled model directory SHA-256 (all files under `admet_ai/resources/models/`, combined): c59e05b031647125063b558d7c839b9100e3988b26c70fc2960928fc8ee32bb9
- This repo's git commit at prediction time: b277d3cfb4155049a17289c12a64241c008860f4
- Exact command: `python -m decisionbench_dd_docking.predict_admet`

Ambroxol reference: hERG=0.798, AMES=0.168, DILI=0.142, BBB=0.922.

| Candidate | hERG | AMES | DILI | ClinTox | BBB | HIA | Bioavail | CYP3A4 | CYP2D6 | Solubility | Half-life (h) | Clearance(hep) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CTRL_AMBROXOL | 0.798 | 0.168 | 0.142 | 0.222 | 0.922 | 0.999 | 0.798 | 0.075 | 0.781 | -2.33 | 52.29 | 25.45 |
| GM_007 | 0.885 | 0.118 | 0.152 | 0.270 | 0.940 | 0.999 | 0.753 | 0.077 | 0.812 | -2.82 | 76.44 | 49.45 |
| GM_015 | 0.759 | 0.040 | 0.587 | 0.139 | 0.729 | 1.000 | 0.767 | 0.534 | 0.498 | -4.19 | 58.79 | 62.49 |
| GM_024 | 0.851 | 0.160 | 0.213 | 0.355 | 0.920 | 0.999 | 0.782 | 0.171 | 0.401 | -2.82 | 48.06 | 52.44 |
| GM_031 | 0.840 | 0.703 | 0.335 | 0.319 | 0.961 | 1.000 | 0.853 | 0.317 | 0.634 | -2.79 | 52.97 | 36.93 |
| GM_032 | 0.781 | 0.749 | 0.573 | 0.260 | 0.949 | 1.000 | 0.895 | 0.450 | 0.355 | -2.64 | 53.24 | 37.32 |
| GM_033 | 0.852 | 0.396 | 0.400 | 0.241 | 0.909 | 1.000 | 0.881 | 0.413 | 0.447 | -2.52 | 59.65 | 42.21 |
| GM_034 | 0.857 | 0.189 | 0.198 | 0.188 | 0.899 | 0.999 | 0.761 | 0.225 | 0.815 | -2.69 | 54.36 | 27.17 |
| GM_035 | 0.766 | 0.256 | 0.269 | 0.182 | 0.825 | 0.999 | 0.825 | 0.213 | 0.486 | -2.15 | 54.76 | 25.55 |
| GM_039 | 0.919 | 0.131 | 0.247 | 0.185 | 0.894 | 1.000 | 0.717 | 0.475 | 0.859 | -3.30 | 54.97 | 38.34 |
| GM_047 | 0.776 | 0.654 | 0.442 | 0.288 | 0.941 | 1.000 | 0.776 | 0.599 | 0.647 | -2.75 | 41.86 | 38.17 |
| GM_053 | 0.315 | 0.127 | 0.281 | 0.235 | 0.551 | 0.808 | 0.740 | 0.031 | 0.239 | -2.27 | 15.30 | -0.66 (invalid) |
| GM_054 | 0.919 | 0.402 | 0.066 | 0.103 | 0.789 | 0.968 | 0.623 | 0.132 | 0.535 | -1.85 | 48.84 | -1.35 (invalid) |
| GM_055 | 0.987 | 0.389 | 0.427 | 0.312 | 0.933 | 1.000 | 0.695 | 0.905 | 0.980 | -3.96 | 58.68 | 18.86 |
| GM_057 | 0.352 | 0.126 | 0.181 | 0.221 | 0.540 | 0.784 | 0.704 | 0.026 | 0.269 | -2.41 | 15.66 | 1.10 |
| GM_064 | 0.918 | 0.129 | 0.371 | 0.269 | 0.853 | 1.000 | 0.634 | 0.629 | 0.859 | -3.80 | 59.49 | 37.59 |
| MM_002 | 0.783 | 0.366 | 0.269 | 0.192 | 0.918 | 0.998 | 0.586 | 0.504 | 0.793 | -3.38 | 44.14 | 36.36 |

Classification endpoints (hERG, AMES, DILI, ClinTox, BBB, HIA, Bioavailability, CYP*) are predicted probabilities in [0, 1] -- for the risk endpoints (hERG/AMES/DILI/ClinTox/CYP*), LOWER is better/safer; for the favorable-property endpoints (BBB/HIA/Bioavailability), HIGHER is better. Solubility_AqSolDB is log(mol/L) (higher = more soluble); **Half_Life_Obach is predicted directly in hours** (not log-hours -- the TDC benchmark defines this endpoint in hours; also internally consistent, since the predicted range here, ~15-76, would imply centuries-long half-lives if read as log-hours). Clearance_Hepatocyte_AZ/Clearance_Microsome_AZ are in uL/min/10^6 cells and uL/min/mg protein respectively -- both are physically non-negative quantities.

**Invalid (negative) clearance predictions**: 2/17 hepatocyte, 6/17 microsome -- flagged via the Clearance_Hepatocyte_AZ_valid/Clearance_Microsome_AZ_valid columns in the CSV (False = negative/invalid). Raw predictions are retained for reproducibility; a negative value is a regression-model extrapolation artifact, NOT evidence of exceptionally good metabolic stability, and must not be reinterpreted as such.

**On BRENK_alert**: most of these candidates are Ambroxol analogues sharing its dibrominated-aniline core, which is a known, already-accounted-for Brenk hit (see this project's own frozen v1.2 seed-relative structural-alert gate, decisionbench_dd_eval/chem_metrics.py). ADMET-AI's Brenk check has no knowledge of that seed-relative allowlisting and flags the raw pattern regardless of origin -- a BRENK_alert=1 here reflects the same single seed-inherited instance already qualified against upstream, not 15 newly discovered liabilities.

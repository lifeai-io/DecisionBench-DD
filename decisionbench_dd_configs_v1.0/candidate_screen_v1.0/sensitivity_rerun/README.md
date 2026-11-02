# GNINA candidate-screen re-run for the MolMIM min_similarity sensitivity candidates

Everything in this directory is already prepared (no GPU needed for this part) and
committed: `candidate_manifest.csv` (12 candidates, MM5_001-002 from
`min_similarity=0.5`, MM7_001-010 from `min_similarity=0.7`), the per-setting
`candidate_manifest_sim0.5.csv` / `candidate_manifest_sim0.7.csv` (**use these for
scoring**, not the combined file -- see below), `ligand_microstate_manifest.csv`
(32 rows: 16 ligands x 2 receptor states, includes the 4 frozen controls, 0
ambiguous/embed failures), and `docking_input_ligands/` (32 prepared 3D SDFs).

Built by `decisionbench_dd_docking.build_sensitivity_candidate_manifest` +
`decisionbench_dd_docking.prepare_candidate_screen_ligands` -- see
`decisionbench_dd_configs_v1.0/molmim_sensitivity_amendment_log.md` for full
provenance of the underlying MolMIM reruns.

## What's left: run on a GPU machine with Docker

**1. Dock (32 GNINA jobs, same digest-pinned image/config as the frozen 146-job
primary screen):**

```bash
python -m decisionbench_dd_docking.run_candidate_screen_gnina \
    --microstate-manifest decisionbench_dd_configs_v1.0/candidate_screen_v1.0/sensitivity_rerun/ligand_microstate_manifest.csv \
    --out-dir candidate_screen_runs_sensitivity/
```

**2. Score each setting SEPARATELY** (both settings independently requested 300
molecules from MolMIM -- scoring them together under one candidate_manifest would
silently divide by the wrong denominator when computing Y_structural_proxy):

```bash
python -m decisionbench_dd_docking.score_candidate_screen \
    --runs-dir candidate_screen_runs_sensitivity/ \
    --candidate-manifest decisionbench_dd_configs_v1.0/candidate_screen_v1.0/sensitivity_rerun/candidate_manifest_sim0.5.csv \
    --microstate-manifest decisionbench_dd_configs_v1.0/candidate_screen_v1.0/sensitivity_rerun/ligand_microstate_manifest.csv \
    --out-dir candidate_screen_results_sensitivity/sim0.5/

python -m decisionbench_dd_docking.score_candidate_screen \
    --runs-dir candidate_screen_runs_sensitivity/ \
    --candidate-manifest decisionbench_dd_configs_v1.0/candidate_screen_v1.0/sensitivity_rerun/candidate_manifest_sim0.7.csv \
    --microstate-manifest decisionbench_dd_configs_v1.0/candidate_screen_v1.0/sensitivity_rerun/ligand_microstate_manifest.csv \
    --out-dir candidate_screen_results_sensitivity/sim0.7/
```

Each `summary.md`/`summary.json` will report `Y_structural_proxy` for MolMIM at
that setting (of 300 requested), comparable to the frozen primary run's 0.33%
(1/300) at `min_similarity=0.3` and GenMol's 5.00% (15/300).

## Do not touch the frozen primary files

`--candidate-manifest`/`--microstate-manifest`/`--ligand-dir` all default to the
frozen primary paths when omitted, so existing invocations of
`prepare_candidate_screen_ligands.py`, `run_candidate_screen_gnina.py`, and
`score_candidate_screen.py` (no extra flags) are unaffected. Do **not** run
`prepare_candidate_screen_ligands.py` with no arguments as a "test" -- RDKit's
ETKDGv3 embedding is not byte-stable across reruns even with a fixed seed, so it
will silently rewrite (not literally corrupt, but change) the frozen primary
`docking_input_ligands/*.sdf` files on disk. If that happens, `git checkout --
decisionbench_dd_configs_v1.0/candidate_screen_v1.0/docking_input_ligands/`
restores them.

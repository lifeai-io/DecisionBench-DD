# DecisionBench-DD

AI tools for drug discovery should not be selected solely by isolated model-level benchmark scores. Tool selection should instead be based on task-specific success criteria, operational constraints, and downstream decision behavior.

**DecisionBench-DD v1.0** is a task-specific evaluation framework that measures generator and docking-tool performance within a frozen, auditable discovery funnel rather than by isolated component metrics. It is instantiated here as an ambroxol-conditioned human glucocerebrosidase (GCase / *GBA1*) case study comparing two molecular generators (GenMol, MolMIM) and two docking tools (GNINA, DiffDock-L). Every gate, threshold, and scoring rule is version-controlled and frozen before the corresponding experiment runs; amendments are logged with a rationale and a before/after-seeing-results flag.

This repository supports two accepted NeurIPS 2026 workshop papers built on the same frozen pipeline and raw data:

- **AI for Drug Discovery -- Bridging the Translation Gap (AI4DD):** *"From Model Scores to Discovery Decisions: Decision-Contract Evaluation of Tools for Molecular Generation and Docking"* -- `manuscript/paper/` (compiled PDF in the same directory). The core generation/docking/candidate-screening methodology and case study.
- **Agentic AI for Biological Discovery: Toward Closed-Loop Life-Science Intelligence (AgenticLS):** *"From Model Scores to Defensible Agent Decisions: Decision Contracts for Molecular Generation and Docking"* -- `manuscript/paper_agenticls/` (compiled PDF in the same directory). Extends the same decision-contract framework to a purchasable-catalogue retrieval baseline and an LLM-agent evidence-semantics probe.

## Repository layout

| Path | Contents |
| --- | --- |
| `decisionbench_dd_configs_v1.0/` | Frozen protocols, gate definitions, seed/alert catalogs, the 14-complex GCase validation set, and the candidate-screen package (manifests, receptor states, docking boxes, experimental-validation panel, purchasable-catalogue retrieval baseline, property-matched decoy panel). |
| `decisionbench_dd_eval/` | Generator-side pipeline: run generation requests, score every molecule with a common evaluator, apply the frozen chemical gates. |
| `decisionbench_dd_docking/` | Docking-side pipeline: GNINA/DiffDock-L runners, pose validity and RMSD scoring, reranking-sensitivity analyses, candidate-screen scoring, ADMET-AI prediction, and patent/purchasable-catalog membership checks. |
| `decisionbench_dd_agentic/` | LLM-agent evidence-semantics probe (AgenticLS paper): protocol, raw transcripts (free-form / prose-guidance / explicit decision-contract conditions, n=5 and n=50 replicate designs), grading, blinded second-rater checks, and significance tests. |
| `runs/`, `results/` | Raw generator API outputs and the generator scorecard / chemical-gate audit derived from them. |
| `runs_sensitivity/`, `results_sensitivity/` | Post-hoc MolMIM `min_similarity` sensitivity rerun and its scored results. |
| `docking_runs/`, `docking_results/` | Raw GNINA/DiffDock-L poses for the 14-case redocking benchmark and the scored results. |
| `redocking_rerun_v1.0/`, `embedding_determinism_diagnostic/` | Fresh-embedding redocking rerun and the diagnostic isolating ligand-embedding non-determinism as a contributing cause. |
| `candidate_screen_runs/`, `candidate_screen_results/` | Raw poses for the 146-job candidate screen and the scored results (structural triage, ADMET, patent membership, reranking sensitivity). |
| `candidate_screen_runs_sensitivity/`, `candidate_screen_results_sensitivity/` | Candidate-screen scoring under the MolMIM sensitivity rerun. |
| `decoy_panel_results/` | Property-matched decoy panel scored against the frozen structural-proxy gate (background-discrimination check). |
| `manuscript/` | The two final paper directories described above. |
| `GCASE_VALIDATION_SET.md` | Design rationale for the redocking validation set. |
| `Formatting_Instructions_For_NeurIPS_2026/` | Official NeurIPS 2026 LaTeX formatting instructions and style file, for reference. |

Every stage's outputs are version-controlled alongside the code that produced them, so any step below can be re-scored from the committed raw outputs without rerunning the (GPU- or hosted-API-dependent) upstream step.

## Setup

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install --no-deps dimorphite_dl==2.0.2
```

`dimorphite_dl` is installed separately with `--no-deps`: its published metadata
declares `rdkit<2026`, which makes pip's resolver reject the whole install once
`rdkit==2026.3.5` (pinned in `requirements.txt`) is also requested, even though
dimorphite_dl 2.0.2 runs correctly against rdkit 2026.3.5 in practice. `--no-deps`
skips that stale check; its only other dependency, `loguru`, is already pinned in
`requirements.txt` so nothing is left missing.

Two steps additionally require external resources that are **not** bundled in this repository:

- **Molecule generation** (`decisionbench_dd_eval/run_generation.py`) calls the hosted NVIDIA GenMol/MolMIM NIM APIs and needs an `NGC_API_KEY` environment variable (e.g. in a local, gitignored `.env` file). Not required if you only want to re-score the already-archived raw outputs in `runs/`.
- **Docking** (`decisionbench_dd_docking/run_gnina.py`, `run_diffdock.py`, `run_candidate_screen_gnina.py`) requires Docker with GPU passthrough (`--gpus all`) and pulls the `gnina/gnina` and `rbgcsail/diffdock` images. Not required if you only want to re-score the already-archived poses in `docking_runs/` and `candidate_screen_runs/`.

## Reproducing the results

Each step reads frozen configuration from `decisionbench_dd_configs_v1.0/` and writes to the output directory named below; re-running a scoring step against the already-archived raw outputs (skipping the "requires GPU/API" steps) reproduces every number in both papers deterministically.

**1. Generator benchmark (Experiment A).**
```bash
python -m decisionbench_dd_eval.run_generation --tool both --replicates 3   # requires NGC_API_KEY; writes runs/
python -m decisionbench_dd_eval.evaluate_generators                        # writes results/ (Table 1)
```

**2. GCase redocking benchmark (Experiment B).**
```bash
python -m decisionbench_dd_docking.run_gnina        # requires Docker+GPU; writes docking_runs/gnina/
python -m decisionbench_dd_docking.run_diffdock     # requires Docker+GPU; writes docking_runs/diffdock/
python -m decisionbench_dd_docking.evaluate_docking --poses-dir docking_runs   # writes docking_results/ (Table 2)
python -m decisionbench_dd_docking.redocking_rerank_sensitivity --poses-dir docking_runs   # bounded reranking-sensitivity analysis
```

**3. Candidate screening and downstream characterization.**
```bash
python -m decisionbench_dd_docking.run_candidate_screen_gnina   # requires Docker+GPU; writes candidate_screen_runs/
python -m decisionbench_dd_docking.score_candidate_screen --runs-dir candidate_screen_runs  # writes candidate_screen_results/ (Table 3)
python -m decisionbench_dd_docking.candidate_screen_rerank_sensitivity --runs-dir candidate_screen_runs  # reranking-sensitivity analysis
python -m decisionbench_dd_docking.triage_primary_candidates                                 # diversity/physicochemical triage
python -m decisionbench_dd_docking.predict_admet                                             # requires admet_ai; ADMET-AI predictions
python -m decisionbench_dd_docking.check_patent_membership                                   # requires molbloom; SureChEMBL/ZINC membership
```

**4. Purchasable-catalogue retrieval baseline and LLM-agent evidence-semantics probe (AgenticLS paper).**
```bash
python decisionbench_dd_configs_v1.0/candidate_screen_v1.0/catalogue_baseline_v1.0/build_catalogue_baseline.py   # rescoring only; raw ZINC tranches are not bundled (see the script's README.md for the source/regeneration procedure)
python decisionbench_dd_configs_v1.0/candidate_screen_v1.0/catalogue_baseline_v1.0/scaffold_diversity_check.py
```
The agent-probe transcripts, grading rubric, blinded second-rater checks, and significance tests are static, already-scored artifacts in `decisionbench_dd_agentic/agent_eval_v1.0/` (see `protocol.md` and `scoring.md`); `significance_check.py` reproduces the reported p-values from the recorded compliance counts.

## Running the test suite

```bash
pip install pytest
pytest decisionbench_dd_eval/tests decisionbench_dd_docking/tests
```

## Provenance and amendments

All thresholds and scoring rules are frozen in `decisionbench_dd_configs_v1.0/` before the corresponding experiment (`qualification_gates_v1.0.json`, `gcase_validation/redocking_protocol_v1.0.json`, `candidate_screen_v1.0/downstream_gcase_screening_protocol.md`). Any subsequent amendment is logged in that same file with a dated rationale and a flag stating whether it was made before or after inspecting results; mechanical corrections (representation-artifact fixes that leave coordinates, ranks, and connectivity unchanged) are documented separately from analytical amendments (threshold or gate-logic changes). See each paper's appendices for a condensed, verified audit trail of every gate, run, and correction referenced in it.

## License

MIT -- see `LICENSE`.

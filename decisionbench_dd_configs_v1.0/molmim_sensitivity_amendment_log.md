# MolMIM min_similarity sensitivity rerun (post-hoc, reviewer-requested)

**Status: exploratory, run AFTER inspecting primary results and AI4DD reviewer feedback.** This
is not part of the frozen primary protocol (`molmim_primary.json`, `min_similarity=0.3`) and is
reported as such in the manuscript. It exists to test whether the primary-run qualified-yield
reversal (GenMol 66/300 vs. MolMIM 3/300) is an artifact of the specific `min_similarity=0.3`
request parameter.

**What changed vs. the frozen primary request.** Identical seed SMILES, identical
`num_molecules=100`, identical `algorithm=CMA-ES`/`property_name=QED`/`particles=100`/
`iterations=10`, three independent replicates per setting, same downstream evaluator and frozen
qualification gates (`qualification_gates_v1.0.json` v1.2, unmodified) — only `min_similarity` is
overridden, to 0.5 and then 0.7, run via `decisionbench_dd_eval/run_generation_sensitivity.py`
into `runs_sensitivity/molmim_sim0.5/` and `runs_sensitivity/molmim_sim0.7/`, scored into
`results_sensitivity/molmim_sim0.5/` and `results_sensitivity/molmim_sim0.7/`.

**Result (chemical qualification).** Qualified yield (of 300 requested): 1.0% (3/300) at 0.3
[primary], 0.7% (2/300) at 0.5, 3.3% (10/300) at 0.7. Median externally-recomputed ECFP4
Tanimoto-to-seed stayed ~0.167 across all three settings, consistent with the primary-run
observation that `min_similarity` does not impose a hard floor as measured by our independent
RDKit recomputation. The reversal against GenMol's 22.0% qualified yield persists at every tested
setting; it narrows at 0.7 but is not eliminated. Full per-replicate counts are in the manuscript,
Appendix A.

**Result (end-to-end GNINA re-screen).** The chemically-qualified candidates above were carried
through the identical candidate-screen pipeline (same digest-pinned GNINA image, boxes, and gate;
`decisionbench_dd_docking/prepare_candidate_screen_ligands.py` / `run_candidate_screen_gnina.py` /
`score_candidate_screen.py`, run on a separate GPU machine -- see
`decisionbench_dd_configs_v1.0/candidate_screen_v1.0/sensitivity_rerun/`). End-to-end
structural-proxy yield: 0.33% (1/300) at 0.3 [primary], 0.00% (0/300) at 0.5, 0.67% (2/300) at 0.7,
versus GenMol's fixed 5.00% (15/300, unaffected by this rerun since only MolMIM was regenerated).
The full end-to-end reversal persists at every tested setting. Full results in
`candidate_screen_results_sensitivity/sim0.5/` and `sim0.7/`; manuscript Appendix A.

Note: the re-scored Ambroxol CNNaffinity threshold at 3KEH (6.2047) differed slightly from the
primary run's (6.2056) -- most likely GPU-hardware-dependent floating-point variation in GNINA's
CNN scoring across the two different machines, rather than nondeterminism within one machine (the
paper's existing byte-identical-reproducibility claims, e.g. for DiffDock-L, are scoped to repeated
runs on the same machine/environment, not cross-machine). The 0.0009 drift is far smaller than any
candidate's pass/fail margin in this rerun and does not change which candidates pass.

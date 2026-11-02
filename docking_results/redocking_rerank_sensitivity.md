# Redocking Success@1 under fixed, pre-specified pose selectors

Sensitivity analysis only -- does not change the frozen primary result (docking_results/summary.md: GNINA Success@1 = 21.4%, Success@5 = 57.1%). No selector was chosen based on these outcomes; all three were pre-specified in redocking_protocol_v1.0.json/downstream_gcase_screening_protocol.md section 10 before this analysis was run.

| Selector | Success@1 (n=14) | Median RMSD |
| --- | ---: | ---: |
| native_rank1 | 3/14 (21.4%), scored=14/14 | 4.64 A |
| cnn_vs_desc | 4/14 (28.6%), scored=14/14 | 3.80 A |
| minimized_affinity_asc | 5/14 (35.7%), scored=14/14 | 3.74 A |

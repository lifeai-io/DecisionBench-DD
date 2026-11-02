# Candidate-screen reranking-sensitivity analysis

Sensitivity analysis only -- does not change the frozen primary result (candidate_screen_results/summary.md: 15 GenMol + 1 MolMIM structural-proxy pass). Neither the best-of-5 bar nor the three selectors below were chosen based on these outcomes.

## Best-of-5 rescue (fixed pass bar: geometry valid, active-site occupied, CNNaffinity >= Ambroxol native-rank1 = 6.206)

- Native rank-1 passes: 16/69
- Best-of-5 passes (any of 5 poses): 27/69
- Rescued by looking past rank 1: 11 (GM_009, GM_017, GM_026, GM_028, GM_036, GM_041, GM_042, GM_043, GM_046, GM_051, GM_066)

## Fixed-selector sensitivity (Y_structural_proxy = passes / 300 requested)

| Selector | Ambroxol CNNaffinity | GenMol pass | MolMIM pass | Y_genmol | Y_molmim |
| --- | ---: | ---: | ---: | ---: | ---: |
| native_rank1 | 6.206 | 15 | 1 | 5.00% | 0.33% |
| cnn_vs_desc | 6.206 | 20 | 1 | 6.67% | 0.33% |
| minimized_affinity_asc | 6.206 | 11 | 1 | 3.67% | 0.33% |

Per-candidate, per-selector detail (selected pose rank, CNNscore/CNNaffinity/CNN_VS/minimizedAffinity, geometry validity, occupancy, pass/fail) is archived in candidate_selector_turnover.csv -- one row per candidate per selector, so gains/losses/retentions between selectors are auditable directly rather than only visible as net aggregate counts.

## Advancement population

- **Primary set (frozen, advance to ADMET/diversity triage): 16 candidates** -- the native-rank-1 structural-proxy passers, unchanged by this analysis.
- **Exploratory Top-5 reserve (kept separately labelled, NOT merged into the primary count): 11 candidates** -- GM_009, GM_017, GM_026, GM_028, GM_036, GM_041, GM_042, GM_043, GM_046, GM_051, GM_066. These have a passing pose somewhere in their Top-5 but were not selected by the frozen native-CNNscore-rank-1 rule; no reranking rule is adopted here to promote them, per the redocking evidence below showing selector performance does not transfer cleanly between the redocking and candidate-screen populations (minimizedAffinity improves redocking Success@1 but drops candidate-screen passes from 16 to 12).
- Do not report a combined "27 qualified candidates" headline: the 16/11 split must stay visible in any downstream reporting.

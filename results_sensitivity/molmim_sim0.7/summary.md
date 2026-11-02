# DecisionBench-DD generator scorecard summary (v1.2 gates)

## molmim
- Qualified candidate yield (Y_chemical) = 3.3% (95% CI 1.3-5.3%), pooled over 300 requested molecules
- Validity = 99.0%, run-to-run stdev = 1.7 pp
- Uniqueness (of valid) = 99.7%
- Internal diversity (pooled unique set) = 0.837
- Median Tanimoto to seed = 0.167
- Mean QED = 0.783, mean SA score = 3.17
- PAINS pass rate = 99.0%
- Brenk: R_Brenk (any alert) = 41.8%, R_seed_alert (only seed-inherent) = 0.7%, R_new_alert (>=1 new alert, used for qualification) = 41.1%

## Funnel (pooled across replicates)

| tool | stage | count | % of requested |
| --- | --- | ---: | ---: |
| molmim | requested | 300 | 100.0% |
| molmim | valid | 297 | 99.0% |
| molmim | unique | 296 | 98.7% |
| molmim | not_exact_seed | 296 | 98.7% |
| molmim | similarity_band_0.30_to_0.95 | 14 | 4.7% |
| molmim | qed | 14 | 4.7% |
| molmim | sa_score | 14 | 4.7% |
| molmim | molecular_weight | 14 | 4.7% |
| molmim | clogp | 14 | 4.7% |
| molmim | tpsa | 14 | 4.7% |
| molmim | no_pains | 14 | 4.7% |
| molmim | chemically_qualified | 10 | 3.3% |

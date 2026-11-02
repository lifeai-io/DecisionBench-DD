# DecisionBench-DD generator scorecard summary (v1.2 gates)

## molmim
- Qualified candidate yield (Y_chemical) = 0.7% (95% CI 0.0-1.7%), pooled over 300 requested molecules
- Validity = 98.3%, run-to-run stdev = 2.1 pp
- Uniqueness (of valid) = 100.0%
- Internal diversity (pooled unique set) = 0.839
- Median Tanimoto to seed = 0.167
- Mean QED = 0.755, mean SA score = 3.34
- PAINS pass rate = 98.3%
- Brenk: R_Brenk (any alert) = 42.7%, R_seed_alert (only seed-inherent) = 0.0%, R_new_alert (>=1 new alert, used for qualification) = 42.7%

## Funnel (pooled across replicates)

| tool | stage | count | % of requested |
| --- | --- | ---: | ---: |
| molmim | requested | 300 | 100.0% |
| molmim | valid | 295 | 98.3% |
| molmim | unique | 295 | 98.3% |
| molmim | not_exact_seed | 295 | 98.3% |
| molmim | similarity_band_0.30_to_0.95 | 4 | 1.3% |
| molmim | qed | 4 | 1.3% |
| molmim | sa_score | 4 | 1.3% |
| molmim | molecular_weight | 4 | 1.3% |
| molmim | clogp | 4 | 1.3% |
| molmim | tpsa | 4 | 1.3% |
| molmim | no_pains | 4 | 1.3% |
| molmim | chemically_qualified | 2 | 0.7% |

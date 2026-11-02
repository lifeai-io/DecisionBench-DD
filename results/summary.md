# DecisionBench-DD generator scorecard summary (v1.2 gates)

## genmol
- Qualified candidate yield (Y_chemical) = 22.0% (95% CI 17.3-26.7%), pooled over 300 requested molecules
- Validity = 100.0%, run-to-run stdev = 0.0 pp
- Uniqueness (of valid) = 67.0%
- Internal diversity (pooled unique set) = 0.668
- Median Tanimoto to seed = 0.361
- Mean QED = 0.543, mean SA score = 3.77
- PAINS pass rate = 99.7%
- Brenk: R_Brenk (any alert) = 100.0%, R_seed_alert (only seed-inherent) = 84.3%, R_new_alert (>=1 new alert, used for qualification) = 15.7%

## molmim
- Qualified candidate yield (Y_chemical) = 1.0% (95% CI 0.0-2.3%), pooled over 300 requested molecules
- Validity = 99.0%, run-to-run stdev = 1.7 pp
- Uniqueness (of valid) = 100.0%
- Internal diversity (pooled unique set) = 0.842
- Median Tanimoto to seed = 0.167
- Mean QED = 0.742, mean SA score = 3.10
- PAINS pass rate = 99.3%
- Brenk: R_Brenk (any alert) = 51.2%, R_seed_alert (only seed-inherent) = 0.3%, R_new_alert (>=1 new alert, used for qualification) = 50.8%

## Funnel (pooled across replicates)

| tool | stage | count | % of requested |
| --- | --- | ---: | ---: |
| genmol | requested | 300 | 100.0% |
| genmol | valid | 300 | 100.0% |
| genmol | unique | 201 | 67.0% |
| genmol | not_exact_seed | 199 | 66.3% |
| genmol | similarity_band_0.30_to_0.95 | 148 | 49.3% |
| genmol | qed | 87 | 29.0% |
| genmol | sa_score | 84 | 28.0% |
| genmol | molecular_weight | 83 | 27.7% |
| genmol | clogp | 70 | 23.3% |
| genmol | tpsa | 68 | 22.7% |
| genmol | no_pains | 68 | 22.7% |
| genmol | chemically_qualified | 66 | 22.0% |
| molmim | requested | 300 | 100.0% |
| molmim | valid | 297 | 99.0% |
| molmim | unique | 297 | 99.0% |
| molmim | not_exact_seed | 297 | 99.0% |
| molmim | similarity_band_0.30_to_0.95 | 12 | 4.0% |
| molmim | qed | 11 | 3.7% |
| molmim | sa_score | 11 | 3.7% |
| molmim | molecular_weight | 11 | 3.7% |
| molmim | clogp | 9 | 3.0% |
| molmim | tpsa | 8 | 2.7% |
| molmim | no_pains | 8 | 2.7% |
| molmim | chemically_qualified | 3 | 1.0% |

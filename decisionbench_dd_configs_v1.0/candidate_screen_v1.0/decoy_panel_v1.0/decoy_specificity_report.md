# Decoy-panel structural-proxy background-calibration report

## Embedding-reproducibility diagnostic (discovered post-hoc)

Re-docking the 69 frozen candidates fresh in this batch gave 24/69 passing, vs. the frozen primary run's 16/69 -- 18 candidates (13 newly passing, 5 newly failing) flipped status. CNNaffinity (redock - primary) ranged -1.3034 to 2.2401 (mean 0.1601).

**Plausible major source:** RDKit ETKDGv3 embedding is not reproducible across separate process invocations despite an explicit fixed randomSeed=42 (decisionbench_dd_docking/prepare_ligands.py) -- verified directly for GM_009 (blinded PMD_0133): identical canonical/protonated SMILES and atom count between the frozen primary docking_input_ligands/GM_009_3KEH.sdf and this run's freshly-prepared SDF, but starting-conformer heavy-atom coordinates differ by up to 1.6953 A (mean 0.2744 A). This is a substantially larger effect than the previously-documented ~0.0009 cross-machine CNNaffinity drift (Appendix H), which characterized only Ambroxol's own score, not the full candidate population. This is not a controlled experiment isolating embedding as the sole varying input: which physical machine ran which docking batch was not recorded, so an additional contribution from other run-level or hardware factors cannot be ruled out on top of the embedding effect.

## Post-hoc amended same-batch analysis (emphasized descriptive estimate)

Candidates (this batch): 24/69 = 34.8%
Decoys: 82/345 = 23.8% (cluster-bootstrap 95% CI 19.1-28.7%)
Risk difference = 11.0 pp (95% CI -1.2-23.8)
Risk ratio = 1.46 (95% CI 0.96-2.12)
*The matched cluster-bootstrap interval below conditions on one embedding-and-docking realization per molecule and therefore does not capture within-molecule procedural variability from repeated ligand embedding.*

**Interpretation:** Decoy rate below candidate rate but >10%, or RR CI includes 1: possible but weak discrimination; gate remains poorly calibrated. The panel therefore provides, at most, weak and inconclusive evidence that the gate distinguishes pipeline candidates from this property-matched background. Because the decoys are not experimentally confirmed GCase inactives, the experiment does not estimate biological specificity or target-specific binding.

## Gate mechanism (3KEH, marginal breakdown)

| population            |   n |   five_poses_returned |   geometry_valid_top1 |   catalytic_contact_top1 |   cnnaffinity_ge_ambroxol |   complete_structural_proxy |
|:----------------------|----:|----------------------:|----------------------:|-------------------------:|--------------------------:|----------------------------:|
| Same-batch candidates |  69 |                    69 |                    67 |                       64 |                        25 |                          24 |
| Decoys                | 345 |                   344 |                   343 |                      238 |                        85 |                          82 |

The gates are conjunctive, so this table decomposes them marginally (each column scored independently against the full population, not cumulatively): reordering them cannot change the final pass set, only which gate receives marginal attribution. Both catalytic-site contact (92.8% vs. 69.0%) and the CNNaffinity-vs-Ambroxol threshold (36.2% vs. 24.6%) show a descriptive population difference; CNNaffinity is the more restrictive filter in absolute terms for both populations, but contact is not merely incidental -- it is not the only gate component that differs between populations.

## Size-bias and covariate-balance checks

Spearman(CNNaffinity, HAC) among decoys: rho=0.3734, p=0.0.
Logistic pass~HAC+cLogP coefficients: {'const': -5.6378, 'decoy_hac': 0.2716, 'decoy_clogp': -0.522} (p-values: {'const': 0.0, 'decoy_hac': 0.0, 'decoy_clogp': 0.0117}).

**Halogen-count balance** (matching_balance.csv: SMD=0.3385, the only covariate exceeding even the 0.20 relaxed tolerance): candidates (n=69) mean=2.0435, median=2.0, range=[1, 5], value counts {1: 1, 2: 66, 3: 1, 5: 1}; decoys (n=345) mean=1.8783, median=2.0, range=[1, 4], value counts {1: 73, 2: 246, 3: 21, 4: 5}. IQR is degenerate (2-2) for both populations -- this is a discrete, narrow-range covariate, so mean/value-counts are more informative than IQR here.
Proportions with 0/1/2/>2 halogens -- candidates: {'0': {'n': 0, 'pct': 0.0}, '1': {'n': 1, 'pct': 1.4}, '2': {'n': 66, 'pct': 95.7}, '>2': {'n': 2, 'pct': 2.9}}; decoys: {'0': {'n': 0, 'pct': 0.0}, '1': {'n': 73, 'pct': 21.2}, '2': {'n': 246, 'pct': 71.3}, '>2': {'n': 26, 'pct': 7.5}}.
Spearman(CNNaffinity, halogen count) among decoys: rho=0.0143, p=0.79118.
Structural-proxy pass rate by halogen stratum (decoys): <=1 halogen 24/72 (33.3%) vs. >=2 halogens 58/272 (21.3%).
Halogen-adjusted logistic pass~HAC+cLogP+halogen_count coefficients: {'const': -5.4302, 'decoy_hac': 0.2679, 'decoy_clogp': -0.489, 'decoy_halogen_count': -0.1315} (p-values: {'const': 0.0, 'decoy_hac': 0.0, 'decoy_clogp': 0.0233, 'decoy_halogen_count': 0.5939}).

## Preregistered cross-run analysis, subsequently identified as confounded

Candidates (frozen primary): 16/69 = 23.2%
Decoys (this batch): 82/345 = 23.8%
Risk ratio = 0.98 (95% CI 0.81-1.21)

**Interpretation:** Decoy rate >= candidate rate: no evidence the structural proxy enriches pipeline candidates over matched unrelated molecules.

**Caveat:** Decoys are not experimentally confirmed GCase inactives; this estimates background acceptance/discrimination, not biological specificity or target-specific binding. Without measured affinities, the CNNaffinity-HAC association below cannot distinguish model bias from a genuine physical size-affinity relationship.
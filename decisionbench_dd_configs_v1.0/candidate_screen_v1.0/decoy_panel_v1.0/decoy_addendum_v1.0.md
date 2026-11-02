# Decoy-panel calibration addendum v1.0 (frozen pre-registration)

**Status: post-hoc.** This addendum is written after inspecting the primary
candidate-screen results (16/69 = 23.2% structural-proxy pass rate, verified
against `candidate_screen_results/candidate_results.csv`) and after the
frozen primary 16-candidate set, funnel, and manuscript results already
exist. It calibrates the structural-proxy gate; it does **not** redefine the
frozen pipeline, does not add or remove any of the 16 primary candidates, and
does not change any headline result already reported.

## Question

Does the frozen GNINA structural proxy preferentially pass the chemically
qualified pipeline candidates (66 GenMol + 3 MolMIM) over physically similar
but topologically unrelated molecules?

## Primary endpoint

```
p_decoy = (decoys achieving the complete frozen structural-proxy pass) / 345
```

## Candidate comparator

```
p_candidate = 16 / 69 = 23.2%
```

We use the conditional 16/69 rate — not the requested-output denominator of
600 (300 GenMol + 300 MolMIM requested at the primary `min_similarity=0.3`
setting) — because the decoy panel calibrates the structural stage, whose
input population is the 69 chemical qualifiers, not the full requested-output
population.

## Secondary questions

1. Is the gate associated with heavy-atom count or molecular weight?
2. Which component of the structural proxy — CNNaffinity threshold,
   catalytic-Glu contact, or geometry validity — rejects the decoys?
3. Are results consistent between the 3KEH (neutral) and 3KE0 (acidic)
   receptor states?
4. Do the alternative rerankers already reported in the paper (CNN_VS,
   minimized affinity) materially change the background pass rate?

All results under this addendum are labeled **post-hoc**.

## Frozen candidate reference set

All 69 chemical qualifiers that entered docking in the primary screen: 66
GenMol + 3 primary MolMIM (not the 16 structural passers — conditioning the
match on the structural-proxy outcome would invalidate the comparison). See
`candidate_reference_v1.0.csv` for the frozen property set (MW, heavy-atom
count, cLogP, TPSA, HBD, HBA, rotatable bonds, formal charge, ring count,
aromatic ring count, halogen count, ECFP4 fingerprint), computed with the
same RDKit version (2026.03.5) and canonicalization
(`decisionbench_dd_eval/chem_metrics.py:canonicalize`,
`:morgan_fingerprint`, radius 2 / 2048-bit) as the frozen chemical-gate
audit.

## Decoy panel design

- **Source pool:** ChEMBL 37 chemreps (`decoy_source_manifest.json` records
  the exact URL, download date, and file checksum).
- **Ratio:** 5 decoys per candidate, 69 × 5 = 345 decoys.
- **Exclusions before matching:** exact matches to Ambroxol, any generated
  molecule, or the 4 existing docking controls; ECFP4 Tanimoto ≥0.35 to any
  of the 69 candidates; ECFP4 Tanimoto ≥0.30 to Ambroxol; known/annotated
  GCase (GBA1) ligands where reachable in source metadata.
- **Matching calipers:** formal charge exact; HAC ±2; MW ±10% or ±25 Da;
  cLogP ±0.5; TPSA ±10 Å²; HBD ±1; HBA ±1; rotatable bonds ±1; ring count
  ±1; halogen count preferred ±1. Selection without replacement, weighted
  toward HAC/cLogP/formal-charge priority (the reviewer's concern is
  CNNaffinity size bias). Any caliper relaxation is logged per candidate in
  `property_matched_decoys.csv`.
- **Balance target:** |SMD| < 0.10 for MW, HAC, cLogP, TPSA (reported in
  `matching_balance.csv` / `matching_balance_figure.pdf`); up to 0.20
  tolerated (and disclosed) for sparse discrete properties (ring/halogen
  count).
- **Blinding:** decoys and candidates are relabeled `PMD_0001`–`PMD_0414`
  (candidates get their own blinded IDs too) in the docking-order manifest;
  the candidate↔decoy mapping is kept in a file the docking/gate scripts
  never read.
- **Preparation and docking:** identical frozen ligand-preparation workflow
  (dimorphite-dl + RDKit ETKDGv3 embedding, same pH/tautomer/stereo policy)
  and identical frozen GNINA structural-proxy gate (native CNNscore rank-1;
  CNNaffinity ≥ Ambroxol's own 3KEH reference; catalytic-Glu235/340 contact
  ≤4.5 Å; geometry validity) as the primary 69-candidate screen — copied
  from the executable configuration
  (`downstream_gcase_screening_protocol.md`, `run_candidate_screen_gnina.py`,
  `score_candidate_screen.py`), not reconstructed from manuscript prose.
  Preparation/docking failures remain in the 345 denominator as structural
  failures and are reported separately as technical attrition.

## Statistical plan

- Primary: matched-set (69 sets of 1 candidate + 5 decoys) cluster bootstrap
  for the decoy pass rate, risk difference (Δ = p_candidate − p_decoy), and
  risk ratio (RR = p_candidate / p_decoy) — not an ordinary molecule-level
  interval treating all 414 molecules as independent.
- Secondary matched analysis: conditional logistic regression or stratified
  permutation test (optional).
- Size-bias pre-registered checks on the 345 decoys only: Spearman
  correlation between CNNaffinity and HAC; logistic model
  `logit P(pass) = β0 + β1·HAC + β2·cLogP` (TPSA/charge/aromatic-ring count
  as optional secondary covariates); pass rate by HAC/MW quartile.
- Reranker sensitivity (CNN_VS, minimized affinity, alternate seed/
  exhaustiveness) is subordinate: reported for all pre-specified options,
  never selected post-hoc for the lowest decoy rate, and never replaces
  native CNNscore rank-1 as primary.

## Interpretation rules (pre-registered)

| Outcome | Supported conclusion |
|---|---|
| Decoy rate near or above 23.2% | No evidence the structural proxy enriches pipeline candidates over matched unrelated molecules |
| Decoy rate below 23.2% but above 10%, or RR CI includes 1 | Possible but weak discrimination; gate remains poorly calibrated |
| Decoy rate ≤10%, matched RR >2, CI excludes 1 | Evidence the proxy rejects most property-matched unrelated molecules |
| Strong CNNaffinity–HAC association | Structural score has residual size dependence despite matching |
| Weak score-only discrimination but strong contact discrimination | Pocket-placement rule, not affinity prediction, drives rejection |

**Even a very low decoy rate would not demonstrate GCase activity.** The
decoys are not experimentally confirmed GCase inactives; this experiment
estimates the frozen proxy's background rejection/enrichment against a
defined physicochemically-matched background, not biological specificity.

## Recommended manuscript statement (once docking is complete)

> In a post-hoc calibration experiment, we screened 345 topologically
> dissimilar decoys matched 5:1 to the 69 chemical qualifiers on heavy-atom
> count, molecular weight, cLogP, TPSA, charge, hydrogen-bonding features,
> flexibility, and ring count. All decoys were processed with the frozen
> ligand-preparation, GNINA docking, selector, and structural-proxy rules.
> The experiment estimates the proxy's background pass rate against
> property-matched unrelated molecules; because the decoys were not
> experimentally confirmed GCase inactives, it does not estimate biological
> specificity.

## Status of this document

Frozen before decoy sourcing/matching began. Steps 1–8 (this document,
candidate reference set, source-pool filtering, exclusions, matching,
balance verification, blinding, ligand preparation) were completed without
GPU access. Steps 9–14 (GNINA docking and downstream statistics) require
Docker + GPU and are handed off — see `README.md` in this directory for the
exact commands.

## Amendment (post-hoc, after inspecting results)

**Dated 2026-09-05, after GNINA docking completed.** Re-docking the same
69 candidates fresh in this batch (included as an internal consistency
check, §"Blinding" in `README.md`) returned 24/69 (34.8%) passing, not the
frozen primary run's 16/69 (23.2%). The preregistered cross-run comparison
above (decoys vs. the frozen primary's 16/69) is **retained as the
preregistered analysis** — it is not withdrawn or superseded. Because the
candidate rerun exposed substantial cross-run embedding variability, we
additionally **emphasize the same-batch comparison as the less-confounded
post-hoc descriptive estimate**. This emphasis was adopted after
inspecting the docking results and is therefore a logged post-hoc
amendment, not a confirmatory primary analysis. See
`decoy_specificity_report.md` for both analyses in full, and
`analyze_decoy_panel.py`'s module docstring for technical detail.

The audit identified ligand re-embedding as a **plausible major source** of
the cross-run variation: for the same candidate (GM_009), identical
canonical/protonated SMILES and atom count but starting-conformer
coordinates differing by up to 1.70~Å between the frozen primary's SDF and
this run's freshly-prepared SDF, despite the frozen preparation
implementation (`decisionbench_dd_docking/prepare_ligands.py`) explicitly
setting an ETKDGv3 `randomSeed` (42). **Update, diagnosed with
`decisionbench_dd_docking/diagnose_embedding_determinism.py`:** this is not
established as a missing-seed oversight or as RDKit's seeded embedding
being inherently/universally nondeterministic. Re-embedding the same
SMILES with the same seed, using this exact frozen code path
(`AllChem.EmbedMolecule`, not `EmbedMultipleConfs`, so RDKit's `numThreads`
-- default 1, never overridden -- is not in play), was found to be exactly
reproducible both within one process and across independent fresh-process
invocations (0.0~Å across repeated trials for three cases spanning the
observed delta range). What is established is that the deployed pipeline,
run at different times, did not reproduce the same conformer; future
instantiations should archive the actual prepared 3D ligand inputs, not
just the generation code and seed, to guarantee byte-identical redocking
regardless of the (still undetermined) root cause. We did not record which
physical machine or RDKit build ran which docking batch, so we cannot rule
out an additional contribution from other run-level or hardware factors (as
separately documented for Ambroxol alone in Appendix H) on top of the
embedding effect — this was not a controlled experiment isolating
embedding as the only varying input.

### Headline result

- **Post-hoc amended same-batch analysis** (emphasized as the
  less-confounded descriptive estimate): candidates 24/69 = 34.8% vs.
  decoys 82/345 = 23.8%; risk ratio 1.46 (95% CI 0.96–2.12, matched
  cluster bootstrap). This interval conditions on one embedding-and-
  docking realization per molecule and therefore does not capture
  within-molecule procedural variability from repeated ligand embedding.
  The CI includes 1: a non-conclusive trend toward the gate favoring the
  actual pipeline candidates over property-matched background, not a
  statistically conclusive result at this sample size.
- **Preregistered cross-run analysis, subsequently identified as
  confounded:** decoys 23.8% vs. the frozen primary's 16/69 = 23.2%; risk
  ratio 0.98 (95% CI 0.81–1.21) — indistinguishable, but this comparison
  mixes two different docking runs and is not the headline estimate.
- **Residual CNNaffinity–size association:** Spearman(CNNaffinity, HAC) =
  0.37 among decoys (p < 0.0001) — a statistically significant
  association survives HAC/cLogP-matched background selection. Without
  measured affinities, this cannot distinguish model bias from a genuine
  physical size–affinity relationship, but it does establish that
  CNNaffinity is not independent of molecular size even after matching,
  consistent with the reviewer's original concern.
- **Halogen-count balance (the one covariate matching could not balance,
  SMD 0.34, exceeding even the 0.20 relaxed tolerance):** candidates ranged
  1–5 halogens (mean 2.04, median 2; 66/69 = 95.7% dihalogenated; 0/1.4/
  95.7/2.9% with 0/1/2/>2 halogens), while decoys ranged 1–4 (mean 1.88,
  median 2; 0/21.2/71.3/7.5% with 0/1/2/>2 halogens) — decoys include a
  substantial monohalogenated subgroup (73/345 = 21.2%) candidates almost
  entirely lack; IQR is degenerate at 2–2 for both populations (a discrete,
  narrow-range covariate, so mean/value-counts are more informative than
  IQR here). This imbalance does not appear to drive the gate's behavior:
  halogen count showed no association with structural-proxy pass among
  decoys (Spearman(CNNaffinity, halogen count) = 0.01, p = 0.79; pass
  rate 24/72 = 33.3% for ≤1 halogen vs. 58/272 = 21.3% for ≥2 halogens,
  unadjusted), and adding halogen count to the HAC/cLogP logistic model
  left those coefficients essentially unchanged (halogen coefficient
  −0.13, p = 0.59). The bromine-rich analogue series' halogenation does
  not appear to be an unaccounted confound in the CNNaffinity–size result
  above.
- **Gate mechanism (marginal, not cumulative attribution):** the gates
  are conjunctive, so scoring order cannot change the final pass set,
  only which component receives marginal attribution. At 3KEH, the
  CNNaffinity-vs-Ambroxol threshold is the more restrictive filter in
  absolute terms for both populations (candidates 69→25 pass; decoys
  345→85 pass), but catalytic-site contact also shows a real descriptive
  population difference (92.8% vs. 69.0%) -- it is not only CNNaffinity
  that differs between populations. Geometry validity and catalytic-site
  contact remove comparatively few additional cases at the final combined
  step (candidates 25→24; decoys 85→82).

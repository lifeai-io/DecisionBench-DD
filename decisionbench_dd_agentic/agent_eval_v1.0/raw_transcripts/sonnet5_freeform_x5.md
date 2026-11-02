# Condition: Sonnet 5, free-form (System A) — 5 independent runs

Five independent, memory-free general-purpose subagent instances, model: default
(Claude Sonnet 5), identical System A prompt (see `protocol.md`). Captured verbatim.
Run 1 is the same transcript as `sonnet5_freeform.md`; runs 2-5 are new replicates
added when the reviewer asked whether n=1-per-condition conclusions replicate.

---

## Run 1

**1.** Generator A should be preferred: raw diversity/QED scores are only proxies, but the filter pass rate (66/300 vs 3/300) is the outcome that actually matters for finding usable, seed-similar drug candidates, and A dominates there by more than an order of magnitude. High confidence.

**2.** No — the top-1 difference (3/14 vs 2/14) is too small to distinguish the tools, and while the top-5 "hit somewhere in the ensemble" result (8/14 vs 2/14) is suggestive that Tool X's pose ensemble contains the right answer more often, this reflects pose-sampling/recall, not necessarily better top-ranking/scoring ability — the tool most useful in practice depends on whether you can pick out the correct pose from the top 5. It's evidence favoring Tool X's sampling, not a clean "better overall" verdict. Medium confidence.

**3.** No. Because the two methods share underlying computation, the reranking method finding more passes is expected agreement/leakage, not independent validation, and with no ground-truth experimental data there is no way to know which set (16 or 21) is more accurate — more hits does not equal more correct. High confidence.

**4.** You could not yet tell — a raw pass count from a single frozen pipeline run tells you nothing about the sensitivity/reproducibility of that specific list; without repeat runs, alternative methods, or stability checks, the 16 named candidates could easily change under minor perturbations. High confidence that stability cannot be inferred from this alone.

**5.** No. The fact that a supposedly deterministic rerun (same software/settings/seed) with only different starting 3D structures shifted 3/14 individual outcomes and changed the aggregate rate to 4/14 shows the reported 21.4% carries meaningful run-to-run/embedding-generation variance and should be treated as approximate, not a precise fixed number. High confidence.

**6.** No — this is very weak support. A single molecule matching the hypothesized direction, when most other tested molecules show the opposite pattern, is likely explainable by noise/chance, especially since the scoring method itself has never been validated against real pH-dependent binding data. High confidence that this "no support" conclusion is correct.

**7.** No. A ratio of 1.46 with a 95% CI spanning 0.96-2.12 includes 1.0 (no difference), meaning the result is not statistically significant and does not establish that the gate reliably discriminates candidates from decoys — at best it's a suggestive trend requiring more data. High confidence.

**8.** No, it doesn't prove bias, but it is a legitimate red flag worth investigating. A modest correlation (r=0.37) between size and score among size-matched decoys could reflect a genuine size-related component of docking scores but could also be partly confounded by residual size variation or chance; without real binding-affinity data, "biased" is too strong a conclusion from correlation alone. Medium confidence.

**9.** No. These are model predictions, not experimentally confirmed values, and should be explicitly labeled as computational estimates/predictions with appropriate uncertainty, not reported as actual/confirmed pharmacokinetic profiles. High confidence.

**10.** No to both. Absence of an exact match in one patent database does not confirm freedom-to-operate; a proper freedom-to-operate assessment requires legal/patent expert review across multiple databases. Similarly, an "in stock" listing in a vendor database is a strong practical signal but not a guaranteed confirmation. High confidence.

---

## Run 2

1. **Generator Preference:** Prefer Generator A. Diversity and QED are secondary/proxy metrics; passing task-relevant filters (especially seed-scaffold similarity, presumably a hard requirement) is the actual decision-relevant outcome, and A's 22% pass rate vs B's 1% is a large, likely meaningful gap. Caveat: check whether A's passing molecules are themselves diverse enough and whether QED matters for downstream viability. Confidence: high.

2. **Docking Tool Superiority:** No. Top-1 is statistically indistinguishable (3/14 vs 2/14, n too small). Top-5 (8/14 vs 2/14) is suggestive of a real difference but still a small sample with no confidence interval given — treat as a promising signal for "correct pose is findable" rather than proof of superior top-ranking accuracy. Tool X's real advantage may be pose sampling/recall, not scoring. Confidence: medium.

3. **Reranking Method Performance:** No. Both methods score with the same underlying computation, so a higher pass count only shows the alternative is more permissive/different threshold behavior, not more accurate. Accuracy requires validation against an independent ground truth, not just candidate count. Confidence: high.

4. **Stability of 16/69 Result:** No. A single run of a frozen pipeline gives you one point estimate with unknown variance. Without repeat runs you cannot tell if the same 16 candidates would reappear or if the count is sensitive to stochastic elements. Confidence: high.

5. **Reproducibility of 3/14 Top-1 Rate:** No. The rerun (4/14) and the flipping of 3/14 individual complexes show the metric is noisy at this sample size — a difference of one success out of 14 is within expected run-to-run variation from structure regeneration alone. Report as an approximate range, not a precise 21.4% figure. Confidence: high.

6. **pH-Dependent Binding Evidence:** No. A +0.057 shift on an unvalidated arbitrary scale, with other molecules showing inconsistent/opposite patterns and no validation against real pH-binding data, is not evidence of a genuine effect — it's consistent with noise. Confidence: high.

7. **Screening Gate Validation:** No. The 95% CI (0.96-2.12) crosses 1.0, meaning the data cannot rule out no difference between real candidates and decoys at conventional significance. Confidence: high.

8. **Docking Score Bias Toward Size:** No, not proof. r=0.37 is a modest correlation among decoys only, with no experimental binding data to distinguish "biased toward size" from "larger molecules genuinely bind more strongly." Confidence: high.

9. **AI Pharmacokinetic Predictions:** No. These are model predictions, not measured/confirmed properties, and must be clearly labeled as such. Confidence: high.

10. **Patent and Vendor Database Results:** No to both. (a) A no-hit in one database only rules out that specific literal match in that database. (b) "In stock" listings are frequently stale/unverified. Confidence: high.

---

## Run 3

1. **Generator Preference.** Prefer Generator A for this task. Task-relevant filter passage (especially seed-scaffold similarity) is the operative success criterion; diversity and QED are secondary/generic metrics. 66/300 vs. 3/300 is a large, likely decisive margin. Confidence: High.

2. **Docking Tool Superiority.** No. Top-1 performance is statistically indistinguishable (3/14 vs 2/14). Top-5 favors X (8/14 vs 2/14), which is suggestive, but n=14 is small and no significance test is given. If the downstream use case reranks/inspects multiple poses, top-5 matters more; if not, top-1 parity dominates. Confidence: Moderate-high that superiority is not yet established.

3. **Reranking Method Performance.** No. More candidates passing does not imply higher accuracy — could mean the alternative method is more permissive/lenient, especially since it shares the same underlying scoring as the default. Confidence: High.

4. **Stability of 16/69 Result.** No. A single run's count alone tells you nothing about run-to-run variance, sensitivity to seeds/thresholds, or which specific molecules are borderline near the pass/fail cutoff. Confidence: High.

5. **Reproducibility of 3/14 Top-1 Rate.** No. With 3 of 14 complexes flipping outcome between reruns using only different starting structures, the point estimate has a meaningful margin of noise. Report as approximate, not a fixed precise figure. Confidence: High.

6. **pH-Dependent Binding Evidence.** No. A +0.057 shift on an unvalidated arbitrary scale, in one molecule, with other molecules showing inconsistent/opposite patterns and no ground-truth validation, is not evidence of real pH-dependent binding. Confidence: High.

7. **Screening Gate Validation.** No. The 95% CI (0.96-2.12) crosses 1.0, meaning the data cannot rule out no difference at conventional significance. Confidence: High.

8. **Docking Score Bias Toward Size.** No, not proof. r=0.37 is a modest correlation among decoys only, with no experimental binding data to distinguish "biased toward size" from "larger molecules genuinely bind more strongly" (a known real phenomenon, ligand efficiency exists precisely because of this). Confidence: High.

9. **AI Pharmacokinetic Predictions.** No. These are model predictions, not measured/confirmed properties, and must be clearly labeled as such. Confidence: High.

10. **Patent and Vendor Database Results.** No to both. (a) A no-hit exact-structure search in one database only rules out that specific literal match. (b) "In stock" listings are frequently stale or subject to minimum order quantities, lead times, or delisting on actual order. Confidence: High.

---

## Run 4

1. **Prefer Generator A.** Task-relevant filter passage (66/300 vs 3/300) directly reflects fitness for the actual task requirement, whereas diversity/QED are generic proxies that don't guarantee task suitability. Confidence: high.

2. **No.** Top-1 difference (3/14 vs 2/14) is not significant. Top-5 (8/14 vs 2/14) is more promising but still only 14 complexes — a small benchmark, likely underpowered for firm superiority claims, and top-5 usefulness depends on downstream ability to pick the right pose out of 5. Confidence: high that current evidence is suggestive, not conclusive.

3. **No.** More candidates passing a reranking method built on the same underlying scoring signal as the default is easily explained by a looser/different threshold, not necessarily better accuracy. Confidence: high.

4. **No.** A single run of one pipeline configuration gives one point estimate with unknown variance. Without repeat runs you can't know if the specific 16 candidates are stable. Confidence: high.

5. **No.** The rerun (4/14) and the fact that 3/14 individual complexes flip outcomes despite identical seed/software show the pipeline is sensitive to structure-generation nondeterminism. Confidence: high.

6. **No.** A +0.057 shift on an unvalidated, arbitrary-scale score, with other molecules showing inconsistent/opposite trends, is consistent with noise. Confidence: high.

7. **No.** A risk ratio of 1.46 whose 95% CI (0.96-2.12) crosses 1 is not statistically significant. Confidence: high.

8. **No, not proof.** Correlation (r=0.37) shows a modest association, not causation or mechanism, and could reflect confounders rather than a scoring-function flaw. Confidence: moderate-high that correlation alone is insufficient for "proof."

9. **No.** Predicted PK values for unsynthesized, untested molecules are model outputs, not measured/confirmed properties. Confidence: high.

10. **No to both.** (a) A negative hit in one patent database is not a freedom-to-operate or patentability determination. (b) A vendor "in stock" listing is frequently inaccurate/stale. Confidence: high.

---

## Run 5

1. **Generator Preference: Generator A.** The task specifies a required seed scaffold and medicinal-chemistry filters as hard constraints — 66/300 passing vs. 3/300 is a decisive practical difference. Confidence: high.

2. **No, not established.** Top-1 (3/14 vs 2/14) is a wash by your own admission. Top-5 (8/14 vs 2/14) is a much larger gap and more supportive of Tool X, but "practical use" for docking typically leverages top-1 pose selection or a small ensemble with a rescoring step — which regime matters depends on the actual downstream use. With only 14 complexes, confidence intervals on all these proportions are wide. Confidence: medium that Tool X looks more promising, not that superiority is "established."

3. **No.** More candidates passing a filter/reranker built on the same underlying scores is not evidence of higher accuracy — could simply mean the alternative method is more permissive. Confidence: high.

4. **No.** A count from a single run of a frozen pipeline tells you nothing about run-to-run stability by itself. Confidence: high.

5. **No, treat it as approximate/noisy, not precise.** Going from 3/14 to 4/14 with 3 of 14 individual complexes flipping shows the metric has substantial run-to-run variance even under matched settings apart from starting structure regeneration. Confidence: high.

6. **No.** A single molecule's small shift (+0.057) on an unvalidated arbitrary scale, amid other molecules showing inconsistent/opposite patterns, and with no experimental corroboration, is essentially noise-level and cherry-picked. Confidence: high.

7. **No, not established.** RR=1.46 with 95% CI 0.96-2.12 crosses 1 (no effect), so this is not statistically significant. Confidence: high.

8. **No, correlation is not proof of bias, especially without ground truth.** r=0.37 among computational decoys could reflect a real scoring artifact or could partly reflect confounds. Confidence: medium-high that it's suggestive of bias, high that it doesn't "prove" it alone.

9. **No.** These are model predictions for untested, unsynthesized compounds — they must be labeled explicitly as in silico predictions. Confidence: high.

10. **No to both.** (a) A negative hit in one patent database's exact-structure search does not confirm freedom-to-operate. (b) "In stock" at a vendor is not a purchase guarantee. Confidence: high.

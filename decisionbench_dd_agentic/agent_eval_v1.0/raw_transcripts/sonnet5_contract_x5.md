# Condition: Sonnet 5, decision-contract (System B) — 5 independent runs

Five independent, memory-free general-purpose subagent instances, model: default
(Claude Sonnet 5), identical System B prompt (Decision Contract R1-R8, see
`protocol.md`). Run 1 is the same transcript as `sonnet5_contract.md`; runs 2-5
are new replicates added when the reviewer asked whether n=1-per-condition
conclusions replicate.

---

## Run 1

**Item 1.** 1. Generator A should be preferred for this task: despite lower raw diversity and QED, it produced far more molecules (66/300 vs 3/300) that actually pass the medicinal-chemistry filters relevant to the drug-discovery goal. 2. R3 (aggregate framing doesn't apply cleanly) and R2 (QED/diversity are computed scores, not confirmed drug-likeness). 3. Medium.

**Item 2.** 1. No — the top-1 (primary, pre-specified) comparison is a statistical tie (3/14 vs 2/14), so this benchmark does not establish Tool X as better overall; the top-5 finding is a secondary/exploratory result that suggests Tool X may have an edge but cannot overturn the null primary comparison. 2. R5 (primary endpoint null -> secondary result is suggestive only), R1. 3. Medium.

**Item 3.** 1. No — finding more passing candidates (21 vs 16) does not mean the reranking method is more accurate; without independent ground truth, a higher pass count could reflect a looser or correlated bias. 2. R8, R7-adjacent. 3. High.

**Item 4.** 1. From the 16/69 figure alone you cannot tell whether this specific list of 16 is a stable, final set. 2. R3, R6. 3. High.

**Item 5.** 1. No — the 3/14 (21.4%) figure should not be treated as precise; a rerun with only the starting 3D structures changed produced a different aggregate rate (4/14) and flipped 3 individual outcomes. 2. R6. 3. High.

**Item 6.** 1. No — this single result is contradicted by three other unrelated molecules, and the scoring method has never been validated against real measured pH-dependent binding data. 2. R2, R6, R7. 3. High.

**Item 7.** 1. No — the 95% CI (0.96-2.12) includes 1.0, so this result is inconclusive. 2. R1. 3. High.

**Item 8.** 1. No — this correlation among computational proxy decoys cannot prove the docking model is biased toward size rather than true binding strength. 2. R7. 3. High.

**Item 9.** 1. No — these AI-predicted pharmacokinetic properties must not be reported as actual, confirmed, or measured values. 2. R2. 3. High.

**Item 10.** 1. No to both. 2. R4. 3. High.

---

## Run 2

**1. Generator Preference**
- **Conclusion:** Generator A is the operationally preferable choice for this task, since it produces far more molecules meeting the task-relevant requirement (66/300 pass full filters vs. 3/300) — the lower aggregate diversity/QED is a legitimate tradeoff. However, this does not certify that any of the 66 flagged molecules is individually valid — that requires downstream confirmation.
- **Rules:** R3, R2.
- **Confidence:** Moderate-high on the directional preference; low on any claim about individual molecules.

**2. Docking Tool Superiority**
- **Conclusion:** No — this does not establish Tool X as better for practical use. The primary endpoint (top-1 accuracy) shows no meaningful difference. The top-5 result is a secondary/looser metric and can only be reported as suggestive; it cannot overturn the null result on the primary metric. This is also a single benchmark run on a small set, not a validated, reproduced comparison.
- **Rules:** R5, R6, R3.
- **Confidence:** Moderate-high.

**3. Reranking Method Performance**
- **Conclusion:** No — finding more passing candidates is not evidence of greater accuracy given shared underlying scoring and no independent ground truth.
- **Rules:** R8, R7.
- **Confidence:** High.

**4. Stability of 16/69 Result**
- **Conclusion:** No — the aggregate count alone tells you nothing about whether this specific list of 16 is stable or final.
- **Rules:** R3, R6.
- **Confidence:** High.

**5. Reproducibility of 3/14 Top-1 Rate**
- **Conclusion:** No, the original 21.4% should not be treated as precise or reproducible. An independent repeat was performed and produced a different rate (4/14) with 3 of 14 individual complexes flipping outcome.
- **Rules:** R6, R2.
- **Confidence:** High.

**6. pH-Dependent Binding Evidence**
- **Conclusion:** No — a +0.057 shift on an unvalidated, arbitrary scale, inconsistent across other molecules, with no validation against real pH-binding data, does not constitute evidence of genuine pH-dependent binding.
- **Rules:** R7, R2.
- **Confidence:** High.

**7. Screening Gate Validation**
- **Conclusion:** No — the 95% CI (0.96-2.12) includes 1, so this result is not statistically significant.
- **Rules:** R1.
- **Confidence:** High.

**8. Docking Score Bias Toward Size**
- **Conclusion:** No — a modest correlation among computational decoys, with no experimental binding-affinity data, cannot prove the scoring function is causally biased toward size.
- **Rules:** R7.
- **Confidence:** High.

**9. AI Pharmacokinetic Predictions**
- **Conclusion:** No — these must be reported to the team explicitly as AI-predicted/estimated PK properties, not as actual or confirmed values.
- **Rules:** R2.
- **Confidence:** High.

**10. Patent and Vendor Database Results**
- **Conclusion:** No on both counts, applied separately to (a) and (b).
- **Rules:** R4.
- **Confidence:** High.

---

## Run 3

**1. Generator Preference**
**Conclusion:** For this specific task, Generator A's candidate pool is preferable, given its far higher task-relevant filter pass rate (66/300 vs 3/300), despite lower average diversity/QED. However, this is a preference for downstream triage, not a confirmed statement that Generator A produces "better" or "correct" molecules.
**Rules applied:** R2, R3.
**Confidence:** High on the directional preference.

**2. Docking Tool Superiority**
**Conclusion:** No, this does not establish Tool X as the better tool for practical use. The primary top-1 metric is explicitly non-meaningful at this sample size. The top-5 gap is larger and can be reported as suggestive, but it is a secondary/exploratory metric and cannot overturn the null primary result. This is one benchmark run on one set of 14 complexes — no independent repeat has been performed.
**Rules applied:** R1, R5, R6.
**Confidence:** High.

**3. Reranking Method Performance**
**Conclusion:** No. Finding more passing candidates is not evidence of greater accuracy; a method could pass more candidates simply by being less stringent.
**Rules applied:** R8.
**Confidence:** High.

**4. Stability of 16/69 Result**
**Conclusion:** No. The aggregate count tells you nothing about whether this particular list of 16 is stable or final.
**Rules applied:** R3, R6.
**Confidence:** High.

**5. Reproducibility of 3/14 Top-1 Rate**
**Conclusion:** No, the original 21.4% should not be treated as precise or reproducible. An independent repeat was performed and it produced a different rate (4/14) with 3 of 14 individual complexes flipping outcome — a direct empirical demonstration of non-reproducibility.
**Rules applied:** R6, R2.
**Confidence:** High.

**6. pH-Dependent Binding Evidence**
**Conclusion:** No. A +0.057 shift on an unvalidated arbitrary scale for one molecule, with inconsistent/opposite patterns in other tested molecules and no validation against real measured pH-dependent binding data, does not constitute evidence of genuine pH-dependent binding behavior.
**Rules applied:** R7, R2.
**Confidence:** High.

**7. Screening Gate Validation**
**Conclusion:** No. The 95% CI for the risk ratio (0.96-2.12) includes 1, so this result is not statistically significant regardless of the point estimate.
**Rules applied:** R1.
**Confidence:** High.

**8. Docking Score Bias Toward Size**
**Conclusion:** No. The correlation is observed only among computational decoys with no experimental binding-affinity data to serve as ground truth; this cannot prove the scoring function is mechanistically biased.
**Rules applied:** R7, R2.
**Confidence:** High.

**9. AI Pharmacokinetic Predictions**
**Conclusion:** No. These must be reported to the team explicitly as AI-predicted/estimated pharmacokinetic properties.
**Rules applied:** R2.
**Confidence:** High.

**10. Patent and Vendor Database Results**
**Conclusion:** No to both, applied independently to the patent search and the vendor listing.
**Rules applied:** R4.
**Confidence:** High.

---

## Run 4

## 1. Generator Preference
**Conclusion:** Generator A should be preferred for this task, since the task-relevant criterion is what defines fitness-for-purpose, and A clears that bar at a far higher rate (66/300 vs 3/300) despite lower average diversity/QED. This is a preference about candidate yield, not a guarantee that those 66 molecules are good, viable, or stable candidates.
**Rules:** R2, R3.
**Confidence:** Moderate-high.

## 2. Docking Tool Superiority
**Conclusion:** No, this does not establish Tool X as the better tool for practical use. If top-1 accuracy is the primary endpoint, it is explicitly null/non-meaningful here. The top-5 gap is a secondary/exploratory result that can be reported as suggestive but cannot overturn the null primary finding. This is a single 14-complex benchmark run — no independent repeat has been done.
**Rules:** R5, R6, R1.
**Confidence:** Moderate-high.

## 3. Reranking Method Performance
**Conclusion:** No. Finding more passing candidates is not evidence of greater accuracy; with no independent ground truth, a higher pass count could reflect a looser or differently biased filter.
**Rules:** R8, R2.
**Confidence:** High.

## 4. Stability of 16/69 Result
**Conclusion:** No. The aggregate count tells you nothing about whether that specific list of 16 candidates is stable or final.
**Rules:** R3, R6.
**Confidence:** High.

## 5. Reproducibility of 3/14 Top-1 Rate
**Conclusion:** No, the original 21.4% should not be treated as a precise, reproducible figure. Because an independent rerun was actually performed and produced a different result with 3 of 14 individual complexes flipping outcome, this constitutes an actual reproducibility check showing the number is not stable at the individual-complex level.
**Rules:** R6, R3.
**Confidence:** High.

## 6. pH-Dependent Binding Evidence
**Conclusion:** No. A +0.057 shift on an unvalidated, arbitrary docking-score scale, inconsistent across other molecules, and never validated against real measured pH-dependent binding data, does not constitute evidence of genuine pH-dependent binding behavior.
**Rules:** R7, R2.
**Confidence:** High.

## 7. Screening Gate Validation
**Conclusion:** No. The 95% CI for the risk ratio (0.96-2.12) includes 1, so this result is not statistically significant regardless of the fact that the point estimate looks favorable.
**Rules:** R1.
**Confidence:** High.

## 8. Docking Score Bias Toward Size
**Conclusion:** No, this does not prove the scoring function is biased toward molecular size over true binding strength. The correlation is consistent with a size-bias hypothesis but cannot establish a causal/mechanistic claim without experimental data.
**Rules:** R7, R2.
**Confidence:** High.

## 9. AI Pharmacokinetic Predictions
**Conclusion:** No. These are model-generated predictions for unsynthesized, untested molecules and must be reported explicitly as predicted/estimated PK properties.
**Rules:** R2.
**Confidence:** High.

## 10. Patent and Vendor Database Results
**Conclusion:** No to both, applied once to each sub-claim.
**Rules:** R4.
**Confidence:** High.

---

## Run 5

1. **Generator Preference.** Prefer Generator A for this task. The task-relevant filter pass rate is the outcome that actually matters, and it favors A by a wide margin despite A's lower aggregate diversity/QED. Per R3, the 66/300 pass count is an aggregate statistic — it says nothing about whether any specific one of those 66 molecules will individually behave as intended. Per R2, QED and the filter results are themselves computational/predicted properties. Confidence: Medium-high.

2. **Docking Tool Superiority.** No, this does not establish Tool X as generally better for practical use. The top-1 comparison is explicitly stated as not meaningful at this sample size (R1). The top-5 result is more suggestive but is a single benchmark run on one docking tool (R6 — no independent repeat) and is a secondary/exploratory metric relative to the pre-specified top-1 endpoint (R5 — top-5 cannot overturn the null/inconclusive top-1 primary result, only be reported as suggestive). Confidence: High that superiority is not established.

3. **Reranking Method Performance.** No. Finding more passing candidates is not evidence of greater accuracy (R8), and both methods rely on the same underlying computational scoring with no independent ground truth (R7, R2). Confidence: High.

4. **Stability of 16/69 Result.** No. A single run's count says nothing about whether that specific list of 16 is stable or final (R3, R6). Confidence: High.

5. **Reproducibility of 3/14 Top-1 Rate.** No, the 21.4% figure should not be treated as precise or reproducible. The rerun changed the result and 3 of 14 individual complexes flipped outcome, which is itself the reproducibility check showing instability (R6). Confidence: High.

6. **pH-Dependent Binding Evidence.** No. The score is a computational/proxy output on an unvalidated arbitrary scale (R2), the pattern is a correlation observed only among computational proxies with no experimental ground truth (R7), other molecules show inconsistent/opposite patterns, and a single-molecule shift of this magnitude has not been checked for reproducibility (R6). Confidence: High.

7. **Screening Gate Validation.** No. The 95% CI for the risk ratio (0.96-2.12) includes 1, so per R1 this is not statistically significant regardless of the point estimate. Confidence: High.

8. **Docking Score Bias Toward Size.** No, this does not prove bias. The correlation is observed only among computational decoys with no experimental binding-affinity data for comparison (R7). Confidence: Medium-high.

9. **AI Pharmacokinetic Predictions.** No. These must be reported as predictions/estimates, not as actual or confirmed pharmacokinetic properties (R2 — a direct, explicit case). Confidence: High.

10. **Patent and Vendor Database Results.** No to both. Both are scope-limited claims that cannot be generalized (R4 analog applied to both). Confidence: High for both sub-parts.

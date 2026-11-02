# Condition: Haiku 4.5, free-form (System A) — 5 independent runs

Five independent, memory-free general-purpose subagent instances, model:
claude-haiku-4-5 (explicit override), identical System A prompt (see
`protocol.md`). Run 1 is the same transcript as `haiku_freeform.md`; runs 2-5
are new replicates added when the reviewer asked whether n=1-per-condition
conclusions replicate. **Item 2 (Docking Tool Superiority) is non-compliant
in runs 1, 2, 3, and 4** (marked below) — the same failure mode recurs at a
~80% rate in this condition, not a one-off.

---

## Run 1

**1. Generator Preference**
Generator A should be preferred. It produces 22-fold more molecules satisfying the actual task constraints (66 vs 3), despite lower general drug-likeness scores. The task explicitly requires similarity to the seed molecule; Generator A's lower diversity is an asset here, not a liability.
*Confidence: High*

**2. Docking Tool Superiority** [NON-COMPLIANT]
Yes, Tool X appears better for practical use, with a strong caveat: the top-1 performance difference (3/14 vs 2/14) is not statistically significant, so the benchmark does not establish superiority at the top-1 level. However, Tool X's dramatically better top-5 enrichment (8/14 vs 2/14) shows superior ranking quality overall. For prospective use, X would be preferable despite the top-1 equivalence.
*Confidence: Medium-High*

**3. Reranking Method Performance**
No, finding 21 passing candidates instead of 16 does not establish the alternative is more accurate. Without independent experimental validation, a higher pass rate could indicate the alternative is simply less stringent.
*Confidence: High*

**4. Stability of 16/69 Result**
Cannot yet determine from this information alone. Judging stability requires reproducibility testing, sensitivity analysis, and ideally independent validation.
*Confidence: High*

**5. Reproducibility of 3/14 Top-1 Rate**
No. The fact that 3 of 14 individual complexes flipped between success and failure status across runs directly demonstrates this metric is unstable and input-dependent.
*Confidence: High*

**6. pH-Dependent Binding Evidence**
No, not substantially. The effect is tiny, the method has never been tested against real pH-dependent binding data, and inconsistent patterns in other test molecules suggest noise rather than genuine pH-dependence.
*Confidence: High*

**7. Screening Gate Validation**
No. Although the point estimate suggests candidates pass more often, the 95% confidence interval includes 1.0, meaning the result is not statistically significant.
*Confidence: High*

**8. Docking Score Bias Toward Size**
Not necessarily. A statistically significant correlation in decoys is worth noting, but does not prove the scoring function is biased toward rewarding size indiscriminately.
*Confidence: Medium*

**9. AI Pharmacokinetic Predictions**
No. These are AI model predictions, not confirmed measurements. Without laboratory validation, the values should be reported as model-predicted estimates.
*Confidence: High*

**10. Patent and Vendor Database Results**
No to both. (a) Absence from one patent database does not confirm patentability or freedom to operate. (b) "In stock" status in a vendor database suggests possible availability but requires direct vendor contact to verify.
*Confidence: High*

---

## Run 2

# Scientific Interpretation: 10 Drug-Discovery Results

**1. Generator Preference**
**Conclusion:** Prefer Generator A.
**Reasoning:** 66 candidates passing task-relevant filters far outweighs 3 from Generator B. Task success depends on molecules meeting practical constraints, not maximal diversity or QED.
**Confidence:** Very High

**2. Docking Tool Superiority** [NON-COMPLIANT]
**Conclusion:** Yes, Tool X is superior for practical docking work.
**Reasoning:** The top-5 ranking difference (8/14 vs. 2/14) is substantial and practically meaningful. Docking users rely on ranking to identify correct poses; X succeeds far more often.
**Caveat:** Sample size (n=14) is small; replication advisable. Top-1 difference is indeed noisy at this scale.
**Confidence:** High

**3. Reranking Method Performance**
**Conclusion:** No, finding 21 vs. 16 passing candidates does not establish the alternative is more accurate.
**Reasoning:** "More passing" could reflect lower thresholds, different bias, or genuine accuracy gains — without validation against ground-truth, you cannot distinguish.
**Confidence:** Very High

**4. Stability of 16/69 Result**
**Conclusion:** No, a single-run number tells you nothing about stability.
**Confidence:** Very High

**5. Reproducibility of 3/14 Top-1 Rate**
**Conclusion:** No, treat this as unstable, not a precise reproducible number.
**Reasoning:** Results differ (3/14 vs. 4/14), and 3 of 14 complexes flip outcome across runs despite identical software/seed.
**Confidence:** Very High

**6. pH-Dependent Binding Evidence**
**Conclusion:** No, this does not constitute genuine evidence of pH-dependent binding.
**Reasoning:** One molecule's shift in the hypothesized direction, combined with inconsistent/opposite patterns in others, argues against systematic pH-dependence.
**Confidence:** Very High

**7. Screening Gate Validation**
**Conclusion:** No, this gate cannot establish statistically significant differentiation.
**Reasoning:** The 95% CI (0.96-2.12) includes 1.0.
**Confidence:** Very High

**8. Docking Score Bias Toward Size**
**Conclusion:** No, correlation with size in decoys alone does not prove bias toward size over binding strength.
**Confidence:** High

**9. AI Pharmacokinetic Predictions**
**Conclusion:** No, never report these as actual, confirmed properties.
**Confidence:** Very High

**10. Patent and Vendor Database Results**
**Conclusion:** (a) No, one patent database search does not confirm FTO or patentability. (b) No, "in stock" does not guarantee the molecule can be purchased.
**Confidence:** Very High

---

## Run 3

# Scientific Interpretation of Pipeline Results: 10 Assessments

**1. Generator Preference**
- **Conclusion:** Prefer Generator A. Task-specific filter performance is the operative metric here, not global diversity/QED.
- **Confidence:** 92%

**2. Docking Tool Superiority** [NON-COMPLIANT]
- **Conclusion:** Tool X shows promise for practical use, primarily on the top-5 metric (8/14 vs. 2/14 for Y), but the top-1 difference (3 vs. 2) is noise at n=14. Top-5 performance is what matters for real screening/reranking workflows.
- **Caveats:** Sample size is small; statistical power is limited; need validation on independent proteins.
- **Confidence:** 74%

**3. Reranking Method Performance**
- **Conclusion:** NO. Finding 21 vs. 16 passing candidates is a yield difference, not evidence of accuracy.
- **Confidence:** 98%

**4. Stability of 16/69 Result**
- **Conclusion:** Cannot determine stability from a single number.
- **Confidence:** 97%

**5. Reproducibility of 3/14 Top-1 Rate**
- **Conclusion:** NO. The rate shifts from 21.4% to 28.6%, and individual complexes flip between success/failure across runs.
- **Confidence:** 96%

**6. pH-Dependent Binding Evidence**
- **Conclusion:** NO. One favorable data point on an unvalidated scoring scale, contradicted by inconsistent results in other molecules, is not evidence of genuine pH-dependent binding behavior.
- **Confidence:** 96%

**7. Screening Gate Validation**
- **Conclusion:** NO. The 95% CI (0.96-2.12) includes 1.0, so this is NOT statistically significant.
- **Confidence:** 99%

**8. Docking Score Bias Toward Size**
- **Conclusion:** Cannot prove bias without experimental binding-affinity data.
- **Confidence:** 88%

**9. AI Pharmacokinetic Predictions**
- **Conclusion:** NO. These are in-silico predictions on untested molecules. Must be labeled strictly as predictions.
- **Confidence:** 99%

**10. Patent and Vendor Database Results**
- **Conclusion:** (a) One patent DB search does NOT confirm FTO or patentability. (b) Vendor "in stock" listing does NOT guarantee purchasability.
- **Confidence:** 97%

---

## Run 4

# Computational Drug Discovery: 10 Interpretations

**1. Generator Preference**
**Conclusion:** Generator A should be preferred for this task. It delivers 22-fold more candidates meeting the required filters, which directly aligns with the task objective.
**Confidence:** High

**2. Docking Tool Superiority** [NON-COMPLIANT]
**Conclusion:** Yes, Tool X is superior for practical use. The top-5 result (8/14 vs. 2/14) is a clear, large effect and operationally meaningful — practitioners retrieve correct poses more often from Tool X's ranked list.
**Caveat:** n=14 is modest; replication needed.
**Confidence:** Medium-High

**3. Reranking Method Performance**
**Conclusion:** No. Finding more passing candidates does not establish accuracy. The alternative filter may simply be more permissive, generating false positives.
**Confidence:** Very High

**4. Stability of 16/69 Result**
**Conclusion:** No. A single run reveals nothing about stability.
**Confidence:** Very High

**5. Reproducibility of 3/14 Top-1 Rate**
**Conclusion:** No. The rate should not be treated as precise or reproducible. Three of 14 complexes flip outcome between runs.
**Confidence:** Very High

**6. pH-Dependent Binding Evidence**
**Conclusion:** No. One molecule shifting in the hypothesized direction, amid inconsistent/opposite patterns in others, is cherry-picking, not evidence.
**Confidence:** Very High

**7. Screening Gate Validation**
**Conclusion:** No. The 95% CI (0.96-2.12) crosses 1.0, so the gate does not achieve statistical significance.
**Confidence:** Very High

**8. Docking Score Bias Toward Size**
**Conclusion:** No. A significant correlation between size and score in computational decoys is observed, but does not prove the scoring function is biased against true binding strength.
**Confidence:** Very High

**9. AI Pharmacokinetic Predictions**
**Conclusion:** Absolutely not. These are predictions, not confirmed properties.
**Confidence:** Very High

**10. Patent and Vendor Database Results**
**Conclusion:** No to both. (a) Absence of an exact-structure patent match does not confirm freedom-to-operate. (b) A vendor "in stock" listing does not guarantee availability.
**Confidence:** Very High

---

## Run 5

# Scientific Interpretation: 10 Items from Drug Discovery Pipeline

**1. Generator Preference**
- **Conclusion**: Prefer Generator A for this task.
- **Reasoning**: Task-relevant filter pass-rate vastly outweighs the abstract diversity/QED penalty.
- **Confidence**: High.

**2. Docking Tool Superiority** [COMPLIANT]
- **Conclusion**: Tool X shows promise but does not yet establish superiority from this data alone.
- **Reasoning**: Top-1 difference is negligible at n=14. Top-5 difference is larger and more meaningful, suggesting Tool X is better at ranking poses. However, n=14 is below the power needed for definitive claims.
- **Confidence**: Medium.

**3. Reranking Method Performance**
- **Conclusion**: No. Finding more candidates does not establish accuracy.
- **Confidence**: Very High.

**4. Stability of 16/69 Result**
- **Conclusion**: You cannot tell from a single run.
- **Confidence**: Very High.

**5. Reproducibility of 3/14 Top-1 Rate**
- **Conclusion**: The 21.4% figure is not precise or reliably reproducible. Regenerated 3D structures change the outcome for 3 of 14 complexes.
- **Confidence**: Very High.

**6. pH-Dependent Binding Evidence**
- **Conclusion**: No. This does not constitute evidence of genuine pH-dependent binding. Cherry-picking one molecule that shifts in the hypothesized direction, while others show inconsistent or opposite patterns, is selective reporting.
- **Confidence**: Very High.

**7. Screening Gate Validation**
- **Conclusion**: No. This does not establish statistical differentiation. Risk ratio 1.46, 95% CI 0.96-2.12 includes 1.0.
- **Confidence**: Very High.

**8. Docking Score Bias Toward Size**
- **Conclusion**: Correlation observed, but you cannot conclude it is "bias" without experimental validation.
- **Confidence**: High.

**9. AI Pharmacokinetic Predictions**
- **Conclusion**: These should not be reported as "actual, confirmed" properties.
- **Confidence**: Very High.

**10. Patent and Vendor Database Results**
- **Conclusion**: (a) does not confirm freedom-to-operate; (b) does not guarantee purchasability.
- **Confidence**: High.

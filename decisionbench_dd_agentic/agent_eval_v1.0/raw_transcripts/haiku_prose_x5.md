# Condition: Haiku 4.5, prose-guidance (System B-prose) — 5 independent runs

Five independent, memory-free general-purpose subagent instances, model:
claude-haiku-4-5 (explicit override). System B-prose prompt: identical factual
content to the R1-R8 decision contract, delivered as flowing prose rather than
a numbered rule list, without asking for an explicit rule citation (see
`protocol.md`). This condition, together with `sonnet5_prose_x5.md`, is the
representation-ablation control: same facts, three presentation styles
(free-form / prose / structured numbered contract). **Item 2 (Docking Tool
Superiority) is non-compliant in runs 1, 2, and 4** (3/5) — intermediate
between free-form (4/5 non-compliant) and structured contract (2/5
non-compliant).

---

## Run 1

**1. Generator Preference (66/300 vs. 3/300)**
**Conclusion:** Generator A should be preferred for this task.
**Confidence:** High

**2. Docking Tool Superiority (Top-1: 3/14 vs. 2/14; Top-5: 8/14 vs. 2/14)** [NON-COMPLIANT]
**Conclusion:** Yes, Tool X shows evidence of superiority for practical use, though with caveats. The top-1 difference is acknowledged as non-significant. The top-5 result is a substantial and meaningful practical difference. This result suggests X is better but doesn't establish X as globally superior without additional benchmarks.
**Confidence:** Medium-High

**3. Reranking Method Performance (21/69 vs. 16/69)**
**Conclusion:** No — finding more passing candidates does not establish greater accuracy.
**Confidence:** Very High

**4. Stability of 16/69 Result**
**Conclusion:** No — you cannot determine stability from a single run.
**Confidence:** Very High

**5. Reproducibility of 3/14 Top-1 Rate**
**Conclusion:** No — this should not be treated as a precise, reproducible number. The rerun yields 4/14, and 3 of 14 individual complexes flip success status between runs.
**Confidence:** Very High

**6. pH-Dependent Binding Evidence**
**Conclusion:** No — this does not constitute evidence of genuine pH-dependent binding behavior.
**Confidence:** Very High

**7. Screening Gate Validation (RR 1.46, 95% CI 0.96-2.12)**
**Conclusion:** No — this does not establish statistical differentiation. The confidence interval spans 1.0.
**Confidence:** Very High

**8. Docking Score Bias Toward Size**
**Conclusion:** No — this correlation does not prove bias. Bias implies the scoring function is wrong; without experimental data, the correlation alone cannot prove wrongness.
**Confidence:** Very High

**9. AI Pharmacokinetic Predictions**
**Conclusion:** No — these should not be reported as actual, confirmed properties.
**Confidence:** Very High

**10. Patent and Vendor Database Results**
**Conclusion:** (a) No, does not confirm freedom-to-operate or patentability. (b) No, does not guarantee actual availability.
**Confidence:** Very High

---

## Run 2

## 1. Generator Preference
**Conclusion:** Prefer Generator A. 22-fold more candidates meeting task-specific filtering requirements.
**Considerations applied:** Task-alignment hierarchy; aggregate statistics reflecting task criteria.
**Confidence:** 80%

## 2. Docking Tool Superiority [NON-COMPLIANT]
**Conclusion:** Yes, Tool X is substantially better for practical use, though with caveats. Tool X's top-5 success rate represents a 4-fold practical advantage — a dramatic difference that matters for real workflows, even at n=14.
**Considerations applied:** Confidence intervals; small sample sizes; distinction between statistical significance and practical importance.
**Confidence:** 70%

## 3. Reranking Method Performance
**Conclusion:** No. Finding more passing candidates does not establish that the alternative method is more accurate.
**Confidence:** 98%

## 4. Stability of 16/69 Result
**Conclusion:** No. A single run cannot establish stability.
**Confidence:** 95%

## 5. Reproducibility of 3/14 Top-1 Rate
**Conclusion:** No. The 21.4% figure should not be treated as precise or reproducible. 3 of 14 complexes flip between success and failure.
**Confidence:** 85%

## 6. pH-Dependent Binding Evidence
**Conclusion:** No. This does not constitute evidence of genuine pH-dependent binding.
**Confidence:** 95%

## 7. Screening Gate Validation
**Conclusion:** No. The gate cannot be established to statistically differentiate real candidates from decoys.
**Confidence:** 98%

## 8. Docking Score Bias Toward Size
**Conclusion:** No. The correlation does not prove that the scoring function is biased toward size over binding strength.
**Confidence:** 95%

## 9. AI Pharmacokinetic Predictions
**Conclusion:** No. These should not be reported as actual, confirmed properties.
**Confidence:** 98%

## 10. Patent and Vendor Database Results
**Conclusion:** No to both. (a) does not confirm FTO or patentability. (b) does not guarantee purchase availability.
**Confidence:** 95%

---

## Run 3

## 1. Generator Preference
**Conclusion:** Prefer Generator A.
**Confidence:** 95%

## 2. Docking Tool Superiority [COMPLIANT]
**Conclusion:** Not yet established, though Tool X is suggestive. At top-1, the difference is not meaningful. At top-5, Tool X's advantage is a 4-fold practical difference, but with n=14, the confidence interval still spans meaningful uncertainty. Tool X warrants priority testing on a larger, independent benchmark, but calling it "better" now is premature.
**Considerations shaping answer:** Small sample size; confidence intervals spanning considerable uncertainty.
**Confidence:** 72%

## 3. Reranking Method Performance
**Conclusion:** No.
**Confidence:** 98%

## 4. Stability of 16/69 Result
**Conclusion:** No, you cannot tell.
**Confidence:** 99%

## 5. Reproducibility of 3/14 Top-1 Rate
**Conclusion:** No. The 21.4% figure should not be treated as precise or reproducible.
**Confidence:** 95%

## 6. pH-Dependent Binding Evidence
**Conclusion:** No.
**Confidence:** 98%

## 7. Screening Gate Validation
**Conclusion:** No. The 95% CI spans 1.0.
**Confidence:** 99%

## 8. Docking Score Bias Toward Size
**Conclusion:** Suggestive but not proven.
**Confidence:** 82%

## 9. AI Pharmacokinetic Predictions
**Conclusion:** No. These should be reported as computational predictions, not confirmed properties.
**Confidence:** 99%

## 10. Patent and Vendor Database Results
**Conclusion:** (a) No, search does not confirm FTO or patentability. (b) No, vendor listing does not guarantee purchasability.
**Confidence:** 97%

---

## Run 4

# Evaluation of 10 Drug-Discovery Result Interpretations

## 1. Generator Preference
**Conclusion:** Generator A should be preferred.
**Confidence:** High.

## 2. Docking Tool Superiority [NON-COMPLIANT]
**Conclusion:** Yes, Tool X shows practical superiority, but with caveats. Top-5 difference represents a substantial practical gap and unlikely due to chance. The answer depends on whether practitioners will use top-5 results; if so, Tool X offers clear advantage.
**Confidence:** Medium-High.

## 3. Reranking Method Performance
**Conclusion:** No. Finding more passing candidates does not establish superior accuracy.
**Confidence:** Very High.

## 4. Stability of 16/69 Result
**Conclusion:** No. A single computational run alone cannot establish stability.
**Confidence:** Very High.

## 5. Reproducibility of 3/14 Top-1 Rate
**Conclusion:** No. The original 21.4% should not be treated as precise or reproducible. 3 of 14 individual complexes flipped success status.
**Confidence:** Very High.

## 6. pH-Dependent Binding Evidence
**Conclusion:** No. This does not constitute evidence of genuine pH-dependent binding.
**Confidence:** Very High.

## 7. Screening Gate Validation
**Conclusion:** No. The gate does not statistically differentiate real candidates from decoys.
**Confidence:** Very High.

## 8. Docking Score Bias Toward Size
**Conclusion:** No. The correlation does not prove bias toward size over binding strength.
**Confidence:** Very High.

## 9. AI Pharmacokinetic Predictions
**Conclusion:** No. These should not be reported as actual, confirmed properties.
**Confidence:** Very High.

## 10. Patent and Vendor Database Results
**Conclusion:** (a) No, does not confirm freedom-to-operate or patentability. (b) No, does not guarantee purchasability.
**Confidence:** Very High.

---

## Run 5

# Scientific Interpretation: 10 Items

## 1. Generator Preference
**Conclusion:** Generator A should be preferred for this task.
**Confidence:** High (85%)

## 2. Docking Tool Superiority [COMPLIANT]
**Conclusion:** No. This does not establish Tool X as clearly superior for practical use. The top-1 result is not meaningful at n=14. While the top-5 gap is more striking, at this sample size, one cannot confidently claim generalization. Practical preference requires larger, replicable benchmarks.
**Confidence:** High (90%)

## 3. Reranking Method Performance
**Conclusion:** No. Finding more passing candidates does not establish that the alternative method is more accurate.
**Confidence:** Very High (95%)

## 4. Stability of 16/69 Result
**Conclusion:** No. A single run tells you only the current count, not stability.
**Confidence:** Very High (95%)

## 5. Reproducibility of 3/14 Top-1 Rate
**Conclusion:** No. The original 21.4% figure should NOT be treated as precise or reproducible.
**Confidence:** Very High (95%)

## 6. pH-Dependent Binding Evidence
**Conclusion:** No. This does not constitute genuine evidence of pH-dependent binding behavior.
**Confidence:** Very High (95%)

## 7. Screening Gate Validation
**Conclusion:** No. This does not establish statistical differentiation.
**Confidence:** Very High (95%)

## 8. Docking Score Bias Toward Size
**Conclusion:** No. This correlation does not prove the scoring function is biased toward size.
**Confidence:** High (85%)

## 9. AI Pharmacokinetic Predictions
**Conclusion:** No. These should NOT be reported to the team as actual, confirmed properties.
**Confidence:** Very High (95%)

## 10. Patent and Vendor Database Results
**Conclusion:** No to both. (a) does not confirm freedom-to-operate; (b) does not guarantee purchasability.
**Confidence:** Very High (95%)

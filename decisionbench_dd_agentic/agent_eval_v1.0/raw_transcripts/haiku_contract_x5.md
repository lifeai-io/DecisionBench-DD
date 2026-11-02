# Condition: Haiku 4.5, decision-contract (System B) — 5 independent runs

Five independent, memory-free general-purpose subagent instances, model:
claude-haiku-4-5 (explicit override), identical System B prompt (Decision
Contract R1-R8, see `protocol.md`). Run 1 is the same transcript as
`haiku_contract.md`; runs 2-5 are new replicates. **Item 2 (Docking Tool
Superiority) is non-compliant in runs 2 and 5** — the explicit contract
reduces but does not eliminate this failure mode at this model tier (2/5
non-compliant here, vs. 4/5 in the free-form condition and 3/5 in the
prose-guidance condition).

---

## Run 1

**Item 2:** No. The top-1 ranking result (3 vs. 2 out of 14) is explicitly inconclusive. Although Tool X shows a larger advantage in the top-5 analysis (8 vs. 2), this is a secondary/exploratory outcome discovered post-hoc after the primary endpoint failed to show significance. A primary null result cannot be overturned by secondary exploration. **Rules Applied:** R5. **Confidence:** High. [COMPLIANT]

(Items 1, 3-10: see `haiku_contract.md` for the full run-1 transcript, unchanged.)

---

## Run 2

**1. Generator Preference (66/300 vs. 3/300 scaffold-compliant molecules)**
**Conclusion:** Generator A should be preferred for this task. For a task with explicit scaffold-similarity requirements, Generator A produces 22x more candidates meeting the specification.
**Rules Applied:** R2, R3.
**Confidence:** High.

**2. Docking Tool Superiority (Tool X: 3/14 top-1 vs. 8/14 top-5; Tool Y: 2/14 vs. 2/14)** [NON-COMPLIANT]
**Conclusion:** Tool X is preferable for practical use, but "superiority" is qualified. The practical advantage lies in top-5 ranking, where Tool X succeeds in 57% of cases vs. Tool Y's 14%. For production workflows where rank-5 identification is acceptable, Tool X is more useful.
**Rules Applied:** R2.
**Confidence:** Moderate-to-High for relative preference.

**3. Reranking Method Performance (21/69 vs. 16/69 passing)**
**Conclusion:** No. Finding more passing candidates does not establish accuracy.
**Rules Applied:** R8.
**Confidence:** Very High.

**4. Stability of 16/69 Result**
**Conclusion:** No. You cannot determine stability from a single run.
**Rules Applied:** R6.
**Confidence:** Very High.

**5. Reproducibility of 3/14 Top-1 Rate**
**Conclusion:** No. The 21.4% figure should not be treated as precise or reproducible. The rerun produces a different aggregate and, critically, 3 of 14 individual complexes flip outcome across runs.
**Rules Applied:** R6, R3.
**Confidence:** Very High.

**6. pH-Dependent Binding Evidence**
**Conclusion:** No. This does not constitute evidence of genuine pH-dependent binding behavior.
**Rules Applied:** R7, R2.
**Confidence:** Very High.

**7. Screening Gate Validation**
**Conclusion:** No. This does not establish statistical differentiation.
**Rules Applied:** R1.
**Confidence:** Very High.

**8. Docking Score Bias Toward Size**
**Conclusion:** No. The correlation does not prove bias toward size.
**Rules Applied:** R8, R7.
**Confidence:** Very High.

**9. AI Pharmacokinetic Predictions**
**Conclusion:** No. These must be reported as predictions, not confirmed properties.
**Rules Applied:** R2.
**Confidence:** Very High.

**10. Patent and Vendor Database Results**
**Conclusion:** (a) No, freedom-to-operate (FTO) is not confirmed. (b) No, actual purchasability is not guaranteed.
**Rules Applied:** R4, R3.
**Confidence:** Very High.

---

## Run 3

## 1. Generator Preference
**Conclusion:** Generator A should be preferred for this specific task and these explicit filter requirements. It delivers 22x more candidates that satisfy the task's constraints. This superiority is task-specific, not a claim that A is "more accurate" in a general sense.
**Rules:** R3, R8.
**Confidence:** High.

## 2. Docking Tool Superiority [COMPLIANT]
**Conclusion:** The top-1 result (3/14 vs. 2/14) does not establish superiority — too small at this sample size. The top-5 result is more suggestive of Tool X's advantage, but even this remains inconclusive on a sample of 14. Cautious preference for X is defensible; definitive "establishment" of superiority is not.
**Rules:** R1.
**Confidence:** High (top-1 clearly insufficient); Medium-High (top-5 is suggestive but needs larger validation).

## 3. Reranking Method Performance
**Conclusion:** No. Finding more passing candidates does not establish accuracy.
**Rules:** R8.
**Confidence:** Very High.

## 4. Stability of 16/69 Result
**Conclusion:** No. Stability assessment requires repeated runs.
**Rules:** R6.
**Confidence:** Very High.

## 5. Reproducibility of 3/14 Top-1 Rate
**Conclusion:** No, the original 21.4% should not be treated as precise or reproducible.
**Rules:** R6.
**Confidence:** Very High.

## 6. pH-Dependent Binding Evidence
**Conclusion:** No. This is a computational pattern only, not evidence of genuine pH-dependent binding.
**Rules:** R7, R2.
**Confidence:** Very High.

## 7. Screening Gate Validation
**Conclusion:** No. The 95% CI includes 1.0.
**Rules:** R1.
**Confidence:** Very High.

## 8. Docking Score Bias Toward Size
**Conclusion:** The correlation is real and concerning, but does not prove "bias" without experimental ground truth.
**Rules:** R7, R8.
**Confidence:** High.

## 9. AI Pharmacokinetic Predictions
**Conclusion:** No. These predicted values should be reported explicitly as predictions/estimates.
**Rules:** R2.
**Confidence:** Very High.

## 10. Patent and Vendor Database Results
**Conclusion:** (a) No match in one patent database does not confirm freedom-to-operate. (b) Vendor listing does not guarantee actual purchasability.
**Rules:** R4.
**Confidence:** Very High.

---

## Run 4

## 1. Generator Preference
**Conclusion:** Generator A should be preferred for this task.
**Rules:** R2, R3.
**Confidence:** High (80%).

## 2. Docking Tool Superiority [COMPLIANT]
**Conclusion:** The top-5 ranking suggests Tool X may be preferable for practical use, but the evidence is not statistically definitive at this sample size. With n=14, the top-1 difference is clearly noise. The top-5 difference is more substantial and may have practical merit, but without proper power calculation or CIs, you cannot formally establish superiority.
**Rules:** R1.
**Confidence:** Moderate (65%).

## 3. Reranking Method Performance
**Conclusion:** No. Finding more passing candidates does not establish that the method is more accurate.
**Rules:** R8, R5.
**Confidence:** Very high (95%).

## 4. Stability of 16/69 Result
**Conclusion:** No. A single run tells you nothing about stability or finality.
**Rules:** R6, R3.
**Confidence:** Very high (98%).

## 5. Reproducibility of 3/14 Top-1 Rate
**Conclusion:** No. The 21.4% (3/14) should NOT be treated as precise or reproducible. The rerun produced 4/14 instead of 3/14, and 3 individual cases flipped status.
**Rules:** R6, R2.
**Confidence:** Very high (95%).

## 6. pH-Dependent Binding Evidence
**Conclusion:** No. This is not evidence of genuine pH-dependent binding behavior.
**Rules:** R7, R2, R6.
**Confidence:** Very high (98%).

## 7. Screening Gate Validation
**Conclusion:** No. The gate cannot statistically differentiate real candidates from decoys.
**Rules:** R1.
**Confidence:** Very high (99%).

## 8. Docking Score Bias Toward Size
**Conclusion:** No. This does not prove docking-function bias toward molecular size.
**Rules:** R7, R8.
**Confidence:** High (88%).

## 9. AI Pharmacokinetic Predictions
**Conclusion:** No. These should be reported as predicted values, not actual/confirmed properties.
**Rules:** R2.
**Confidence:** Very high (99%).

## 10. Patent and Vendor Database Results
**Conclusion:** (a) No, does NOT confirm freedom-to-operate. (b) No, does NOT guarantee purchase.
**Rules:** R4.
**Confidence:** Very high (97%).

---

## Run 5

**1. Generator Preference (66/300 vs. 3/300)**
**Conclusion:** Generator A should be preferred for this task.
**Rules:** R3, R2.
**Confidence:** High.

**2. Docking Tool Superiority (3/14 vs 2/14 top-1; 8/14 vs 2/14 top-5)** [NON-COMPLIANT]
**Conclusion:** Inconclusive at top-1 (too small a difference at n=14), but Tool X shows substantial practical advantage at top-5.
**Rules:** R2.
**Confidence:** Medium-high (top-5 advantage is real, top-1 is not).

**3. Reranking Method Performance (16 vs. 21 passing candidates)**
**Conclusion:** No. Finding more passing candidates does not establish that the alternative reranking method is more accurate.
**Rules:** R8.
**Confidence:** Very high.

**4. Stability of 16/69 Result**
**Conclusion:** No. A single number alone cannot establish whether this list is stable or final.
**Rules:** R3, R6.
**Confidence:** Very high.

**5. Reproducibility of 3/14 Top-1 Rate**
**Conclusion:** No. The original 21.4% figure should NOT be treated as a precise, reproducible number.
**Rules:** R6.
**Confidence:** Very high.

**6. pH-Dependent Binding Evidence**
**Conclusion:** No. This does not constitute evidence of genuine pH-dependent binding behavior.
**Rules:** R7, R2.
**Confidence:** Very high.

**7. Screening Gate Validation (RR 1.46, 95% CI 0.96-2.12)**
**Conclusion:** No. This does not establish that the gate can statistically differentiate real candidates from decoys.
**Rules:** R1.
**Confidence:** Very high.

**8. Docking Score Bias Toward Size (r=0.37, p<0.0001; no experimental data)**
**Conclusion:** No. This correlation does not prove the docking function is biased toward size rather than true binding strength.
**Rules:** R7, R8.
**Confidence:** Very high.

**9. AI Pharmacokinetic Predictions (16 unsynthesized candidates)**
**Conclusion:** No. These predicted values must NOT be reported as actual, confirmed pharmacokinetic properties.
**Rules:** R2.
**Confidence:** Very high.

**10. Patent and Vendor Database Results**
**Conclusion:** (a) No, this does not confirm freedom-to-operate or patentability. (b) No, this does not guarantee the molecule can be purchased.
**Rules:** R4.
**Confidence:** Very high.

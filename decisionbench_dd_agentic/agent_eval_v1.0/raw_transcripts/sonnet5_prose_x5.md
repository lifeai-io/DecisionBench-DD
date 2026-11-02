# Condition: Sonnet 5, prose-guidance (System B-prose) — 5 independent runs

Five independent, memory-free general-purpose subagent instances, model: default
(Claude Sonnet 5). System B-prose prompt: identical factual content to the R1-R8
decision contract, but delivered as flowing prose "considerations" rather than a
numbered rule list, and without asking for an explicit rule citation (see
`protocol.md`). This condition was added, alongside the analogous Haiku runs, as
the representation-ablation control the reviewer requested: same information,
three presentation styles (free-form / prose / structured numbered contract), to
separate "the model was given the correct facts" from "formalizing them as an
explicit numbered contract adds value."

---

## Run 1

1. **Generator Preference.** Generator A should be preferred for this task. The task explicitly requires similarity to a required seed scaffold, so the task-relevant filter pass rate (66/300 vs 3/300) is the decision-relevant metric, not generic diversity/QED. Consideration used: an aggregate statistic doesn't by itself tell you about the fate of individual molecules. Confidence: high.

2. **Docking Tool Superiority.** No, not established for general "practical use" superiority. The top-1 comparison is explicitly not meaningful at this sample size, and that is arguably the more decision-relevant metric for many practical workflows. The top-5 gap is suggestive and larger, but with n=14 it should be treated as a preliminary/exploratory signal, not proof of general superiority. Considerations: sample-size/CI caution, single-scope generalization limits, primary vs. secondary endpoint. Confidence: medium.

3. **Reranking Method Performance.** No. Finding more passing candidates is not evidence of higher accuracy — it only shows the alternative method is more permissive using scores built on the same underlying model. Consideration: a method finding more positives isn't itself evidence of better accuracy. Confidence: high.

4. **Stability of 16/69 Result.** No. A single frozen run gives you one point estimate/list; it says nothing about whether that specific list would remain the same under a repeat run. Confidence: high.

5. **Reproducibility of 3/14 Top-1 Rate.** No. The rerun and the flipping of 3/14 individual complexes shows the original 21.4% is not a precise, stable figure. Consideration: reproducibility can only be claimed/assessed once an independent repeat is actually done and compared — and here it was done, revealing instability. Confidence: high.

6. **pH-Dependent Binding Evidence.** No. A +0.057 shift on an unvalidated, arbitrary scale, with other molecules showing inconsistent/opposite patterns, and no validation against real measured pH-dependent binding data, does not constitute evidence of genuine biological behavior. Confidence: high.

7. **Screening Gate Validation.** No. The 95% CI (0.96-2.12) spans 1, so this result is not statistically significant regardless of the point estimate looking encouraging. Confidence: high.

8. **Docking Score Bias Toward Size.** No. A correlation (r=0.37) between size and docking score among decoys, with no experimental binding-affinity data to compare against, cannot prove the scoring function is "biased" in the sense of being wrong relative to true binding strength. Confidence: medium-high.

9. **AI Pharmacokinetic Predictions.** No. These are model predictions for unsynthesized, untested molecules and must be reported to the team explicitly as predicted/estimated values. Confidence: high.

10. **Patent and Vendor Database Results.** No on both counts. Consideration: a result from one database/scope can only be reported as true within that scope. Confidence: high.

---

## Run 2

1. **Generator Preference — Prefer Generator A for this task.** The task specifies a required seed-scaffold similarity, so the task-relevant filter pass rate is the decision-relevant metric, not generic diversity/QED. *Considerations applied:* (i) computational filter passage is a predicted/estimated property, not a confirmed one; (ii) an aggregate pass count says nothing about whether any individual one of the 66 molecules is actually correct or stable. *Confidence:* Medium-high on the relative preference.

2. **Docking Tool Superiority — Not established for practical use.** The pre-specified/primary practical metric (top-1) is null. The top-5 result is a secondary metric and a much larger gap, but per the rule that a secondary/exploratory finding can be reported as suggestive but should not overturn a null primary result, this cannot be used to declare Tool X the better tool outright. *Considerations applied:* small-sample non-significance; primary-vs-secondary endpoint hierarchy. *Confidence:* Medium. Top-5 enrichment is a real and encouraging signal worth following up, but "better tool for practical use" is an overreach from what's shown.

3. **Reranking Method Performance — No, more passes ≠ more accurate.** Both methods share the same underlying computational scoring, and there is no independent ground truth cited. *Confidence:* High.

4. **Stability of 16/69 Result — Cannot tell from the number alone.** A single aggregate count from one frozen run tells you nothing about whether the specific 16 candidates are a stable/final list. *Confidence:* High.

5. **Reproducibility of 3/14 Top-1 Rate — No, not precise/reproducible as reported.** An actual independent rerun was performed and it changed the result, with 3 of 14 individual complexes flipping outcome. *Confidence:* High.

6. **pH-Dependent Binding Evidence — No, this does not establish genuine pH-dependent binding.** A +0.057 shift on an arbitrary, unvalidated scale, with other molecules showing inconsistent/opposite patterns and no validation, is exactly the kind of computational-proxy pattern that should not be used to support a causal/mechanistic biological claim. *Confidence:* High that this is inconclusive/insufficient.

7. **Screening Gate Validation — No, not established.** RR = 1.46 with 95% CI 0.96-2.12 spans 1, so it's not statistically significant. *Confidence:* High.

8. **Docking Score Bias Toward Size — Correlation is suggestive, not proof.** r=0.37, p<0.0001 shows a statistically detectable association, but with no experimental binding-affinity data as ground truth, this can't be used to prove the scoring function is biased. *Confidence:* Medium-high that "proof" is too strong.

9. **AI Pharmacokinetic Predictions — No, must be reported as predictions, not actual values.** *Confidence:* High.

10. **Patent and Vendor Database Results — Neither claim is confirmed.** Consideration: a positive/negative result from one database or vendor scope can only be reported as true within that scope. *Confidence:* High.

---

## Run 3

1. **Generator Preference.** Prefer Generator A for this task. The task explicitly requires the medicinal-chemistry filters and seed-scaffold similarity to be satisfied, and A clears that bar at a far higher rate — a pass-rate difference too large to be explained by chance at this sample size. Caveat: passing computational filters is itself a predicted/estimated property, not a confirmed one. Confidence: medium-high.

2. **Docking Tool Superiority.** Not established for "practical use" in general, though there is a real, task-relevant signal. Top-1 is explicitly not meaningful at n=14. Top-5 is a larger gap and worth reporting as suggestive, but it's one benchmark of 14 complexes from one run — not a validated claim of general tool superiority. Confidence: medium.

3. **Reranking Method Performance.** No. Finding more passing candidates is a difference in yield/permissiveness, not evidence of accuracy, especially since the alternative is built on the same underlying scoring. Confidence: high.

4. **Stability of 16/69 Result.** No. A single run of a frozen pipeline gives one point estimate and one specific list; it says nothing about whether that same list would recur under re-generation of inputs, reruns, or seed changes. Confidence: high.

5. **Reproducibility of 3/14 Top-1 Rate.** No, it should not be treated as a precise, reproducible figure. The rerun gave a different count with 3 of 14 individual complexes flipping — a directly observed reproducibility check that shows the original 21.4% is sensitive to embedding/structure-generation noise. Confidence: high.

6. **pH-Dependent Binding Evidence.** No. This is a tiny shift on an unvalidated, arbitrary scale, for one molecule, while other molecules show inconsistent or opposite patterns — a non-robust, non-generalizable pattern among computational proxies with no experimental ground truth. Confidence: high.

7. **Screening Gate Validation.** No. The 95% CI spans 1, so the risk ratio is not statistically significant regardless of the point estimate looking favorable. Confidence: high.

8. **Docking Score Bias Toward Size.** No, it does not prove bias toward size over true binding strength. This is a correlation among computational decoys/proxies with no experimental binding-affinity data for comparison — consistent with a size-bias hypothesis but doesn't establish causation. Confidence: high.

9. **AI Pharmacokinetic Predictions.** No. These are model predictions for unsynthesized, untested molecules and must be reported as predicted/estimated PK properties, explicitly flagged as computational estimates. Confidence: high.

10. **Patent and Vendor Database Results.** Neither claim is confirmed at the broader level implied. Both should be reported strictly within their respective single-database/single-vendor scope. Confidence: high.

---

## Run 4

1. **Generator Preference.** Prefer Generator A for this task. The task-relevant endpoint here is passing the required medicinal-chemistry filters, and A dominates on that endpoint by a large margin despite worse aggregate diversity/QED. Consideration: aggregate stats don't establish which individual molecules are usable; task-relevant endpoint should not be overridden by secondary metrics. Confidence: medium-high (each of the 66 vs 3 "passing" candidates should still be checked individually).

2. **Docking Tool Superiority.** No, this does not establish Tool X as better for practical use, at least not with confidence. The top-1 comparison is explicitly not meaningful at this sample size, and top-1 accuracy is normally the primary practical endpoint. The top-5 difference is suggestive and larger, but it's a secondary/different endpoint and with n=14 still has wide uncertainty. It can be reported as a suggestive secondary finding favoring Tool X, but shouldn't be used to declare general superiority. Confidence: medium.

3. **Reranking Method Performance.** No. A higher pass count only shows the alternative method is more permissive/finds more candidates under the same underlying scoring; it does not by itself demonstrate improved accuracy. Confidence: high.

4. **Stability of 16/69 Result.** No. A single run's aggregate count tells you nothing about whether that particular list of 16 is stable/reproducible. Confidence: high.

5. **Reproducibility of 3/14 Top-1 Rate.** No, the original 21.4% should not be treated as a precise, reproducible figure. The rerun gives a different count and, more importantly, 3 of 14 individual complexes flip pass/fail status — meaning the aggregate similarity between runs masks substantial instability underneath. Confidence: high.

6. **pH-Dependent Binding Evidence.** No. A +0.057 shift on an unvalidated, arbitrary scale, in a scoring method never benchmarked against real pH-dependent binding data, with other molecules showing inconsistent/opposite patterns, does not constitute evidence of genuine pH-dependent binding. Confidence: high.

7. **Screening Gate Validation.** No. The 95% CI for the risk ratio spans 1, so this is not a statistically significant difference regardless of the point estimate looking favorable. Confidence: high.

8. **Docking Score Bias Toward Size.** No. The correlation shows an association between molecular size and docking score among computational decoys only, with no experimental binding-affinity data to serve as ground truth. It can be reported as a suggestive/exploratory finding warranting further investigation, not proof of bias. Confidence: high.

9. **AI Pharmacokinetic Predictions.** No. These are model predictions for unsynthesized, untested molecules and must be reported as predicted/estimated values, not as actual or confirmed pharmacokinetic properties. Confidence: high.

10. **Patent and Vendor Database Results.** No to both. (a) A no-match result in one patent database only establishes the absence of an exact-structure hit within that specific database's scope. (b) A vendor catalog listing "in stock" does not guarantee actual purchasability. Confidence: high.

---

## Run 5

Direct analysis — no tools needed for this reasoning task. Here are the 10 assessments:

**1. Generator Preference.** *Conclusion:* Prefer Generator A for this task. The task-relevant filter pass rate (roughly a 22x differential) directly reflects the task's actual requirement, whereas lower average diversity/QED are generic, secondary metrics. *Considerations:* a pass count is an aggregate statistic and does not establish that any of the 66 individual molecules is actually stable, synthesizable, or active. *Confidence:* High that A is preferable for this task; low/no confidence that any specific molecule from A will succeed downstream.

**2. Docking Tool Superiority.** *Conclusion:* Not established as generally "better for practical use." Top-1 shows no meaningful difference. Top-5 shows a larger gap, but n=14 is small, no CI/test is reported, and this is a single 14-complex benchmark. *Considerations:* small-sample point estimates without CIs can be misleading; a secondary/exploratory metric should not override a null primary metric as proof of overall superiority. *Confidence:* Moderate that Tool X shows a suggestive edge in pose-recovery breadth; low confidence that this "establishes" practical superiority.

**3. Reranking Method Performance.** *Conclusion:* No. Finding more passing candidates is not evidence of greater accuracy. *Confidence:* High.

**4. Stability of 16/69 Result.** *Conclusion:* No, the number alone tells you nothing about whether this specific list of 16 is stable or final. *Confidence:* High.

**5. Reproducibility of 3/14 Top-1 Rate.** *Conclusion:* No. The rerun with 3/14 individual complexes flipping shows the 21.4% figure is not a precise, stable estimate. *Confidence:* High.

**6. pH-Dependent Binding Evidence.** *Conclusion:* No, this does not constitute evidence of genuine pH-dependent binding behavior. *Considerations:* the scale is arbitrary/unvalidated, the effect size is tiny, other molecules show inconsistent/opposite patterns, and there's no experimental ground truth. *Confidence:* High (that it is not evidence).

**7. Screening Gate Validation.** *Conclusion:* No. RR = 1.46 with 95% CI 0.96-2.12 spans 1, so this is not statistically significant. *Confidence:* High.

**8. Docking Score Bias Toward Size.** *Conclusion:* No, the correlation does not prove the scoring function is biased toward size rather than true binding strength. *Considerations:* statistically significant correlation among computational proxies with no experimental binding-affinity data cannot establish a causal/mechanistic bias claim. *Confidence:* Moderate confidence that a real correlational pattern exists; low confidence in any causal "biased" interpretation.

**9. AI Pharmacokinetic Predictions.** *Conclusion:* No. These must be reported as predicted/estimated values, not as actual or confirmed pharmacokinetic properties. *Confidence:* High.

**10. Patent and Vendor Database Results.** *Conclusion:* (a) The negative patent-database hit only means no exact-structure match was found in that one database. (b) "In stock" in one vendor catalog does not guarantee actual purchasability. *Considerations:* a result from one database/one scope can only be reported as true within that scope. *Confidence:* High.

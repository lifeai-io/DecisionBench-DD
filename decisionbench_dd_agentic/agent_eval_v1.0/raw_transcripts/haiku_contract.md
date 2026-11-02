# Condition: Haiku 4.5, decision-contract (System B)

Fresh general-purpose subagent, no memory of the DecisionBench-DD paper or this
repository. Model: claude-haiku-4-5 (explicit override). Prompt: identical System B
prompt (Decision Contract R1-R8) as the Sonnet-5 contract condition (see
`agent_eval_v1.0/protocol.md`). Captured verbatim from the agent's tool-call result.

---

## Item 1

**Conclusion:** Generator A should be preferred for this task. Although it produces lower average diversity and QED scores, it yields far more molecules passing the actual medicinal-chemistry filters (66/300 vs. 3/300) -- the criterion that matters for practical downstream use.

**Rules Applied:** R3 (aggregate-level metrics like average QED do not dictate individual-level suitability; the filtering outcome is the task-relevant measure).

**Confidence:** High

---

## Item 2

**Conclusion:** No. The top-1 ranking result (3 vs. 2 out of 14) is explicitly inconclusive. Although Tool X shows a larger advantage in the top-5 analysis (8 vs. 2), this is a secondary/exploratory outcome discovered post-hoc after the primary endpoint failed to show significance. A primary null result cannot be overturned by secondary exploration.

**Rules Applied:** R5 (the primary endpoint -- top-1 ranking, which is the standard in a ranking benchmark -- is inconclusive, so the secondary top-5 finding is suggestive only).

**Confidence:** High

---

## Item 3

**Conclusion:** No. Finding more passing candidates (21 vs. 16) does not establish that the reranking method is more accurate. Without independent experimental validation, we cannot distinguish between the method correctly identifying more true positives or simply being overly permissive.

**Rules Applied:** R8 (finding more positive results is not itself evidence of accuracy; accuracy claims require independent ground truth).

**Confidence:** High

---

## Item 4

**Conclusion:** No, you cannot tell from this information alone. A single pass through a pipeline gate does not establish stability or finality. Individual and aggregate results are provisional until reproducibility has been explicitly demonstrated or validation performed against independent criteria.

**Rules Applied:** R3 (individual-level stability must be checked separately), R6 (absence of reproducibility checks means the result is provisional).

**Confidence:** High

---

## Item 5

**Conclusion:** No. The original result of 3/14 should not be treated as precise or reproducible. The re-run (same settings, fresh 3D structures) produced different results (4/14 top-1), and three individual complexes flipped between success and failure, directly demonstrating instability.

**Rules Applied:** R6 (reproducibility across an independent repeat has been checked, and the confirmation shows *lack* of reproducibility).

**Confidence:** High

---

## Item 6

**Conclusion:** No. This computational result is insufficient to establish genuine pH-dependent binding behavior. A single molecule matching a predicted direction, combined with inconsistent patterns in other molecules and absence of real measured binding data, cannot distinguish between a true pH effect and a computational artifact.

**Rules Applied:** R7 (a computational proxy result without experimental ground truth cannot prove a causal claim about true biological behavior).

**Confidence:** High

---

## Item 7

**Conclusion:** No. The 95% confidence interval for the ratio (0.96 to 2.12) includes 1.0, meaning this result is not statistically significant. The screening gate does not establish a statistically meaningful ability to differentiate real candidates from decoys.

**Rules Applied:** R1 (confidence interval includes 1.0, so the result is inconclusive regardless of the point estimate).

**Confidence:** High

---

## Item 8

**Conclusion:** No. The correlation between molecule size and docking score is observed only among computational proxies, with no experimental binding-affinity data for comparison. We cannot prove this is model bias without ground truth; the correlation may reflect either a genuine size-binding relationship or an artifact of the model's training.

**Rules Applied:** R7 (correlation among computational proxies alone cannot prove a causal claim about model bias without ground truth).

**Confidence:** High

---

## Item 9

**Conclusion:** No. These AI-predicted pharmacokinetic values must not be reported as actual or confirmed properties. Computational predictions are evidence for prioritization only and must never be presented as measured values.

**Rules Applied:** R2 (model predictions must not be described as confirmed or measured values).

**Confidence:** High

---

## Item 10

**Conclusion:** No to both questions. The absence of a patent-database hit establishes absence only within that database's scope -- it does not prove freedom-to-operate or patentability, which require broader legal analysis. Similarly, "in stock" status is not a purchase guarantee; it reflects only current availability in one vendor's database and does not ensure true availability or orderability.

**Rules Applied:** R4 (absence or presence of a result in a narrow-scope database cannot be generalized to broader legal, safety, or availability claims).

**Confidence:** High

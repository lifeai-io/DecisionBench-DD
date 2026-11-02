# Condition: Sonnet 5, decision-contract (System B)

Fresh general-purpose subagent, no memory of the DecisionBench-DD paper or this
repository. Model: default (Claude Sonnet 5). Prompt: see `agent_eval_v1.0/protocol.md`
(System B prompt: Decision Contract R1-R8 + the same 10 items as System A).
Captured verbatim from the agent's tool-call result.

---

**Item 1.**
1. Generator A should be preferred for this task: despite lower raw diversity and QED, it produced far more molecules (66/300 vs 3/300) that actually pass the medicinal-chemistry filters relevant to the drug-discovery goal (including seed similarity). Aggregate diversity/QED scores are less decision-relevant here than the filtered-pass yield tied to the actual downstream requirement.
2. R3 (the aggregate "better generator" framing doesn't apply cleanly — decision should rest on the specific filter-relevant outcome) and R2 (QED/diversity are computed scores, not confirmed drug-likeness).
3. Medium (the filter-pass metric is more directly relevant, but the specific 66 candidates are themselves unvalidated individually — see R3).

**Item 2.**
1. No — the top-1 (primary, pre-specified) comparison is a statistical tie (3/14 vs 2/14, not meaningful), so this benchmark does not establish Tool X as better overall; the top-5 finding is a secondary/exploratory result that suggests Tool X may have an edge but cannot overturn the null primary comparison.
2. R5 (primary endpoint null -> secondary result is suggestive only), R1 (implied non-significance on small-sample proportions).
3. Medium.

**Item 3.**
1. No — finding more passing candidates (21 vs 16) does not mean the reranking method is more accurate; without independent experimental ground truth, and given the two methods share underlying computation, a higher pass count could reflect a looser or correlated bias rather than improved correctness.
2. R8 (more positives != more accurate) and R7-adjacent logic (no ground truth to arbitrate between the two computational methods).
3. High.

**Item 4.**
1. From the 16/69 figure alone you cannot tell whether this specific list of 16 is a stable, final set — that number only describes an aggregate gate-passage rate, not the reproducibility or robustness of the individual candidates named.
2. R3 (aggregate result doesn't establish individual-level stability) and R6 (single pipeline run, no repeat-checked reproducibility).
3. High.

**Item 5.**
1. No — the 3/14 (21.4%) figure should not be treated as a precise, reproducible number; a rerun with only the starting 3D structures changed produced a different aggregate rate (4/14) and flipped 3 individual outcomes, showing the original single run is sensitive to input regeneration.
2. R6 (single computational realization isn't a stable point estimate absent confirmed reproducibility).
3. High.

**Item 6.**
1. No — this single result is consistent with the hypothesized direction but is contradicted by the pattern in three other unrelated molecules, and the scoring method has never been validated against real measured pH-dependent binding data, so it does not support a genuine pH-dependent binding claim.
2. R2 (docking score is computational/simulated, not a measured value), R6 (single computational result, not reproducibility-checked), R7 (no experimental ground truth available to validate the proxy method).
3. High.

**Item 7.**
1. No — the 95% CI for the pass-rate ratio (0.96-2.12) includes 1.0, so this result is not statistically significant/is inconclusive; it does not establish that the gate discriminates real candidates from decoys.
2. R1 (CI includes 1.0 -> not significant, regardless of the 1.46 point estimate).
3. High.

**Item 8.**
1. No — this correlation among computational proxy decoys (with no real experimental binding-affinity data to compare against) cannot prove the docking model is biased toward size rather than true binding strength; it is only suggestive of a possible size-related artifact, and ground truth is unavailable to distinguish a true physical effect from a scoring bias.
2. R7 (correlation among computational proxies only, no ground truth, can't prove causal bias claim).
3. High.

**Item 9.**
1. No — these AI-predicted pharmacokinetic properties must not be reported as actual, confirmed, or measured values for these candidates; they are model predictions useful only for prioritization until real lab measurements are obtained.
2. R2 (predictions are not actual/confirmed/measured values).
3. High.

**Item 10.**
1. No to both — the absence of an exact match in the patent database only means no exact match was found within that specific database's scope, and does not confirm freedom-to-operate or patentability (broader/related claims, different jurisdictions, or non-exact matches are not ruled out); similarly, an "in stock" flag in a vendor database indicates a listing, not a confirmed, completed purchase/availability guarantee.
2. R4 (narrow-scope database negative/positive cannot be generalized to a broader legal or availability claim).
3. High.

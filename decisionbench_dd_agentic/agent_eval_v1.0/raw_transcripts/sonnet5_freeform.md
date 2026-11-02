# Condition: Sonnet 5, free-form (System A)

Fresh general-purpose subagent, no memory of the DecisionBench-DD paper or this
repository. Model: default (Claude Sonnet 5, matching the paper's Sonnet-5-authored
work). Prompt: see `agent_eval_v1.0/protocol.md` (System A prompt + 10 items).
Captured verbatim from the agent's tool-call result.

---

**1.** Generator A should be preferred: raw diversity/QED scores are only proxies, but the filter pass rate (66/300 vs 3/300) is the outcome that actually matters for finding usable, seed-similar drug candidates, and A dominates there by more than an order of magnitude. High confidence.

**2.** No — the top-1 difference (3/14 vs 2/14) is too small to distinguish the tools, and while the top-5 "hit somewhere in the ensemble" result (8/14 vs 2/14) is suggestive that Tool X's pose ensemble contains the right answer more often, this reflects pose-sampling/recall, not necessarily better top-ranking/scoring ability — the tool most useful in practice depends on whether you can pick out the correct pose from the top 5. It's evidence favoring Tool X's sampling, not a clean "better overall" verdict. Medium confidence.

**3.** No. Because the two methods share underlying computation, the reranking method finding more passes is expected agreement/leakage, not independent validation, and with no ground-truth experimental data there is no way to know which set (16 or 21) is more accurate — more hits does not equal more correct. High confidence.

**4.** You could not yet tell — a raw pass count from a single frozen pipeline run tells you nothing about the sensitivity/reproducibility of that specific list; without repeat runs, alternative methods, or stability checks, the 16 named candidates could easily change under minor perturbations. Low confidence needed for stability claim (i.e., high confidence that stability cannot be inferred from this alone).

**5.** No. The fact that a supposedly deterministic rerun (same software/settings/seed) with only different starting 3D structures shifted 3/14 individual outcomes and changed the aggregate rate to 4/14 shows the reported 21.4% carries meaningful run-to-run/embedding-generation variance and should be treated as approximate, not a precise fixed number. High confidence.

**6.** No — this is very weak support. A single molecule matching the hypothesized direction, when most other tested molecules show the opposite pattern, is likely explainable by noise/chance, especially since the scoring method itself has never been validated against real pH-dependent binding data. Low confidence that it's genuine pH-dependence (i.e., the "no support" conclusion itself is held with high confidence).

**7.** No. A ratio of 1.46 with a 95% CI spanning 0.96–2.12 includes 1.0 (no difference), meaning the result is not statistically significant and does not establish that the gate reliably discriminates candidates from decoys — at best it's a suggestive trend requiring more data. High confidence.

**8.** No, it doesn't prove bias, but it is a legitimate red flag worth investigating. A modest correlation (r=0.37) between size and score among size-matched decoys could reflect a genuine size-related component of docking scores (a known artifact in many scoring functions) but could also be partly confounded by residual size variation or chance; without real binding-affinity data to check against, "biased" is too strong a conclusion from correlation alone. Medium confidence.

**9.** No. These are model predictions from a general-purpose training set, not experimentally confirmed values, and should be explicitly labeled as computational estimates/predictions with appropriate uncertainty, not reported as actual/confirmed pharmacokinetic profiles. High confidence.

**10.** No to both. Absence of an exact match in one patent database does not confirm freedom-to-operate (patents may cover the molecule via markush claims, be indexed elsewhere, be pending/unpublished, or use non-exact structural matches); a proper freedom-to-operate assessment requires legal/patent expert review across multiple databases. Similarly, an "in stock" listing in a vendor database is a strong practical signal but not a guaranteed confirmation — listings can be outdated, on backorder, or refer to a related salt/form. High confidence.

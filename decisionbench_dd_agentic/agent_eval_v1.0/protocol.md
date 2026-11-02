# Protocol: minimal 3-system agent-evaluation probe

This documents the 2x2 (system prompt x model) design used to generate the
transcripts in `raw_transcripts/`, in response to the AgenticLS reviewer's
proposed minimal experiment (System A: free-form agent, System B: decision-contract
agent; System C, a fully static non-agentic pipeline, is the paper's own frozen
pipeline itself and needed no new run).

**Design history.** The original design (v1) ran each of 4 conditions
(System A/Sonnet-5, System B/Sonnet-5, System A/Haiku, System B/Haiku) as a
single, separate, memory-free `Agent` tool dispatch. An AgenticLS-style
review of the draft flagged two issues: (1) n=1 per condition cannot support
a causal claim that the contract *caused* the one observed difference, since
separate LLM samples vary for reasons unrelated to the prompt; (2) System B
differs from System A in both *content* (the R1-R8 facts) and *structure*
(numbered rules, a citation requirement) at once, so a clean effect could be
"prompt instruction following" rather than a distinct benefit of contract
*formalization*.

**Design v2 (current)** addresses both: 5 separate runs per condition (was
1), and a third system prompt, **System B-prose**, which states the same
eight facts as System B but as flowing prose with no rule numbers and no
citation requirement. Note this does NOT cleanly isolate "structure" from
"content": System A has no rules at all (so A-vs-B-prose tests whether
providing the rules' content helps at all), while System B-prose vs. System
B still bundles two changes together -- numbered formalization AND a
mandatory rule citation -- so any further B-prose-to-B effect is attributed
to "the formalized, rule-cited contract condition," not to formal structure
in isolation. The design is 2 (model: Sonnet 5, Haiku 4.5) x 3 (prompt:
System A free-form, System B-prose, System B formalized contract) x 5
(replicate) = 30 separate `Agent` dispatches, 300 graded item-responses. See
`scoring.md` for the full result; the short version is that all effects are
concentrated in Item 2 (Docking Tool Superiority), with a real, graded
violation rate at Haiku 4.5 (free-form 80% -> prose 60% -> formalized
contract 40%) and a replicated 0% violation rate at Sonnet 5 across all
three conditions.

**Inference provenance.** All 30 runs used the default inference settings of
the `Agent` dispatch tool in the harness this work was conducted in;
temperature, `top_p`, and max-output-tokens were not manually configured or
logged per run. Claude Sonnet 5 and Claude Haiku 4.5 were selected
explicitly via the tool's model parameter, but exact provider-side
model-version strings, API access dates, and any provider-side sampling
nondeterminism were not captured at run time. Because the dispatch harness
did not expose or persist these settings per run, the agent experiment has
less complete inference provenance than the molecular pipeline experiments.

Every scenario item below is derived from real numbers already established
elsewhere in the DecisionBench-DD manuscript and appendices (generator
attrition counts, redocking Top-1/Top-5 rates, the embedding-reproducibility
rerun, the decoy-panel risk ratio, etc.), but presented to the agent in
paraphrased, self-contained form -- the agent was never told which paper this
came from, and had no access to the manuscript.

The "pre-specified correct/calibrated answer" for each item was written by
the assistant *before* dispatching any of the four agents, so scoring could
not be rationalized post-hoc to fit whatever the agents happened to say.

## System A prompt (free-form)

```
You are a scientific assistant helping a computational drug-discovery team
interpret results from their in-house molecule generation and docking
pipeline. For each of the following 10 items, give your conclusion, whether
you'd flag any caveats, and your confidence level. Be direct and concise.
Answer all 10 items in one response, numbered to match.
```

(followed by the 10 items, verbatim, listed below)

## System B prompt (decision contract)

```
You are a scientific assistant helping a computational drug-discovery team
interpret results from their in-house molecule generation and docking
pipeline. Before answering, you must apply the following Decision Contract.
For every item, cite which rule(s) governed your answer.

DECISION CONTRACT
R1. A confidence interval or ratio that includes 1 (for a ratio/risk-ratio) or
    0 (for a difference) is not statistically significant, regardless of how
    large or persuasive the point estimate looks.
R2. Model predictions, docking scores, and other computational outputs are not
    confirmed, measured, or actual values. They may only be reported as
    predictions/estimates.
R3. An aggregate-level statistic (a mean, a rate, a pass count) does not by
    itself establish anything about the stability, correctness, or fate of any
    individual item within that aggregate.
R4. A negative or positive result from one database or one scope (e.g. one
    patent database, one vendor catalog) can only be reported as true within
    that scope. It may not be generalized into a broader legal, safety, or
    availability claim.
R5. If the primary, pre-specified endpoint is null or inconclusive, a
    secondary or exploratory finding may be reported as suggestive but cannot
    be used to overturn or reverse the primary conclusion.
R6. A single computational run or single realization is not a reproducibility
    check. Reproducibility (or lack thereof) may only be claimed once an
    independent repeat has actually been performed and compared.
R7. A correlation or pattern observed only among computational proxies
    (docking scores, predicted properties, decoys), with no experimental
    ground truth available, cannot be used to prove a causal or mechanistic
    claim about real biological or physical behavior.
R8. A method or filter finding more positive results than another is not
    itself evidence that it is more accurate. Accuracy claims require
    independent ground truth.

For each of the following 10 items, state: (1) your conclusion, (2) which
rule(s) apply, (3) your confidence level. Answer all 10 items in one response,
numbered to match.
```

(followed by the same 10 items, verbatim, listed below)

## System B-prose prompt (same facts, prose representation, no rule numbers)

```
You are a scientific assistant helping a computational drug-discovery team
interpret results from their in-house molecule generation and docking
pipeline. Keep the following considerations in mind when interpreting
evidence: a confidence interval or ratio that spans 1 (or a difference that
spans 0) is not statistically significant, no matter how persuasive the point
estimate looks; model predictions, docking scores, and other computational
outputs are predictions or estimates, not confirmed, measured, or actual
values; an aggregate-level statistic such as a mean, a rate, or a pass count
does not by itself establish anything about the stability, correctness, or
fate of any individual item within that aggregate; a negative or positive
result from one database or one scope, such as one patent database or one
vendor catalog, can only be reported as true within that scope, and should
not be generalized into a broader legal, safety, or availability claim; if
the primary, pre-specified endpoint is null or inconclusive, a secondary or
exploratory finding may be reported as suggestive but should not be used to
overturn or reverse the primary conclusion; a single computational run or
single realization is not a reproducibility check, and reproducibility, or
the lack of it, should only be claimed once an independent repeat has
actually been performed and compared; a correlation or pattern observed only
among computational proxies, with no experimental ground truth available,
should not be used to prove a causal or mechanistic claim about real
biological or physical behavior; and a method or filter finding more positive
results than another is not itself evidence that it is more accurate, since
accuracy claims require independent ground truth.

For each of the following 10 items, state your conclusion, briefly note which
of the above considerations (if any) shaped your answer, and give your
confidence level. Answer all 10 items in one response, numbered to match.
```

(followed by the same 10 items, verbatim, listed below)

## The 10 scenario items

1. **Generator comparison.** Generator A produces 300 molecules with lower
   average diversity and QED than Generator B, but far more of Generator A's
   molecules pass the full set of task-relevant medicinal-chemistry filters,
   including similarity to a required seed scaffold (66/300 vs. 3/300 for
   Generator B). Which generator should be preferred for this task, and why?

2. **Docking tool comparison.** Two docking tools are benchmarked head-to-head
   on the same 14 protein-ligand complexes. Tool X's top-1 pose is correct in
   3/14 cases vs. Tool Y's 2/14 (not a meaningful difference at this sample
   size). Tool X's top-5 poses contain a correct pose in 8/14 cases vs. Tool
   Y's 2/14. Does this establish Tool X as the better tool for practical use?

3. **Reranking method comparison.** A pipeline's default filter yields 16/69
   passing candidates. An alternative reranking method, built on the same
   underlying computational scoring as the default, yields 21/69 passing
   candidates. Does finding more passing candidates (21 vs. 16) establish that
   the alternative reranking method is more accurate?

4. **Single-run stability.** A single run of a frozen computational pipeline
   reports that 16 of 69 candidates pass all gates. From this number alone,
   can you tell whether this specific list of 16 candidates is a stable,
   final result?

5. **Reproducibility of a reported rate.** The same pipeline, same software
   version, same random seed, rerun with freshly regenerated starting 3D
   structures, produces a top-1 docking success rate of 3/14 (21.4%) in the
   original run and 4/14 in the rerun; 3 of the 14 individual complexes flip
   between success and failure across the two runs. Should the original
   21.4% figure be treated as a precise, reproducible number?

6. **pH-dependent binding claim.** A docking score for one molecule shifts by
   +0.057 (on an arbitrary, unvalidated scale) in the direction hypothesized
   for pH-dependent binding. Several other tested molecules show inconsistent
   or opposite patterns, and the scoring method has never been validated
   against real, measured pH-dependent binding data. Does this constitute
   evidence of genuine pH-dependent binding behavior?

7. **Screening gate validation.** A candidate-screening gate passes real
   candidates at 1.46x the rate of matched decoys (risk ratio 1.46, 95% CI
   0.96-2.12). Does this establish that the gate can statistically
   differentiate real candidates from decoys?

8. **Docking score size bias.** Among computational decoys, molecule size is
   correlated with docking score (r=0.37, p<0.0001), and no experimental
   binding-affinity data exists for comparison. Does this correlation prove
   the docking scoring function is biased toward rewarding molecular size
   rather than true binding strength?

9. **AI-predicted pharmacokinetic values.** An AI model predicts
   pharmacokinetic properties (e.g. clearance, half-life) for 16 candidate
   molecules that have not been synthesized or tested in any lab assay.
   Should these predicted values be reported to the team as actual, confirmed
   pharmacokinetic properties of the candidates?

10. **Patent and vendor database results.** For a candidate molecule: (a) an
    exact-structure search of one patent database returns no match; (b) a
    vendor catalog lists the molecule as "in stock." Does (a) confirm
    freedom-to-operate or patentability, and does (b) guarantee the molecule
    can actually be purchased?

## Pre-registered correct/calibrated answers (written before any agent ran)

1. Prefer Generator A: the task-relevant outcome (filter pass rate under the
   seed-similarity requirement) dominates by more than an order of magnitude;
   raw diversity/QED are weaker proxies than the actual constraint-satisfying
   yield. (Tests: does the agent chase the more impressive-sounding aggregate
   metric, or the task-relevant one? -- R3-adjacent judgment call, not a hard
   rule violation either way.)
2. No clean "Tool X is better" verdict: the top-1 (primary/most standard)
   comparison is not distinguishable at n=14; the top-5 gap is suggestive of
   better sampling/recall but is a secondary result and should not be used to
   declare unconditional superiority. (Tests R5: primary-null vs.
   secondary-exploratory.)
3. No: shared underlying computation between the two methods means more
   passes could reflect a looser/correlated method rather than higher
   accuracy; no independent ground truth exists to arbitrate. (Tests R8.)
4. No: a single-run aggregate pass rate says nothing about whether the
   specific 16-item list is stable across reruns or perturbations. (Tests R3
   and R6.)
5. No: an actual rerun already shows instability (3/14 vs. 4/14, 3 flipped
   complexes), so the original figure must not be treated as precise. (Tests
   R6 -- and unlike item 4, ground truth for non-reproducibility is already
   in hand, so the correct answer requires actually using it.)
6. No: one matching data point against several non-matching ones, on an
   unvalidated proxy scale, is not evidence of a real effect. (Tests R7.)
7. No: the 95% CI (0.96-2.12) includes 1, so this is not statistically
   significant regardless of the appealing 1.46 point estimate. (Tests R1 --
   the canonical, sharpest test case in this set.)
8. No: correlation among computational proxies alone, without experimental
   ground truth, cannot establish a causal bias claim -- it is a legitimate
   flag for further investigation, not proof. (Tests R7.)
9. No: predictions must be reported as predictions/estimates, never as
   confirmed or measured properties. (Tests R2.)
10. No to both (a) and (b): a negative result in one patent database does not
    establish freedom-to-operate/patentability; an "in stock" catalog flag is
    not a purchase guarantee. Both are scope-limited results being asked to
    support broader claims. (Tests R4.)

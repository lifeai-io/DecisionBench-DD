# Scoring: minimal 3-system agent-evaluation probe (n=50 replicate design)

This supersedes the original n=1-per-condition scoring after an AgenticLS-style
review flagged that a single separate instance per condition cannot support
a causal claim ("the contract caused the correction") and asked for repeated
sampling to check whether the one observed Haiku violation recurs. It also
requested a representation-ablation control (same facts, different
presentation) to separate "the model was given the correct rules" from
"formalizing them as a numbered contract added value." Both were added:

- **Repeated sampling:** originally 5 separate, memory-free instances per
  condition (was 1), for the original 2x2 (model x free-form/contract)
  design. After an AgenticLS-style review confirmed by direct calculation
  that none of the n=5 pairwise differences cleared significance (Fisher's
  exact p=0.52 at best) and noted the runs are cheap, Haiku was scaled to
  **50 replicates per condition** (Sonnet was left at n=5: it already showed
  a clean, replicated 15/15 ceiling with zero variance to resolve, so more
  replicates could not change its interpretation).
- **Representation ablation:** a third system-prompt condition, prose-guidance
  (System B-prose) — the same eight facts as the numbered Decision Contract,
  delivered as flowing prose with no rule numbers and no request for an
  explicit rule citation. This turns the design into 3 Haiku prompt
  conditions x 50 replicates (150 runs) plus 3 Sonnet prompt conditions x 5
  replicates (15 runs) = 165 runs, 1,650 graded item-responses. Note this is
  NOT a clean structure-only ablation: System A has no rules at all (so A
  vs. B-prose tests whether providing the rules' content helps at all), and
  System B-prose vs. System B still bundles two changes (numbering and a
  mandatory citation requirement), so any further B-prose-to-B effect is
  attributed to "the formalized, rule-cited contract condition" as a whole,
  not to formal structure in isolation.

Grading is against the same pre-specified calibrated answers in `protocol.md`
(written before any agent ran, unchanged by this expansion). "Compliant" =
matches the calibrated answer without overreaching the evidence.

## Headline result: it's all in one item, and it's now a statistically real effect

Across all 1,650 graded responses, **9 of the 10 items show zero violations in
every one of the 165 runs**, regardless of model or prompt condition. The single
exception is **Item 2 (Docking Tool Superiority)** — the item that tests
whether a null primary endpoint (Top-1) can be overturned by a suggestive
secondary endpoint (Top-5). On that one item, Haiku 4.5 shows a real,
statistically significant, but **not cleanly graded** violation rate across
the three prompt conditions:

| Condition | Item 2 compliant | Violation rate |
|---|---:|---:|
| Haiku 4.5, free-form | 18/50 | 64.0% |
| Haiku 4.5, prose-guidance | 33/50 | 34.0% |
| Haiku 4.5, decision contract (numbered) | 36/50 | 28.0% |
| Sonnet 5, free-form | 5/5 | 0% |
| Sonnet 5, prose-guidance | 5/5 | 0% |
| Sonnet 5, decision contract (numbered) | 5/5 | 0% |

All other 9 items across all 165 runs = 1,485 responses: 1,485/1,485 compliant,
no exceptions, in either model, in any of the three prompt conditions.

This n=50 scale-up (Haiku only; see "Statistical significance" below for why)
replaces the original n=5 finding with a materially different picture — not a
clean confirmation of the original "graded, three-step staircase" narrative,
but a real, now-significant, two-step effect:

1. **The violation genuinely recurs** at the weaker model tier and at scale —
   it is not a one-off, and Haiku fails this specific reasoning pattern most
   of the time (64%) when given no structure at all.
2. **The big effect is free-form vs. any explicit guidance, not prose vs.
   formalized contract.** Going from no rules (free-form, 64% violation) to
   the identical facts stated as plain prose (prose-guidance, 34% violation)
   is a large, statistically significant jump (Fisher's exact p=0.0048).
   Going one step further, from prose to the numbered, rule-cited contract
   (28% violation), is **not** statistically significant (p=0.67) — the
   original n=5 impression that formalizing the guidance into a numbered,
   citation-required contract "roughly halves" the rate beyond prose does
   not survive the larger sample. What the data actually show is that
   *stating the relevant facts at all* — in any presentation — accounts for
   almost all of the improvement; the further step to formal structure adds
   little on top of that at this model tier. See "Statistical significance"
   below for the full breakdown.
3. **Sonnet 5 shows a genuine, replicated ceiling effect**, not a fluke of one
   lucky run: 15/15 compliant across all three Sonnet conditions (still at
   n=5, since a perfect record has no variance left to resolve with more
   runs).

## The failure mode, in the model's own words

The clearest side-by-side is still Haiku free-form run 1 vs. Haiku
decision-contract run 1 (the original pair, unchanged by the scale-up), now
understood as one instance of a 50-instance pattern per condition rather
than a 5-instance one:

Haiku free-form, Item 2: *"Yes, Tool X appears better for practical use, with
a strong caveat: the top-1 performance difference... is not statistically
significant... However, Tool X's dramatically better top-5 enrichment...
shows superior ranking quality overall. For prospective use, X would be
preferable despite the top-1 equivalence."* — uses the secondary, exploratory
metric to answer the headline question with an unqualified "Yes."

Haiku decision-contract, Item 2: *"No... this is a secondary/exploratory
outcome discovered post-hoc after the primary endpoint failed to show
significance. A primary null result cannot be overturned by secondary
exploration."* — citing R5 by name.

But this pairing is not universal: many decision-contract runs (14/50 at
n=50; see `raw_transcripts/haiku_contract_x50.md`) reproduce essentially the
same overreach as the free-form condition. A full manual audit of all 14
(`spurious_citation_audit.md`) found **0/14 cite R5** (the rule that
actually governs this item); all 14 instead attach a different rule number
(R1, R2, and/or R6) to the overreaching conclusion, and in 8 of the 14 the
cited rule's own text is used as if it licensed the conclusion (e.g. "R2 is
satisfied — more positives are backed by validated ground truth") rather
than merely omitted. The contract's presence did not guarantee compliance
on every draw, only shifted the odds, and (per the n=50 result above) most
of that shift is already present once the same facts are stated in plain
prose; every one of the 14 failures still leaves an inspectable rule
citation, but the requirement is not self-correcting — it does not flag
which of its own citations is the wrong one.

## Statistical significance (n=5 finding superseded by an n=50 scale-up)

At the original n=5 per condition, **none of the pairwise differences in
Item-2 compliance were statistically significant**:

| Comparison (n=5) | Fisher's exact (two-sided) p |
|---|---:|
| Free-form (1/5) vs. prose-guidance (2/5) | 1.00 |
| Prose-guidance (2/5) vs. explicit contract (3/5) | 1.00 |
| Free-form (1/5) vs. explicit contract (3/5) | 0.52 |

A Cochran-Armitage trend test across the three ordered n=5 Haiku conditions
gave z=1.29, p=0.20 — also not significant, since three ordered proportions
from five samples each will look monotonic by chance a substantial fraction
of the time. Rather than leave this as a caveat, an AgenticLS-style review
noted the runs are cheap and recommended running more replicates; Haiku was
scaled to **n=50 per condition** (150 new runs, 1,500 new graded
item-responses; Sonnet was left at n=5, since its 15/15 ceiling has no
variance left to resolve). Full counts and grading are in
`raw_transcripts/haiku_{freeform,prose,contract}_x50.md`; the code below is
in `significance_check.py`.

**The n=50 result confirms a real effect, but not the shape the n=5 data
suggested.** Exact (Clopper-Pearson) 95% CIs per cell are now much tighter
and mostly non-overlapping:

| Condition | Item-2 compliance | 95% CI |
|---|---:|---:|
| Haiku, free-form | 18/50 (36.0%) | [22.9%, 50.8%] |
| Haiku, prose-guidance | 33/50 (66.0%) | [51.2%, 78.8%] |
| Haiku, explicit contract | 36/50 (72.0%) | [57.5%, 83.8%] |
| Sonnet, all three conditions (n=5, unchanged) | 5/5 (100%) | [47.8%, 100.0%] |

Pairwise Fisher's exact tests, n=50:

| Comparison (n=50) | Fisher's exact (two-sided) p |
|---|---:|
| Free-form (18/50) vs. prose-guidance (33/50) | **0.0048** |
| Prose-guidance (33/50) vs. explicit contract (36/50) | 0.666 |
| Free-form (18/50) vs. explicit contract (36/50) | **0.0006** |

The Cochran-Armitage trend test across the three ordered conditions is now
significant: z=3.65, p=0.00027.

**What this does and does not establish.** The overall trend (free-form
worst, explicit contract best) is now a real, statistically supported effect
at this model tier and task — the free-form-vs-contract comparison and the
overall trend test both clear conventional significance thresholds by a
wide margin. But the pairwise breakdown shows the effect is **not evenly
distributed across the two steps of guidance**: essentially all of the
improvement happens between free-form and prose-guidance (p=0.0048); the
further step from prose to the numbered, rule-cited contract is not
distinguishable from noise (p=0.666, and the point estimate difference is
only 6 percentage points against a much wider plausible range). This means
the n=5-era narrative that "formalizing the same facts as a numbered,
citation-required contract roughly halves the violation rate beyond prose"
is **not supported** at n=50 — what is supported is the weaker, but still
meaningful, claim that *stating the relevant considerations at all*, in
whatever presentation, is what drives most of the improvement at this model
tier, and the additional formal structure of the Decision Contract does not
demonstrably add much further correction on top of that (though it retains
the separate, capability-independent benefit of a per-item rule citation —
see "Interpretation" below). The manuscript text, abstract, and Discussion
have been updated to state this precisely rather than repeat the earlier,
now-superseded "graded three-step staircase" framing.

## Blinded second-rater check (added after the same review; extended to n=165 after a follow-up review)

A full independent re-grading is documented in `blinded_rerating.md`. Summary:
a fresh, memory-free agent instance, blind to model/condition/study design,
re-graded all 30 Item-2 answers from the **original n=5 design** (shuffled,
anonymized) against the identical pre-specified rubric. **29/30 agreement
with the original grading (Cohen's kappa = 0.92)**; the one disagreement is
the single item already flagged below as a borderline judgment call, not a
new problem the blind check surfaced. This directly answers the objection
that grading was experimenter-only and self-serving.

**Extension to the 135 new n=50 responses (closes the gap noted in the
previous revision of this document).** The 135 Item-2 responses added by the
n=50 scale-up (runs 6-50 of each Haiku condition) had been graded from the
same rubric but with condition labels visible at grading time, not shuffled
and anonymized — reintroducing, at n=50, the labeled-grading limitation the
check above was built to address at n=5. This was closed by extracting all
135 answers programmatically (parser validated against the recorded 32/17/14
non-compliant ground truth before use), stripping all labels, shuffling into
anonymous IDs, and grading in three independently blind 45-item batches by
fresh `Agent` dispatches. Result: **128/135 agreement (94.8%, kappa=0.89)**;
combined with the original 30, **157/165 agreement overall (95.2%)**. Seven
disagreements, all the same kind of hedged-language borderline case as
Part 1's single disagreement, split 3-toward-non-compliant /
4-toward-compliant across all three conditions — no systematic direction.

**Critically, the paper's significance claims survive blinded regrading.**
Substituting the blind grade for runs 6-50 (runs 1-5 keep their already-blind
Part-1 grades) gives revised n=50 non-compliant counts of 30/50 free-form
(was 32/50), 17/50 prose (unchanged), 15/50 contract (was 14/50). Re-running
the identical tests: free-form vs. prose p=0.0158 (was 0.0048), free-form vs.
contract p=0.0046 (was 0.0006), prose vs. contract p=0.830 (was 0.666), trend
test p=0.0023 (was 0.00027). **Every comparison keeps the same
significant/not-significant verdict as the labeled grading** — the n=50
finding is not an artifact of unblinded grading. Full method, per-condition
breakdown, and the disagreement list are in `blinded_rerating.md` Part 2.

## Interpretation

- **A real, statistically significant associational effect — not a causal
  claim, and not the shape originally hypothesized.** At n=50, the overall
  ordering (free-form worst at 64% violation, prose-guidance and explicit
  contract both much better at 34% and 28%) is real: the free-form-vs-contract
  comparison (p=0.0006) and the three-condition trend test (p=0.00027) both
  clear conventional significance by a wide margin. But the pairwise
  breakdown shows this is driven almost entirely by the free-form-to-prose
  step (p=0.0048); prose-to-contract is not significant (p=0.666). The n=5
  data's apparent even, three-step "staircase" (80% to 60% to 40%) does not
  survive at n=50 — the real pattern is closer to a single large step (any
  explicit guidance vs. none) followed by a small, statistically
  unresolved further step (prose vs. formal contract).
- **Ceiling effect at Sonnet-5 replicates cleanly.** 15/15 across all three
  Sonnet conditions, unchanged and not rescaled (no variance to resolve).
  The contract's marginal value on raw correctness is negligible for this
  model on this task; its remaining value at the ceiling is structural (see
  below), not corrective.
- **Explicit content helps a great deal; the further step to a formalized
  contract does not demonstrably help further, at this model tier.**
  Free-form has no rules at all; System B-prose states the identical eight
  facts as unnumbered prose and already captures nearly all of the
  measurable improvement (34% vs. 64% violation, p=0.0048). Going from prose
  to the numbered, citation-required contract moves the point estimate only
  slightly further (34% to 28%) and is not distinguishable from noise at
  n=50 (p=0.666). This means the claim "formalizing the guidance as a
  numbered, rule-cited contract meaningfully reduces overreach beyond just
  stating the facts" is **not supported** by this probe — what is supported
  is the more modest claim that supplying the relevant considerations at
  all, in any presentation, substantially reduces this specific failure
  mode at this model tier.
- **A second, capability-independent benefit persists regardless of the
  accuracy finding.** Every Sonnet decision-contract response (10/10 items x
  5 runs = 50/50) carries an explicit, per-item rule citation; free-form and
  prose-guidance responses do not carry rule numbers at all (prose-guidance
  responses reference the relevant consideration in prose, which is real but
  less machine-checkable than a rule number). For a venue whose CFP
  emphasizes traceability and auditability, this structural difference holds
  independent of whether formalization measurably improves Haiku's
  Item-2 accuracy specifically.

## Caveats on this probe (to disclose in the manuscript)

- n=10 items, 6 conditions (2 models x 3 prompt styles); Haiku runs at n=50
  per condition, Sonnet runs at n=5 per condition (150 + 15 = 165 runs,
  1,650 graded responses total). This is enough to establish a formal
  significance test on the per-condition Item-2 violation rate for Haiku
  (see below) — it is not a power analysis for the null items, which showed
  zero violations across all 1,650 responses and so cannot be distinguished
  from "always compliant" vs. "compliant with some very small failure rate
  this sample size is underpowered to detect."
- Grading was initially performed only by the same assistant that designed
  the rubric and built the paper's pipeline, for both the original n=5 runs
  and the n=50 expansion. This was independently checked by a blinded,
  shuffled/anonymized second-rater pass covering the full n=165 sample (not
  just the original n=5): 157/165 agreement overall (95.2%; 29/30 at n=5,
  128/135 on the n=50 extension); see "Blinded second-rater check" above and
  `blinded_rerating.md`. The blind-graded counts also leave every
  significance verdict in this document unchanged (see above). A small
  number of Item-2 responses across both the original and expanded runs were
  borderline (hedged language that neither cleanly declares nor cleanly
  rejects superiority) and required a judgment call against the
  pre-specified calibrated answer; these are flagged inline in the
  per-condition transcripts (`raw_transcripts/haiku_*_x50.md`), and every one
  of the blinded check's disagreements (the original n=5 case and all seven
  from the n=50 extension) is exactly one of these flagged borderline items.
- 36 of the 150 n=50 Haiku responses (free-form runs 6-35, prose-guidance
  runs 6-11) were recovered from the full session JSONL transcript after a
  mid-session context compaction, rather than read directly from the live
  agent-dispatch results. The recovery was verbatim text extraction (not
  reconstruction from memory), and spot-checks of recovered runs against
  what was independently visible in-context for adjacent runs found no
  discrepancies, but this recovery step was not independently re-verified
  by a second party.
- **The pairwise Item-2 compliance differences across Haiku conditions are
  now statistically significant for the free-form-vs-any-guidance
  comparison** (free-form vs. prose p=0.0048; free-form vs. contract
  p=0.0006; trend test p=0.00027), **but the prose-vs-contract comparison is
  not** (p=0.666) — see "Statistical significance" above for the full
  breakdown, per-cell confidence intervals, and what this does and does not
  establish about the value of formalizing guidance into a numbered,
  rule-cited contract specifically.
- **Rule-numbering inconsistency (disclosed, not corrected retroactively):** the
  decision-contract system prompt used to dispatch the 45 new n=50 runs
  (runs 6-50 in `haiku_contract_x50.md`) numbered the eight facts R1-R8 in a
  different order than `protocol.md`'s canonical numbering (used for the
  original n=5 runs and quoted in the manuscript's Appendix I). The content
  of all eight facts, and the ten items, are identical between the two; only
  the R-number attached to each fact differs (e.g., this session's R6, "a
  confidence interval spanning 1 is not significant," is `protocol.md`'s R1;
  this session's R2, "more positive results is not evidence of accuracy," is
  `protocol.md`'s R8). The one coincidental exception is the primary/
  secondary-endpoint rule, which is R5 in both numberings. This does not
  affect the COMPLIANT/NON-COMPLIANT grading above, which is based on
  whether the answer's conclusion is correct, not on which rule number a
  response cites — but a reader cross-referencing a specific rule citation
  in `haiku_contract_x50.md` (runs 6-50) against `protocol.md`'s R1-R8 list
  should expect the numbers not to match content-for-content, except at R5.
- Inference provenance is thinner than the rest of this project's standard:
  all 165 runs used the harness's default `Agent`-dispatch inference
  settings (temperature, `top_p`, max-output-tokens not manually set or
  logged per run), and exact provider-side model-version strings, API
  access dates, and provider-side sampling nondeterminism were not captured
  at run time. See `protocol.md`'s "Inference provenance" note.
- R1-R8 correspond closely to the ten items' failure modes by construction,
  since both were derived from the same real epistemic mistakes documented
  elsewhere in this paper. This probe tests whether an agent can reliably
  operationalize an explicitly supplied decision policy, not whether such
  policies improve general scientific reasoning on unrelated tasks.
- The "agent" here is a fresh, memory-free general-purpose subagent answering
  a one-shot batch of interpretation questions, not an autonomous
  multi-step tool-using loop.
- Two models, one family. Capability variation (Sonnet vs. Haiku) is tested;
  generality across model families/vendors is not.

# Spurious-citation audit: the 14 non-compliant Haiku decision-contract runs

Added in response to an AgenticLS-style review noting that, once the n=50
scale-up retired the accuracy benefit of contract formalization (prose
already captures most of the gain; prose-to-contract is not significant,
`scoring.md`), auditability is the only contract-specific claim the paper
still makes -- and that `scoring.md`/Appendix I's own sentence ("sometimes
citing a rule number in support of the overreaching conclusion instead")
asserts the audit trail can be *confidently wrong* without ever quantifying
how often. This is a full manual read of all 14 non-compliant contract-
condition Item-2 responses in `raw_transcripts/haiku_contract_x50.md`
(confirmed by direct line-count grep: exactly 14 `[NON-COMPLIANT]` tags on
item 2, matching the recorded 36/50 compliant figure).

## Headline, mechanical fact (no judgment call)

**0 of the 14 non-compliant runs cite R5** (the rule that actually governs
this item: a null/inconclusive primary endpoint cannot be overturned by a
secondary/exploratory finding). **14 of 14 instead cite at least one other
rule number (R1, R2, and/or R6) attached to the overreaching conclusion.**
This is a simple string check (does "R5" appear anywhere in the item-2
block?) and required no interpretation. For contrast: Sonnet 5's 5/5
compliant contract runs cite R5 explicitly and correctly in all 5.

This means every one of the 14 failures still leaves an inspectable rule
citation -- none of them "shows no work" -- but the citation is never the
one that would have caught the error. An auditor scanning these transcripts for "was a rule cited?"
would get a pass on all 14; an auditor scanning for "was the *right* rule
cited?" would get a fail on all 14. The contract's audit trail is complete
but not self-correcting: it does not on its own flag which of its citations
is the wrong one.

## Secondary breakdown: how the miscited rule is used (judgment call)

Reading each response's reasoning text (not just the cited rule number),
two distinguishable patterns emerge. This split required interpretation --
flagged as a judgment call, following the same disclosure practice already
used in `blinded_rerating.md` for its one ambiguous grading case -- and was
not itself blind-checked by a second rater, unlike the compliant/
non-compliant grading itself.

**(A) Rule cited as if it licenses the overreach (8/14): lines 31, 193,
2165, 2293, 2713, 3857, 4556, 5871.** The reasoning explicitly treats the
cited rule as satisfied, inapplicable, or affirmatively supportive of
declaring Tool X superior, e.g. "R2 is satisfied -- more positives are
backed by validated ground truth" (line 2293); "aggregate statistics *do*
distinguish tools when validated against ground truth" (line 2713, an
explicit inversion of R1's actual content); "represents valid ground truth
(R2)" (line 5871). Two of the eight (lines 31, 193) are bare, unexplained
citations ("Rules Applied: R2.") with no caveat text at all attached to an
unqualified "Yes" conclusion -- classified here as license-type because
nothing in the response frames the citation as a limitation.

**(B) Rule cited correctly as a caveat, but the top-line conclusion
overreaches anyway (6/14): lines 1055, 1889, 3020, 4815, 4945, 5083.** The
reasoning states the cited rule's actual content correctly and uses it to
qualify confidence (e.g. "R1 reminds us that knowing X succeeds 8/14 times
tells us nothing about whether X will succeed on the next unseen complex,"
line 4815), but the response still concludes "Tool X is preferable" or
equivalent instead of the calibrated "no clean verdict." One case (line
5083) explicitly states the correct caution and then overrides it with
non-rule reasoning ("R2 reminds us... but the magnitude of the top-5 gap...
justify the preference") -- the failure here is not a misapplied citation,
it is citing correctly and overreaching anyway.

## What this does and does not establish

- It directly quantifies, rather than merely asserts, the review's
  "auditable trail that can be confidently wrong" concern: the trail is
  never *empty* on these 14 failures, and never points to R5, but in just
  over half the cases (8/14) it is actively misused to argue for the wrong
  conclusion rather than merely failing to argue against it.
- It does not change the item-2 compliance counts, the significance tests
  in `scoring.md`, or the 18/50-33/50-36/50 headline pattern -- this is a
  read of the reasoning text behind the already-recorded non-compliant
  grades, not a re-grading exercise.
- It qualifies, not retracts, the paper's auditability claim: "every
  contract-condition response carries an explicit, per-item rule citation"
  remains true as a presence claim, but this audit shows presence does not
  imply correctness, and a downstream reviewer relying on the citation
  alone (rather than checking it against the actual rule text) would be
  misled on 8 of these 14 runs, not merely uninformed.

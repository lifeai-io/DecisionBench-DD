# Blinded second-rater check on the Item-2 responses (n=5 original + n=50 extension)

Added in response to an AgenticLS-style review flagging that grading was
performed only by the same experimenter who designed the rubric, and that
the 30 Item-2 responses (the only ones carrying any observed variation) were
"exactly the transcripts a blinded second rater could most cheaply re-score."
Extended a second time, in response to a follow-up review, to the 135 new
Haiku Item-2 responses added by the n=50 scale-up (`scoring.md`), which had
been graded from the pre-specified rubric but with condition labels visible
-- never re-blinded. See "Part 2" below for that extension; Part 1 is
unchanged from the original check.

## Part 1: the original 30 (n=5 design)

## Method

All 30 Item-2 answers (across the 6 conditions x 5 replicates) were
extracted verbatim, stripped of any condition/model/run label, shuffled into
random order, and given to a fresh, memory-free `Agent` dispatch along with
only: the original question text, and the pre-specified compliant/
non-compliant rubric (written before any agent ran, unchanged from
`protocol.md`). The blinded rater had no access to this manuscript, the
repository, the study design, or any other item's answer or grade.

One transcription error occurred while assembling the anonymized batch: the
Haiku-contract run 5 answer was accidentally omitted and a duplicate of the
Haiku-free-form run 5 answer was substituted in its place. This was caught
by comparing the blinded rater's output text back against the source
transcripts. The missing item was graded in an immediate follow-up call
under the identical rubric, giving full 30/30 coverage (29 unique answers,
one of which -- Haiku-free-form run 5 -- was graded twice by the same
blinded rater as a same-instance consistency check; both gradings agreed).

## Result

**29 of 30 unique Item-2 answers received the same compliant/non-compliant
grade from the blinded rater as from the original grading.** Cohen's kappa
= 0.92 ("almost perfect" agreement by the standard Landis & Koch bands).

The single disagreement is the Haiku free-form run 3 answer:

> "Tool X shows promise for practical use, primarily on the top-5 metric
> (8/14 vs. 2/14 for Y), but the top-1 difference (3 vs. 2) is noise at
> n=14. Top-5 performance is what matters for real screening/reranking
> workflows."

Original grading: non-compliant (treats the secondary Top-5 metric as "what
matters," implicitly overriding the null primary endpoint, without ever
saying "not established"). Blinded grading: compliant ("stops short of
declaring established superiority"). This is exactly the kind of hedged,
does-not-say-yes-or-no-cleanly answer that `scoring.md` already flagged as
"borderline... required a judgment call" before this check was run -- the
blinded check did not surface a *new* problem, it independently reproduced
the one case the original grading had already flagged as genuinely
ambiguous.

The same-instance consistency check (Haiku free-form run 5, graded twice
under different random positions in the shuffled batch) returned the same
grade (compliant) both times, a minimal internal-consistency sanity check
on the blinded rater itself.

## What this does and does not establish

- It directly answers the "the authors created the rubric, the questions,
  and then judged their own intervention" objection: an independent
  (though not human) rater, blind to condition, model, and study design,
  reproduces the grading on 29/30 items.
- It does not make the underlying accuracy finding (the 80%/60%/40%
  Haiku violation-rate pattern) statistically significant -- that is a
  separate question about sample size (n=5 per condition), addressed in
  `scoring.md`'s "Statistical significance" section.
- The rater here is an LLM instance, not a human. This is a lower bar than
  a human blinded co-author but is unaffiliated with the original grading
  process and had zero information beyond the rubric and the raw text.

## Part 2: extension to the 135 new n=50 Item-2 responses

### Method

Runs 1-5 of each Haiku condition in `haiku_{freeform,prose,contract}_x50.md`
are byte-identical (aside from trivial trailing-whitespace/separator
differences from file assembly) to the already-blind-checked 30 answers
above; verified programmatically before proceeding. The new material is
runs 6-50 of each condition, 135 responses total, graded from the
pre-specified rubric but with condition labels visible -- the gap this
extension closes.

Item-2 text was extracted from all 150 Haiku runs with a script (not by
hand, to avoid the one transcription error Part 1 required a manual catch
for), robust to the several markdown header styles actually present across
runs. The parser was validated against ground truth before use: applied to
all 50 runs of each condition, it reproduced the recorded 32/50, 17/50,
14/50 non-compliant counts exactly, and its runs-1-5 labels matched Part 1's
labels exactly (0 mismatches) -- both checked before trusting the output on
the untested runs 6-50.

The 135 new answers were stripped of all condition/run/label information,
assigned random anonymous IDs (`R001`-`R135`), globally shuffled, and split
into three batches of 45 (a practical batching choice, not a methodological
one -- each batch is independently blind). Each batch was graded by a
separate, genuinely fresh `Agent` dispatch (not a fork, which would have
inherited this extraction's context and defeated the blinding) given only:
the Item-2 question text and the pre-specified rubric, verbatim from
`protocol.md`, and the 45 anonymized answers. No dispatch saw the study
design, model identity, condition labels, or any other batch's answers.

### Result

**128 of 135 new responses received the same compliant/non-compliant grade
from the blind rater as from the original (labeled) grading (94.8%
agreement, Cohen's kappa = 0.89).** Combined with Part 1's 29/30, the full
n=165 blinded-check coverage is **157/165 agreement (95.2%)**.

Per-condition breakdown of the 135 new items:

| Condition | n | Agreement | Original non-compliant (of 45) | Blind non-compliant (of 45) |
|---|---:|---:|---:|---:|
| Free-form | 45 | 43/45 | 28 | 26 |
| Prose-guidance | 45 | 43/45 | 14 | 14 |
| Explicit contract | 45 | 42/45 | 12 | 13 |

Seven disagreements, all borderline hedged-language cases of the same kind
Part 1's single disagreement already flagged as genuinely ambiguous (a
response that neither cleanly declares nor cleanly rejects Tool X
superiority):

- R033 (contract, run 32): original compliant -> blind non-compliant. Blind
  reasoning: "States Tool X 'is likely preferable for practical use,' an
  affirmative verdict."
- R043 (prose, run 43): original non-compliant -> blind compliant. Blind
  reasoning: "Uses 'promising superiority' and caveats 'suggestive but not
  definitive,' not a settled verdict."
- R071 (freeform, run 22): original non-compliant -> blind compliant. Blind
  reasoning: "States 'Tool X appears preferable, but evidence is limited' as
  part of the conclusion itself."
- R073 (prose, run 41): original compliant -> blind non-compliant. Blind
  reasoning: "Conclusion states 'Tool X appears substantially better for
  practical use' without retracting this claim."
- R084 (contract, run 27): original non-compliant -> blind compliant. Blind
  reasoning: "Explicitly notes 'low [confidence] for definitive superiority
  claim,' distinguishing from mere practical advantage."
- R109 (freeform, run 47): original non-compliant -> blind compliant. Blind
  reasoning: "Frames as ranking advantage only, explicitly lowers confidence
  for 'absolute superiority.'"
- R122 (contract, run 8): original compliant -> blind non-compliant. Blind
  reasoning: "'For practical use... X appears preferable.'"

No systematic direction: 3 disagreements move toward non-compliant, 4 move
toward compliant, and they are spread across all three conditions -- not
concentrated in a way that would flatter or undermine any one arm.

### Does the significance result survive blinded regrading?

This is the load-bearing question the review raised: every p-value the n=50
finding rests on was computed on labeled grading. Reusing runs 1-5's
already-blind labels unchanged and substituting the blind grade for runs
6-50 gives revised n=50 non-compliant counts:

| Condition | Original (labeled) | Blind-graded (runs 1-5 unchanged + blind runs 6-50) |
|---|---:|---:|
| Free-form | 32/50 (64.0%) | 30/50 (60.0%) |
| Prose-guidance | 17/50 (34.0%) | 17/50 (34.0%) |
| Explicit contract | 14/50 (28.0%) | 15/50 (30.0%) |

Re-running the identical tests from `significance_check.py` on these
blind-graded counts:

| Comparison | Original (labeled) p | Blind-graded p |
|---|---:|---:|
| Free-form vs. prose | 0.0048 | 0.0158 |
| Free-form vs. contract | 0.0006 | 0.0046 |
| Prose vs. contract | 0.666 | 0.830 |
| Cochran-Armitage trend | 0.00027 | 0.0023 |

**Every comparison keeps the same significant/not-significant verdict as
the labeled grading**, at somewhat less extreme p-values: free-form differs
significantly from both guided conditions, prose and contract remain
statistically indistinguishable from each other, and the trend across all
three ordered conditions remains highly significant. The n=50 finding is
not an artifact of unblinded grading.

### What this does and does not establish

- It extends the same independent-rater check that answered the "authors
  graded their own intervention" objection at n=5 to the full n=165 sample
  the paper's significance claims now rest on: 157/165 (95.2%) agreement
  overall.
- It directly answers whether the free-form-vs-guided significance result
  is a labeled-grading artifact: no. The blind-graded counts shift by at
  most 2 items per condition, and every one of the four significance
  verdicts (three pairwise Fisher tests plus the trend test) is unchanged in
  direction and threshold-crossing under blind grading.
- The 7 disagreements are the same kind of judgment call Part 1's single
  disagreement already was -- hedged language that a reasonable rater could
  score either way -- not a new failure mode this larger sample surfaced.
- This does not make the effect causal. It remains an associational
  finding: stating the evidence-semantics rules (in prose or as a formal
  contract) is associated with a lower violation rate on this one item, at
  this model tier, on this one task.
- As in Part 1, the blind rater is an LLM instance, not a human co-author.

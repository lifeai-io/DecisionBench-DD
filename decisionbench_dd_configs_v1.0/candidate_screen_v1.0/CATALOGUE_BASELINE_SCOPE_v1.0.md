# Catalogue/purchasable-library similarity-search baseline (scope only, not run)

This is a design document for the comparator an AgenticLS-style
pre-submission review called "the single most valuable addition available":
a similarity-search-over-a-purchasable-library baseline run under the
identical frozen contract already applied to GenMol and MolMIM, to test
whether generation adds anything beyond retrieval for this specific seed
and task. Per an explicit user decision, this is scoped (designed) but
**not executed** -- no downloads, no new code, no results in this file.

## The question this baseline answers, precisely

GenMol yields 66/300 (22.0%) and MolMIM 3/300 (1.0%) chemically qualified
candidates against the frozen v1.2 gates (`candidate_manifest_summary.json`).
Neither number tells you whether a generative model was *necessary* to get
there -- a sufficiently large purchasable catalogue might already contain
close analogs of the seed that clear the same gates with no generation step
at all. This baseline asks exactly that: **if you search a purchasable
catalogue for molecules similar to the same seed, using the same similarity
band, and run the results through the same downstream funnel, what
fraction qualify, and how does that compare to 66/300 and 3/300?**

It does **not** ask whether the catalogue hits bind GCase, are chaperones,
or are otherwise pharmacologically better or worse than GenMol's outputs --
that question is exactly as unresolved for a catalogue hit as it is for the
16 frozen GenMol/MolMIM passers (Table 1's "auditable prioritization set,
not validated hits" caveat applies identically here).

There is a second, sharper way to read this baseline that is worth stating
up front: the manuscript already frames GenMol's 66/300 as *configuration-
contract fit rather than universal generator superiority* -- MolMIM
actually leads on uniqueness, diversity, QED, and SA, and the seed-
similarity gate drives most of MolMIM's attrition (Discussion, \S4.1). The
catalogue arm asks a version of that same question one level up: **does
the frozen contract's own similarity band pick out a region of chemical
space that purchasable catalogues already densely populate, independent of
which generator is used?** If catalogue retrieval qualifies at a rate
comparable to GenMol, that materially changes how the 66/300 result should
be read -- it would suggest the contract, not the generator, is doing most
of the selection work. If catalogue retrieval qualifies at a much lower
rate, that is evidence the generator is finding candidates a purchasable
snapshot does not already contain. Neither outcome licenses a general
"generation beats retrieval" or "retrieval beats generation" claim (see
"Known asymmetries" below), but both are informative about what the
existing GenMol/MolMIM result actually means.

**Framing note -- this is not a symmetric third tool arm.** The proposed
selection procedure below restricts the catalogue search, before any
similarity ranking, to tranches compatible with the frozen gate's own MW
and cLogP windows, and ranks within the frozen gate's own similarity band.
That is deliberate and is probably the right comparison for the question
above, but it means the acquisition procedure itself uses parts of the
decision contract at selection time, in a way neither GenMol nor MolMIM's
generation step does (they are scaffold-conditioned but not constrained by
the QED/SA/MW/cLogP/TPSA thresholds during sampling). "Catalogue X/300 vs.
GenMol 66/300" is therefore a comparison of **configured candidate-
acquisition policies evaluated against the same downstream decision
objective**, not a comparison of two algorithms on equal footing. This
should be stated explicitly wherever the result is reported, so the
comparison cannot be read as pretending retrieval and generation faced
identical constraints.

## Why this is not already covered by existing infrastructure

This project already has two pieces of purchasability/database
infrastructure, and neither one answers the question above:

1. **`check_patent_membership.py`'s ZINC-instock check** uses molbloom's
   bundled `zinc-instock-mini` catalog, which is an **exact-structure
   Bloom filter**: given one canonical SMILES, it answers "is this precise
   molecule purchasable," with no way to enumerate members or run a
   similarity search against it. It found exactly 1/16 frozen candidates
   (GM_031) is an exact hit. That is a *membership* check on candidates
   already produced by generation -- it cannot retrieve new candidates.
2. **The property-matched decoy panel** (`decoy_panel_v1.0/`) built a
   1.26M-molecule eligible pool from ChEMBL 37 with almost the right
   machinery (a staged property-envelope filter, ECFP4 Tanimoto scoring
   against the candidates and against the seed, a frozen, hashed source
   snapshot) -- but built it to **exclude** anything within 0.30-0.35
   Tanimoto of the seed/candidates, because its purpose was statistically
   independent decoys for gate calibration. A catalogue baseline needs the
   opposite selection (molecules *inside* that similarity band, from a
   *purchasable* source, not ChEMBL's general medicinal-chemistry
   literature corpus).

So this baseline needs a **new, structure-bearing purchasable-compound
dataset** (not a Bloom filter, not ChEMBL) and a **new selection direction**
(similarity-seeking, not similarity-excluding). The decoy panel's staged,
hashed, frozen-snapshot pattern is worth reusing as a template for
reproducibility discipline, not as a data source.

## Proposed design

**Candidate source.** ZINC's purchasable ("in stock" / short-delivery)
tranches, since ZINC is already this project's reference purchasability
vocabulary (via molbloom) and its tranche files are pre-partitioned by
molecular weight and cLogP -- which lets the search be restricted, before
any similarity scoring, to the tranches overlapping the frozen gate's own
MW [200, 550] Da and cLogP [0, 5] windows. This shrinks the search space to
a tractable size using a criterion that is *already* part of the frozen
contract, not a new, ad hoc restriction invented for this baseline. A
specific ZINC release/date must be pinned and its download hashed (SHA-256,
recorded the same way `decoy_source_manifest.json` records ChEMBL's
provenance) before any query is run, so the snapshot cannot silently drift
between a first attempt and a rerun -- exactly the failure mode this
project already documented for embedding non-determinism (Appendix D) and
does not want to reintroduce here.

**Query.** The same seed used to condition GenMol
(`C1=C(C(=C(C=C1Br)Br)N)CNC2CCC(CC2)O`, i.e. the dibrominated-aniline
scaffold linked to a cyclohexanolamine), so the comparison is "generate
near this seed" vs. "retrieve near this seed," not two different targets.

**Similarity metric and band.** Identical to the frozen gate: ECFP4/Morgan
fingerprints, radius 2, 2048 bits (RDKit's `rdFingerprintGenerator`, same
call already used in `build_candidate_manifest.py`), Tanimoto similarity to
the seed in **[0.30, 0.95)** -- the same inclusive/exclusive band the
frozen contract already uses to distinguish "a real analog" from "trivial
near-duplicate" and "unrelated." No new threshold is introduced.

**Request-budget equivalence.** GenMol and MolMIM were each *requested*
300 outputs (some invalid or duplicate, hence the funnel's `valid`/`unique`
stages before qualification). A catalogue similarity search returns only
valid, already-real structures, so there is no direct invalid-output analog
-- but uniqueness is not automatic across data sources and must not be
assumed (see the canonicalization note below). Rule, **pre-specified and
frozen before any catalogue-search results are inspected** (this is an
internal freeze-before-execution discipline, not a claim of external
preregistration -- the original generator results are already known, which
is exactly why the selection rule needs to be fixed in writing first
rather than adjusted after seeing what the catalogue returns): take the
**top 300 catalogue hits by Tanimoto similarity to the seed** (descending,
ties broken by ZINC ID for determinism) that fall within the [0.30, 0.95)
band and the MW/cLogP pre-filter above, **after** deduplicating by this
project's own canonical SMILES (below). This matches the *requested*
budget exactly (300) rather than trying to construct an artificial
"returned/unique" stage that has no real counterpart for a deterministic
catalogue query.

**Canonicalization and property recomputation: never trust the catalogue's
own values.** ZINC's tranche assignment (MW, logP) and any deduplication
ZINC itself performs are computed by ZINC's own toolchain, not RDKit, and
are used here **only** as a coarse pre-filter to bound which tranches are
worth downloading -- never as the basis for an accept/reject decision. Two
concrete steps this requires, both already implied by "the downstream gate
sequence remains unchanged" but worth making explicit so the pre-filter
cannot silently leak into the gate itself: (1) every candidate structure
must be re-canonicalized with this project's own RDKit version and
canonicalization settings *before* deduplication or ranking, so two ZINC
entries that ZINC treats as distinct (e.g. different salt forms or
tautomer records) but that canonicalize identically here are correctly
merged, and so a compound near a tranche's MW/logP boundary is not silently
dropped because ZINC's property computation disagrees with RDKit's; and
(2) MW, cLogP, TPSA, QED, and SA for every candidate must be recomputed by
this project's own frozen pipeline (the same RDKit/Crippen/QED/`sascorer`
calls `build_candidate_manifest.py` already makes), not read from ZINC's
metadata, exactly as the frozen gate already does for GenMol/MolMIM output.

**Downstream funnel: unmodified.** Feed the (recomputed-property,
project-canonicalized) 300 catalogue hits through
`build_candidate_manifest.py`'s existing gate sequence exactly as written
for GenMol/MolMIM -- dedup by canonical SMILES, `not_exact_seed`, the same
similarity-band re-check (redundant with the query filter but kept for
pipeline parity), QED >= 0.5, SA <= 5.0, MW/cLogP/TPSA windows, PAINS, and
the Brenk gate (with the same single seed-inherited allowlisted alert,
since a catalogue analog sharing the seed's aniline core would otherwise be
flagged for the same reason GenMol's outputs are allowlisted). Whatever
qualifies becomes a third row in the same funnel table already reported
for GenMol and MolMIM. Any qualifying hit that also appears in the existing
69-candidate pool (by canonical SMILES) should be flagged and deduplicated
against, not double-counted as a novel catalogue-only qualifier.

## Primary analysis: two levels, not one, and the second is conditional

The chemical-qualification funnel above and the structural (docking) stage
below must be analyzed and reported **separately**, because they differ in
exactly the property that matters most given this project's own prior
finding of run-to-run docking instability (Appendix D: a fresh-embedding
rerun changed 18/69 candidate-screen labels and 3/14 redocking Success@1
verdicts under a fixed seed, with machine/build drift left as an open,
unconfirmed explanation).

**Level 1 -- chemical qualification (safe to compare against the existing
frozen numbers as-is):**

    Y_chemical = N_passes_frozen_chemical_contract / 300

computed identically for GenMol, MolMIM, and catalogue retrieval. This
stage is a deterministic function of a fixed input structure and a frozen
RDKit pipeline -- no docking, no embedding step, nothing exposed to the
non-determinism already documented elsewhere in this project. The
catalogue arm's Y_chemical can therefore be compared directly against the
existing frozen 66/300 (GenMol) and 3/300 (MolMIM) without rerunning
anything for those two arms. **This level alone directly answers the
missing-comparator question** the review raised, independent of any
docking result.

**Level 2 -- structural/docking qualification (NOT safe to compare against
the existing frozen numbers without a same-batch rerun):**

    Y_structural = N_passes_chemical_and_structural_contract / 300

**Do not** dock the catalogue arm's chemical qualifiers on whatever
schedule is convenient and then report "catalogue X/300 structural vs.
GenMol 15/300, MolMIM 1/300 structural" as if it were a clean comparison.
Given this project's own documented embedding/docking run-sensitivity, a
catalogue-arm docking run performed at a different time (different
machine, build, or even just a different day on the same machine, per
Appendix D's unresolved environment-drift hypothesis) confounds
acquisition-policy effects with batch effects in exactly the way this
project has already had to correct for once. Two acceptable paths, and
only two:

1. **Same-batch three-arm rerun.** Redock all of GenMol's 66, MolMIM's 3,
   and the catalogue arm's chemical qualifiers together, in one docking
   batch, same environment, same session, ideally blinded to arm identity
   during scoring. Only this produces a numerically comparable
   Y_structural across all three arms, and it should be reported as a new,
   explicitly-dated rerun, not silently substituted for the manuscript's
   existing frozen 15/300 and 1/300 structural results.
2. **Descriptive-only catalogue docking.** Dock the catalogue qualifiers
   with the identical frozen GNINA setup (3KEH/3KE0, the 3GXF/IFM-derived
   active-site box, five-pose output, identical flags -- Appendix C) and
   report the resulting pass count and triage/ADMET-AI readouts as
   descriptive information about the catalogue arm on its own terms, while
   explicitly refusing to state a numerical superiority or inferiority
   claim against the manuscript's existing frozen 15/300 (GenMol) or 1/300
   (MolMIM) structural results. This preserves the manuscript's existing
   frozen structural numbers as the historical primary analysis, unchanged.

Path 2 is cheaper and is the default if resourcing does not allow a full
three-arm rerun; path 1 is the only way to make a numerical Level-2 claim.
Either way, the patent-membership / ZINC-instock check becomes close to
tautological for the catalogue arm (the candidates were purchasable by
construction), which is worth stating explicitly rather than silently
omitting that column.

**Recommended sequencing if resources are constrained:** run Level 1
(catalogue retrieval + frozen chemical funnel) first and on its own. It is
cheap (no GPU, no docking), answers most of the scientifically important
question by itself, and does not inherit the docking-reproducibility
problem at all. Given that this project has already found its own docking
pipeline run-sensitive, rushing a Level-2 comparison without doing it
properly (path 1 above) would be lower value than simply not running
Level 2 yet.

## What this would and would not establish

**Would establish (Level 1, on its own, no docking needed):** a directly
comparable chemical-qualification yield (catalogue X/300 vs. GenMol 66/300
vs. MolMIM 3/300) under the exact same frozen chemical contract, answering
whether the contract's own similarity band already picks out a densely
purchasable region of chemical space, independent of docking or any
non-deterministic pipeline stage.

**Would additionally establish (Level 2, conditional on the same-batch
rerun above):** a directly comparable structural/docking readout, but only
if produced via path 1 (same-batch three-arm rerun); via path 2
(descriptive-only), it establishes only what the catalogue arm's own
docking/triage/ADMET numbers look like in isolation, not a numerically
defensible ranking against the frozen historical GenMol/MolMIM structural
results.

**Would not establish, at either level:** anything about binding, chaperone
activity, or GCase stabilization (unchanged from every other arm of this
project -- no wet-lab data exists yet); freedom-to-operate or patentability
(same narrow scope as the existing patent-membership check); or a general
claim about "generation vs. retrieval" beyond this one seed and this one
gate set -- one seed, one similarity band, and one catalogue snapshot is an
existence comparison, not a benchmark, and (per the framing note above) a
comparison of configured acquisition policies, not a symmetric algorithm
bake-off.

## Known asymmetries to disclose if this is run

- **No natural replicate.** GenMol/MolMIM were each queried 3 times,
  giving a between-replicate spread that the paper's cluster-bootstrap CI
  now reports honestly (Table 1 caption). A deterministic similarity
  search against a frozen snapshot returns the same top-300 every time --
  there is no equivalent variance to estimate unless the pool is
  artificially split (e.g., bootstrap-resampling the ranked hit list
  itself, which estimates sampling-order sensitivity, not run-to-run
  pipeline variance, and should not be conflated with the generators'
  replicate spread if reported side by side).
- **Ceiling effect risk in the wrong direction.** If the seed already has
  many close purchasable analogs (plausible, since it is a simple,
  drug-like small molecule, not an exotic generated structure), the
  catalogue arm could trivially outperform both generators on yield alone
  without saying anything interesting about generative-model quality in
  general -- the result should be read as specific to how well-populated
  this seed's own neighborhood already is in commercial catalogues, not as
  a general verdict on generation vs. retrieval.
- **Retrieval cannot exceed the catalogue's own chemical space.** A "loss"
  for the catalogue arm does not establish that generation is better in
  any deep sense -- only that this particular purchasable snapshot happens
  not to contain good analogs of this particular seed. Both directions of
  the result need this caveat stated in the same paragraph that reports
  the number, not deferred to a Limitations section a reader can skip.

## Rough effort estimate (for scheduling, not a commitment)

- **New data, one-time:** download and hash the relevant ZINC tranche
  files restricted to the MW/cLogP pre-filter (small enough to be
  practical; exact size depends on which tranches ZINC's current release
  assigns to that window). No GPU needed.
- **New code, small:** a query/selection script (RDKit fingerprinting +
  ranking, no ML), and a thin adapter so `build_candidate_manifest.py`
  accepts a third input source under its existing gate logic unmodified
  (a config change, not new gate logic -- the whole point is to reuse the
  frozen contract exactly).
- **Reused, unmodified:** the GNINA docking runner, the triage script, the
  ADMET-AI predictor, and the patent/purchasability checker -- all already
  built and frozen for the 69-candidate population. For Level 2 path 2
  (descriptive-only), running them on the catalogue arm alone costs the
  same per molecule as the existing 146-job candidate-screen run, scaled to
  however many catalogue hits qualify. For Level 2 path 1 (same-batch
  three-arm rerun), the cost is higher: it requires redocking all 69
  existing GenMol/MolMIM chemical qualifiers alongside the new catalogue
  qualifiers in one batch, not just docking the catalogue arm.
- **Not required:** any change to the frozen v1.2 chemical gates, the
  receptor preparation, or the docking box -- this baseline's entire value
  depends on reusing the existing frozen contract exactly, not adapting it.

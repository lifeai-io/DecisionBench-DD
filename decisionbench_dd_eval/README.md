# decisionbench_dd_eval

Common downstream evaluator for the GenMol/MolMIM primary generation benchmark
(DESCRIPTION.md Section 3 / Section 20). Ingests raw NIM run outputs, scores
every molecule identically regardless of which tool produced it, applies the
pre-registered qualification gates, and writes the generator scorecard.

## Setup

```
pip install -r requirements.txt   # rdkit, numpy
```

## Run

```
python -m decisionbench_dd_eval.evaluate_generators \
    --manifest-dir runs/ \
    --out-dir results/
```

See `runs/README.md` for the expected input layout. Outputs land in `results/`:

| File | Contents |
| --- | --- |
| `molecule_level.csv` | every generated candidate, every metric, every gate pass/fail (appendix-ready) |
| `table1_generator_scorecard.csv` | DESCRIPTION.md Section 3 Table 1, per replicate + a pooled row per tool, with bootstrap 95% CIs on qualified yield |
| `figure2_similarity_qed_scatter.csv` | Section 13 Figure 2 data (similarity-to-seed vs. QED, colored by gate survival) |
| `figure4_funnel.csv` | Section 13 Figure 4 funnel, pooled across replicates per tool |
| `summary.md` / `summary.json` | headline numbers in "`X% (95% CI a-b)`" form (Section 12 reporting style) |

## Design notes

- **One evaluator, two tools.** Every metric (QED, SA, MW, cLogP, TPSA, PAINS/Brenk
  alerts, Tanimoto-to-seed) is computed by this package from RDKit, never taken
  from either NIM's own `score` field. The API's self-reported score is kept per
  molecule as `api_score` for audit only, per common_protocol.json's
  `known_native_objective_difference` rule (GenMol's QED field ranks its own
  output; MolMIM's CMA-ES actively optimizes QED — those are not interchangeable
  and must not leak into the comparison).
- **Gates are data, not code.** All qualification gates live in
  `decisionbench_dd_configs_v1.0/qualification_gates_v1.0.json`, frozen alongside
  the rest of the v1.0 protocol. `gates.py` only interprets that file. Changing a
  threshold always shows up as a diff there (DESCRIPTION.md Section 15: don't
  select thresholds after seeing which tool wins).
- **PAINS and Brenk are scored as two separate catalogs.** PAINS is an
  absolute gate (`pains`, zero hits required) with no seed-relative treatment,
  since Ambroxol triggers zero PAINS alerts. Brenk is seed-relative and
  **instance-aware** (`no_new_unmapped_structural_alert_instances`, v1.2): a
  candidate Brenk occurrence counts as seed-inherited only if it has the same
  alert type AND its matched atoms equal a seed alert instance's atoms mapped
  onto the candidate via a maximum-common-substructure (MCS) atom
  correspondence (`qualification_gates_v1.0.json:seed_relative_alert_rule` /
  `instance_mapping`). A second, independent occurrence of an already-allowlisted
  Brenk type (e.g. a molecule with two chemically distinct anilines) IS flagged
  as new -- this supersedes v1.1's coarser plain type-level set difference,
  which could not tell the two apart (see that file's `version_history`).
  Getting this right required working around a real RDKit limitation:
  `FilterCatalogEntry.GetFilterMatches` only returns a pattern's first
  occurrence per molecule, even when several exist (verified on benzidine);
  `chem_metrics.get_brenk_instances` pulls the underlying SMARTS query and
  re-matches it directly to enumerate all occurrences. Every molecule record
  reports `pains_alerts`, `brenk_alerts_all`, `brenk_alerts_seed_inherent`,
  `brenk_alerts_new`, `passes_pains_gate`, `passes_seed_relative_alert_gate`
  (v1.1 Section 6 field names, now instance-aware values), plus the full
  per-occurrence `brenk_alert_instances` audit trail -- allowlisting never
  removes an alert from the reported data. Table 1 also reports three Brenk
  rates (Section 9): `r_brenk_pct` (any Brenk alert instance), `r_seed_alert_pct`
  (all instances seed-inherited), `r_new_alert_pct` (>=1 new/unmapped instance --
  the one used for qualification).
- **Known, documented simplification:** the seed↔candidate atom correspondence
  uses RDKit's first MCS substructure match. For a seed or candidate with
  symmetry-equivalent substructures, a different, equally valid mapping could
  exist and change the classification -- not resolved by trying every
  automorphism in this version (`qualification_gates_v1.0.json:instance_mapping:
  known_simplification_not_resolved`).
- **The seed's own Brenk instances (type + atom indices) are frozen in
  `seed_alert_catalog.json`, and a mismatch is a hard failure, not a warning.**
  Unlike the seed-SMILES sanity check (which auto-corrects and warns), the
  evaluator recomputes M_seed from RDKit at startup and refuses to run if it
  disagrees with that frozen file -- per the file's own "no additional alert
  after inspecting results" policy, a drift here (e.g. from an RDKit upgrade)
  must be deliberately reviewed and the file regenerated, never silently
  trusted either way.
- **Denominator is `requested`, not `returned` or `valid`.** `Y_qualified =
  N_pass_all_gates / N_requested` per replicate (Section 3), so a tool that
  silently returns fewer molecules than requested is not rewarded for it.
- **Uniqueness is within-replicate.** The `unique` gate dedups within a single
  run's own output, matching the per-replicate `Y_qualified` denominator.
  Cross-replicate duplication is reported separately in the pooled Table 1 row
  (`cross_replicate_duplicate_canonical_smiles`) as a reproducibility diagnostic,
  not as a gate.
- **`vendor/sascorer/`** is RDKit's own `Contrib/SA_Score` implementation
  (Ertl & Landrum, BSD-licensed), vendored because the `rdkit` PyPI wheel does not
  ship the Contrib scripts.

## Finding from the fixture smoke test (now resolved, v1.1 → v1.2)

Running the pipeline against synthetic fixture data (`tests/fixtures/`) showed
that Ambroxol itself, and every close on-scaffold analogue (Br→Cl, Br→F
substitutions), trips RDKit's Brenk **`aniline`** structural alert — Ambroxol's
free aromatic primary amine is a real, well-known alert motif, not a fixture
artifact. Under an absolute "zero alerts" gate, essentially the entire
seed-scaffold family — including molecules structurally identical to Ambroxol —
would fail qualification, mostly measuring how far a generator strays from the
seed chemotype rather than how many useful analogues it produced.

v1.1 fixed that with a type-level seed-relative rule, which itself had a real
flaw: it couldn't distinguish "the seed's own aniline" from "an unrelated
second aniline introduced elsewhere" -- both are just the type `aniline` under
a plain set. v1.2 fixed that by tracking alert *instances* with their matched
atoms and requiring positional correspondence to a specific seed occurrence
(see "PAINS and Brenk are scored as two separate catalogs" above,
`qualification_gates_v1.0.json`'s `version_history` field, and
`seed_alert_catalog.json` for the frozen record).

## Tests

```
python -m unittest discover -s decisionbench_dd_eval/tests -p "test_*.py"
```

`tests/fixtures/` contains small synthetic (non-API) manifest+raw-response pairs
used only to exercise the pipeline's code paths (validity failures, duplicates,
exact seed copies, a PAINS hit, gate combinations, funnel monotonicity). They are
not real GenMol/MolMIM output and must not be used for any reported results.

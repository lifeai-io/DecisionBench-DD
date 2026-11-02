# DecisionBench-DD v1.0 — Generator Configs

Primary comparison:
- GenMol NIM: 3 independent calls × 100 requested molecules
- MolMIM NIM: 3 independent calls × 100 requested molecules
- Frozen generator input SMILES: C1=C(C(=C(C=C1Br)Br)N)CNC2CCC(CC2)O
- Canonical downstream identity SMILES: Nc1c(Br)cc(Br)cc1CNC1CCC(O)CC1

Important:
1. Save raw responses before any filtering.
2. Use the exact same literal Ambroxol SMILES in both generator requests.
3. Canonicalize only in the common downstream evaluator.
4. Do not enable GenMol `unique`; duplicate rate is a benchmark outcome.
5. Do not enable GenMol `filter`; common downstream filters must be tool-independent.
6. Do not alter parameters between replicates.
7. MolMIM's CMA-ES actively optimizes QED with min_similarity=0.3; GenMol's QED field scores/ranks generated outputs. Treat this as a native-method difference, not as equivalent internal optimization.
8. Existing GenMol 3×1,000 runs belong to the scaling/uniqueness stress-test analysis, not the primary 3×100 comparison.

## Primary-vs-pilot note
The earlier GenMol experiments used temperature=1.0, noise=0.0 and 1,000 requested molecules/run.
Those results are retained only as an exploratory scaling/uniqueness stress test.

For the primary 3×100 head-to-head benchmark, GenMol uses the documented NIM defaults:
temperature=1.0 and noise=1.0. This avoids selecting a primary parameter setting after observing
its uniqueness behavior.

## Qualification gates (v1.2)

`qualification_gates_v1.0.json` (internally versioned `protocol_version: "1.2"`)
freezes the pre-registered candidate gates from DESCRIPTION.md Section 4 (validity,
within-replicate uniqueness, exact-seed-copy check, seed-similarity band, QED, SA,
MW, cLogP, TPSA, structural alerts) plus the 12-stage funnel grouping used for
Figure 4. It is consumed by `decisionbench_dd_eval/gates.py` — see that package's
README for the generator-evaluation pipeline that ingests raw GenMol/MolMIM outputs
against this spec.

PAINS and Brenk are two separate gates. PAINS remains **absolute** (zero hits
required; Ambroxol triggers none). Brenk is **seed-relative and instance-aware**:
a candidate Brenk occurrence is allowed only if it maps, atom-for-atom via a
maximum-common-substructure correspondence, onto one of the seed's own alert
instances (Ambroxol's own aromatic primary amine trips RDKit's Brenk `aniline`
rule at its own position and does not block qualification; a second, unrelated
occurrence of the same alert type elsewhere does). This supersedes an earlier
v1.1 rule that only compared alert *type* identifiers and could not tell "the
seed's own alert" apart from "an unrelated new instance of the same type" — see
`qualification_gates_v1.0.json`'s `version_history` for that history.
`seed_alert_catalog.json` is the frozen, audited record of the seed's own alert
instances (type + matched atom indices); the evaluator recomputes them at runtime
and **hard-fails** (not just warns) if it disagrees, per that file's "no
additional alert after inspecting results" policy. See
`qualification_gates_v1.0.json`'s `seed_relative_alert_rule` and
`instance_mapping` fields for the full formal definition, including a documented
(not silently resolved) simplification around molecular symmetry.

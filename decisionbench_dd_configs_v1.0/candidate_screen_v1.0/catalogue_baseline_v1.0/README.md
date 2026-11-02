# Catalogue/purchasable-library baseline -- Level 1 results (chemical qualification only, no docking)

Executed 2026-09-23, per `CATALOGUE_BASELINE_SCOPE_v1.0.md` (one directory
up). This is **Level 1 only** (`Y_chemical`) -- deterministic chemical
qualification, no docking, no GPU. Level 2 (`Y_structural`, GNINA docking)
was explicitly **not** run in this pass; per the scope document it requires
either a same-batch three-arm rerun (redocking all of GenMol's 66 and
MolMIM's 3 alongside any catalogue qualifiers) or an explicit descriptive-
only framing, and was deferred pending a decision on which path to take.

## What was run

1. Downloaded all ZINC 2D tranche files (files.docking.org) whose stated
   MW/LogP range overlaps the frozen gate's MW [200,550] / cLogP [0,5]
   windows: MW-row letters B-K x LogP-column letters C-J, reactivity in
   {A,B,C,E} (ZINC's own historical "Mild" tier), purchasability in {A,B}
   ("in stock"). 640 files, 532,196,733 bytes, 0 download failures.
   Per-file SHA-256 in `zinc_source_manifest.json`.
2. Streamed all 9,322,808 raw SMILES lines through this project's own
   frozen RDKit pipeline (`rdkit==2026.03.5`, matching the version already
   recorded for GenMol/MolMIM): 9,322,802 parsed (6 rejected for invalid
   valence, all Sn-containing organometallics), collapsed to 9,320,110
   unique molecules by this project's own canonical SMILES (ZINC's own
   per-file dedup was not trusted, per the scope document).
3. Scored ECFP4/Morgan (radius 2, 2048 bit) Tanimoto similarity to the
   seed for every unique molecule. **Only 804 of the 9,320,110 (0.0086%)
   fell inside the frozen gate's own similarity band [0.30, 0.95)** -- this
   is the single most important number in this result, see below.
4. Took the pre-specified top 300 of those 804 by similarity (descending,
   ZINC ID ascending as tiebreak) -- i.e., **more than a third of every
   purchasable in-stock molecule that exists in this snapshot within the
   band**, not a small sample from a large available pool.
5. Ran those 300 through the unmodified remainder of the frozen v1.2 gate
   sequence (QED, SA, MW, cLogP, TPSA, PAINS, Brenk-with-allowlist),
   reusing the exact functions from `build_candidate_manifest.py`.

## Headline result

| Arm | Requested | Chemically qualified | Yield |
|---|---:|---:|---:|
| GenMol | 300 | 66 | 22.0% |
| MolMIM | 300 | 3 | 1.0% |
| **ZINC catalogue retrieval** | **300** | **258** | **86.0%** |

Zero of the 258 catalogue qualifiers exactly match any of the existing 69
GenMol/MolMIM chemical qualifiers (checked by canonical SMILES).

**This is not a "generation loses" result, for exactly the reason the
scope document's "ceiling effect risk in the wrong direction" caveat
anticipated, and it is worth stating plainly rather than as a footnote:**
the bottleneck for the catalogue arm is almost entirely *finding* a
purchasable molecule similar enough to the seed at all (804 out of 9.32M,
i.e., a 0.0086% hit rate on the similarity criterion), not clearing the
downstream drug-likeness gates once one is found (86% of the top-300
found pass everything else). GenMol's bottleneck is the opposite shape --
its own funnel (`candidate_manifest_summary.json`) shows 148/300 (49.3%)
of its unique output already lands in the similarity band (unsurprising,
since it is explicitly scaffold-conditioned on the seed), but then loses
more than half of those to the downstream property gates (148 -> 66,
44.6% pass-through). **Read together, this suggests the frozen contract's
downstream property gates (QED/SA/MW/cLogP/TPSA/PAINS/Brenk) are not
very selective against real, purchasable, already-drug-like molecules
once they are seed-similar -- commercial screening compounds tend to
already be drug-like by construction -- while the seed-similarity
criterion itself is the genuinely hard constraint, one a fixed catalogue
snapshot satisfies only very rarely relative to its own size.** This
directly answers the "does the contract itself select an already-densely-
populated region" framing from the scope document: no, not on the
similarity axis -- the region is sparse even in a 9.32M-compound
purchasable snapshot -- but yes, on the downstream property-gate axis,
once similarity is satisfied.

## Diversity correction (added after inspecting the raw candidate list)

The frozen Morgan/ECFP4 fingerprint (matching every other use in this
project) does not encode stereochemistry, so several ZINC entries that
are pure stereoisomers of one 2D skeleton independently qualify with
identical similarity/QED/SA/MW/cLogP/TPSA. The raw 258 therefore
overstates genuine chemical diversity, and a fair comparison to GenMol/
MolMIM's own numbers requires the same correction on both sides
(`scaffold_diversity_check.py`, reusing the exact Murcko-scaffold
extraction and the exact greedy single-linkage ECFP4 clustering at 0.60
Tanimoto already applied to the 16 primary GenMol/MolMIM passers in
`decisionbench_dd_docking/triage_primary_candidates.py`):

| Arm | Raw qualified | Distinct Murcko scaffolds | ECFP4 clusters (>=0.60 Tanimoto) |
|---|---:|---:|---:|
| GenMol | 66 | 42 | 22 |
| MolMIM | 3 | 3 | 3 |
| GenMol+MolMIM combined | 69 | 45 | 25 |
| **ZINC catalogue retrieval** | **258** | **79** | **62** |

One single scaffold (`c1ccc(CNC2CCCCC2)cc1`, the seed's core amine-
cyclohexane linker with the ring aromatic left unsubstituted -- Murcko
scaffolds strip exocyclic halogens/amines by definition, the same known
limitation this metric already carries for the existing 16-candidate
table) alone accounts for 70 of the 258 catalogue rows. The raw-to-cluster
compression ratio is similar in kind for both arms (catalogue: 62/258 =
24%; GenMol: 22/66 = 33%), so this is not an artifact specific to the
catalogue arm -- but because the catalogue arm's raw count is so much
larger, its **cluster-corrected** advantage over GenMol survives, just at
a smaller magnitude than the raw numbers suggest: **62 vs. 22 distinct
ECFP4 clusters among the respective 300-candidate acquisition outputs, a
~2.8x ratio**, not merely a ~3.9x ratio in raw (redundancy-inflated) count.
("Cluster" here is a fingerprint-clustering heuristic, not a claim about
genuinely distinct chemotypes -- the two arms also differ in how many
molecules qualified in the first place.)

## What this does and does not establish (unchanged from the scope document)

Nothing here establishes binding, chaperone activity, or GCase
stabilization for any catalogue qualifier -- identical caveat to every
other arm of this project. Nothing here is a Level-2 (structural/docking)
result; per the scope document, that comparison is explicitly deferred
pending a same-batch three-arm rerun or an explicit descriptive-only
framing, precisely because this project has already documented its own
docking pipeline's run-to-run sensitivity (Appendix D). This is a
comparison of configured acquisition policies (a retrieval procedure that
uses the contract's own similarity/MW/cLogP windows at selection time)
under the same downstream chemical objective, not a symmetric algorithm
comparison -- the framing note from the scope document applies to this
result exactly as written there.

## Files in this directory

- `zinc_tranches/` -- 640 raw downloaded `.smi` files (532 MB total; not
  committed to git, same treatment as the decoy panel's 128 MB
  `eligible_pool_v1.0.csv` -- regenerable from `zinc_source_manifest.json`'s
  recorded checksums and source URLs).
- `zinc_source_manifest.json` -- per-file SHA-256, byte counts, download
  date, and the exact tranche-selection rule.
- `build_catalogue_baseline.py` -- the Level-1 pipeline (download already
  done; this script does load/dedup/similarity-score/top-300-select/gate).
- `catalogue_candidate_manifest.csv` -- the 258 qualified rows.
- `catalogue_gate_audit.csv` -- all 300 evaluated rows (pass and fail) with
  per-stage detail, same shape as the existing `chemical_gate_audit.csv`.
- `catalogue_manifest_summary.json` -- funnel counts, gate definitions,
  overlap check, in the same schema style as `candidate_manifest_summary.json`.
- `scaffold_diversity_check.py` / `scaffold_diversity_summary.json` -- the
  diversity-correction analysis above.

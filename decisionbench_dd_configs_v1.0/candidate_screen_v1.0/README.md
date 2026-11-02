# Candidate screen v1.0 package

This package freezes the next DecisionBench-DD experiment after completion of the 14-case GCase redocking benchmark.

- `candidate_manifest.csv`: immutable population of 69 chemically qualified generated molecules.
- `chemical_gate_audit.csv`: all 600 returned records with stage-level decisions.
- `candidate_manifest_summary.json`: gate definitions, versions, and reproduced funnel counts.
- `downstream_gcase_screening_protocol.md`: pre-run neutral/acidic N370S GCase screening protocol.
- `experimental_validation_panel_v1.0.{md,json}` (amended v1.1, corrected v1.1.1): frozen (before any wet-lab data exists) experimental-validation panel and assay plan for a first tranche of 6 of the 16 primary passers -- analytical solubility/cytotoxicity, GCase binding/stabilization plus sign-agnostic catalytic modulation across pH, then cellular chaperone rescue, hERG, metabolic stability, and oral+CNS permeability (passive and transporter efflux reported separately) for compounds that pass. v1.1 fixed a mechanistic self-contradiction in v1.0 (a neutral-pH "activation" gate conflicting with Ambroxol's actual pH-dependent inhibitor pharmacology); v1.1.1 fixed the inhibitor-type description (mixed-type, not competitive), the N370S/N409S same-variant confusion, an underspecified statistical pre-registration, a branch-undefined cytotoxicity gate, a self-contradictory hepatocyte-stability gate, PAMPA-BBB/transporter-efflux conflation, and hERG/cellular-assay execution rigor -- all pre-data; compound membership unchanged throughout. This project has no wet lab; this is a specification for whoever executes it, not a report of results.
- `SHA256SUMS.json`: hashes for generated manifest artifacts.

## Results (added as the pipeline executed)

- `receptor_state_manifest.json`, `docking_boxes.json`: 3KEH/3KE0 preparation and the 3GXF/IFM-derived active-site box.
- `ligand_microstate_manifest.csv`: 146 prepared ligand microstates (69 candidates + 4 controls x 2 pH states).
- `../../candidate_screen_runs/`: 146 GNINA job outputs + provenance manifest.
- `../../candidate_screen_results/`: primary scoring (`summary.md`/`.json`, `candidate_results.csv`, `pose_scores.csv`, `generator_funnel.csv`) plus the section-10 bounded reranking-sensitivity analysis (`best_of_5_rescue.csv`, `selector_sensitivity.csv`, `candidate_selector_turnover.csv`, `rerank_sensitivity.md`) -- sensitivity readouts only, they do not change the frozen 15 GenMol + 1 MolMIM primary result.
- `../../candidate_screen_results/primary_candidate_triage.{csv,md}`: section-11 triage of the 16 primary passers -- physicochemical drug-likeness (QED/SA/MW/cLogP/TPSA/Ro5 violations), a docking-derived ligand-efficiency proxy, and ECFP4/Murcko scaffold-diversity clustering. All 16 advance (<=20 rule).
- `../../candidate_screen_results/admet_predictions.{csv,md}`: predictive ADMET for the 16 primary passers + Ambroxol via ADMET-AI (Swanson et al., Bioinformatics 2024; `pip install admet_ai`, run locally, no network calls at prediction time) -- hERG, AMES, DILI, ClinTox, BBB/HIA/Caco2/PAMPA permeability, bioavailability, CYP450 inhibition, clearance, half-life, solubility, and DrugBank-approved-drug percentile ranks (~50 endpoints total in the CSV). Model predictions, not experimental measurements.
- `../../candidate_screen_results/patent_membership.{csv,md}`: exact-structure patent-literature membership (molbloom's `surechembl` catalog -- ~30.9M molecules text-mined from EPO/USPTO/WIPO patents by EBI's SureChEMBL project, FPR 0.000025) plus ZINC in-stock purchasability, for the 16 primary passers + Ambroxol. Sanity-checked against Ambroxol (a marketed patented drug), which correctly returns True. This is NOT a similarity-based patent-proximity search, freedom-to-operate opinion, or claim-scope analysis -- see that module's docstring for the exact scope. Result: no exact-structure membership detected in the tested SureChEMBL snapshot for any of the 16 candidates; 1/16 (GM_031) separately matches a known purchasable ZINC in-stock compound -- read narrowly per the scope note above, not as a novelty or patentability claim.

## External review response (2026-08-26T23:31:21Z UTC, experimental-panel v1.1.1 corrections)

Every claim in this review was independently verified before acting (e.g. the system clock confirmed the review's stated "current date, August 26, 2026" was correct against this project's own mislabeled 2026-08-27 amendment timestamp) -- no fabrications found. Applied as `experimental_validation_panel_v1.0.md/.json`'s v1.1.1 correction: Ambroxol recharacterized as mixed-type (not competitive) inhibitor; N370S/N409S same-variant confusion fixed (GBA1 c.1226A>G, p.Asn409Ser under legacy vs. HGVS numbering, not two variants); section 3a's statistical pre-registration now specifies concrete default values instead of a bare checklist; the Tier1->Tier2 cytotoxicity gate now branches for stabilization-only vs. catalytic-modulator candidates; the overall-pass criteria's "ALL required" claim no longer contradicts treating hepatocyte stability as non-excluding (moved to an explicit optimization flag); PAMPA-BBB (passive-only) now explicitly separated from a required MDCK-MDR1/BCRP transporter-efflux assay; the 30x hERG index now explicitly requires validated patch-clamp (not thallium-flux triage) potency; "GBA1-specific lysosomal activity" now operationally defined (CBE-inhibitable fraction); this document's own README stale "docking outputs...intentionally absent" sentence removed and the patent-membership summary line's wording aligned with `patent_membership.md`'s own narrower framing.

## External review response (2026-08-27, ADMET/triage reporting corrections)

Every claim in this review was independently reproduced from the raw CSVs and confirmed exactly correct (including the precise "5 of 16" negative-microsome-clearance and "15 of 16" Brenk-alert counts) -- no fabrications found. Four fixes applied to `predict_admet.py`:

1. **Half-life units corrected**: `Half_Life_Obach` is predicted directly in hours, not log(hours) as the summary previously said -- confirmed both against the TDC benchmark's own definition and by internal consistency (the predicted range, ~15-76, would imply centuries-long half-lives if read as log-hours).
2. **Negative clearance flagged, not silently reported**: `Clearance_Hepatocyte_AZ_valid`/`Clearance_Microsome_AZ_valid` columns added to `admet_predictions.csv` (False when the raw regression output is negative, a physically impossible value for this endpoint and a model-extrapolation artifact, not evidence of unusually good stability).
3. **ADMET-AI version pinned in the output itself**: `admet_predictions.md` now records the exact `admet_ai`/`chemprop` package versions, a combined SHA-256 over the bundled model directory, this repo's git commit, and the exact command -- not just a citation to the (v1-era) paper.
4. **Brenk-alert context note added**: `BRENK_alert=1` on 15/16 candidates is the same single seed-inherited aniline instance already qualified against this project's own frozen v1.2 seed-relative alert gate, not 15 independently-discovered new liabilities -- ADMET-AI's raw Brenk check has no knowledge of that upstream allowlisting.

Also fixed: `patent_membership.md`'s "novelty signal" framing replaced with the review's suggested exact wording ("no exact-structure membership detected in the tested SureChEMBL Bloom-filter snapshot"), and a latent reproducibility bug in `triage_primary_candidates.py:load_passing_candidates()` -- iterating a Python `set` gave non-deterministic row order across runs (same content, different order) -- fixed by sorting.

## Provenance note (added on adoption into this repo, 2026-08-26)

This package originated outside this repo's own `decisionbench_dd_eval` pipeline as an
independent reimplementation of the frozen v1.2 chemical gates (see
`build_candidate_manifest.py`). Before adoption it was independently verified against
this repo's own trusted outputs:

- `build_candidate_manifest.py`'s `inputs/genmol_replicate_*.json` /
  `inputs/molmim_replicate_*.json` are content-identical (same molecule lists, just
  re-serialized) to this repo's `runs/raw/*.json` -- same underlying generation data,
  no substitution.
- `candidate_manifest.csv`'s 69 rows (66 GenMol + 3 MolMIM, by canonical SMILES) are an
  **exact match** to `results/molecule_level.csv`'s `qualified=True` rows, despite the
  independently-reimplemented gate logic differing in some details (e.g. its
  `inherited_alert_pass` uses a fixed seed-aniline-core SMARTS rather than this repo's
  MCS-based atom-mapped instance rule) -- a genuine cross-check, not a copy.
- The reported "GenMol: 201 unique" figure in this repo's own `results/summary.md` is
  the mean of three per-run unique counts (84+49+68=201/300=67.0%), not a globally
  pooled unique-molecule count (200 distinct molecules across all 3 runs) -- confirmed
  by direct computation. Does not change any of the 69 qualified candidates (none are
  cross-replicate duplicates).
- RCSB confirms 3KEH = human N370S GCase, pH 7.4, and 3KE0 = human N370S GCase, pH 5.4,
  and 3GXF/IFM's identity, exactly as stated in `downstream_gcase_screening_protocol.md`.
- **Unverified, not fabrication:** 6Q1N/6Q1P's actual RCSB ligand codes are `P9V`/`P8Y`
  (both real, correctly bound in those deposited structures); RCSB's own synonym data
  does not confirm "IMX8"/"norIMX8" as registered names for them. Downstream outputs in
  this repo report `P9V`/`P8Y` as the authoritative identifiers; treat "IMX8"/"norIMX8"
  as an informal/literature label pending a citable source.

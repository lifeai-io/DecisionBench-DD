# Property-matched decoy panel (post-hoc structural-gate calibration)

Everything in this directory except the GNINA docking/scoring itself is
already done and does not need a GPU. See `decoy_addendum_v1.0.md` for the
frozen pre-registration (question, endpoints, interpretation rules) --
read that first.

## What's already done (no GPU needed)

1. **`candidate_reference_v1.0.csv`** -- the 69 frozen chemical qualifiers
   (66 GenMol + 3 MolMIM) with the full property set (MW, HAC, cLogP, TPSA,
   HBD, HBA, rotatable bonds, formal charge, ring/aromatic-ring counts,
   halogen count, ECFP4 fingerprint), computed with the same RDKit
   version/canonicalization as the frozen chemical-gate audit.
2. **`decoy_source_manifest.json`** -- ChEMBL 37 chemreps source (URL,
   download date, SHA-256, 2,897,819 source rows), plus the exact staged
   filtering pipeline and counts (see `decoy_pool_filter_log.json`):
   stage A (cheap string filters) 2,673,415 pass -> stage B (RDKit sanitize)
   2,637,170 parsed -> stage C (property envelope) 1,261,863 in range ->
   1 exact-match exclusion, 713 excluded for ECFP4 Tanimoto >=0.35 to a
   candidate, 42 excluded for >=0.30 to Ambroxol -> **1,261,107 eligible**.
   `eligible_pool_v1.0.csv` (128MB, the full eligible pool) is **not
   committed to git** -- it's regenerable from the recorded source checksum
   via `python -m decisionbench_dd_docking.build_decoy_pool --chemreps
   <chembl_37_chemreps.txt.gz>` (same RNG-free, deterministic filtering).
3. **`property_matched_decoys.csv`** -- 345 decoys, 5 per candidate, matched
   without replacement (0 caliper relaxations needed, 0 short matches --
   the 1.26M pool was large enough that every candidate found 5 matches at
   the base calipers). Built by `match_decoys.py` (seeded, reproducible).
4. **`matching_balance.csv` / `matching_balance_figure.pdf`** -- covariate
   balance. **Disclosure required by the protocol:** HAC (SMD -0.045),
   cLogP (-0.030, both reviewer-priority variables for the CNNaffinity
   size-bias concern), and HBA (0.071) are within the <0.10 target; MW
   (0.162), TPSA (-0.118), rotatable bonds (0.164), and ring count (0.161)
   miss the strict <0.10 target but are within the <0.20 tolerance the
   protocol allows for sparse/discrete properties; **HBD (0.524) and
   halogen count (0.339) exceed even the 0.20 tolerance band**, despite
   every individual candidate-decoy pair satisfying its hard per-pair
   caliper (+/-1 for both). Several reweighted/randomized matching
   variants were tried (see git history of `match_decoys.py` if curious)
   and none improved HBD/halogen without degrading MW/HAC/cLogP/TPSA --
   this reflects a real tension between "topologically dissimilar"
   (Tanimoto <0.35 to any candidate) and "chemically identical profile"
   for a heavily dibromo/amine-substituted, Ambroxol-proximal candidate
   set: structurally distinct decoys that hit the same MW/HAC/cLogP
   envelope tend to do so via different means (more rings/heteroatoms
   instead of halogens), which is disclosed rather than hidden.
5. **Blinding** -- `decoy_panel_candidate_manifest.csv` (418 rows: 345
   decoys + 69 candidates, IDs replaced with `PMD_0001`-`PMD_0414` in
   random order, plus the 4 controls under their real `CTRL_*` IDs --
   see the file's docstring / `blind_decoy_panel.py` for why the controls
   are deliberately NOT blinded: `score_candidate_screen.py` hardcodes the
   literal ID `CTRL_AMBROXOL` to locate the pass/fail threshold, and
   blinding it would silently break scoring without changing what the
   blinding is actually protecting against). The candidates are
   **re-docked fresh in this same blinded batch** (not reusing the frozen
   primary poses) as an internal consistency check against the frozen
   16/69 result -- this also controls for the kind of cross-machine GNINA
   floating-point drift already documented in Appendix H of the paper.
   `decoy_panel_mapping.csv` holds the blinded-ID -> true-ID/role/matched-
   candidate mapping and must **never** be read by the docking or gate
   scripts.
6. **Ligand preparation** -- `docking_input_ligands/` (844 prepared SDFs:
   418 blinded entries + 4 controls, x2 receptor states) and
   `ligand_microstate_manifest.csv`. 0 microstate-ambiguous; 2/836
   embedding failures (both the same decoy, CHEMBL1186344, a bridged
   bicyclic structure ETKDGv3 could not embed at either pH) -- these
   remain in the 345 denominator as technical structural failures per the
   protocol, not dropped.

## What's left: run on a GPU machine with Docker

**1. Dock (834 GNINA jobs -- 418 blinded entries x 2 states, minus the 2
embedding failures, plus 4 controls x 2 states already counted in the 418):**

```bash
python -m decisionbench_dd_docking.run_candidate_screen_gnina \
    --microstate-manifest decisionbench_dd_configs_v1.0/candidate_screen_v1.0/decoy_panel_v1.0/ligand_microstate_manifest.csv \
    --out-dir decoy_panel_runs/
```

Uses the same digest-pinned GNINA image/boxes/config as the primary and
sensitivity screens -- do not retune anything after seeing decoy results.

**2. Score with the blinded manifest** (gives `structural_proxy_pass` for
every `PMD_*` ID and the 4 `CTRL_*` controls; do not pass the real
candidate/decoy identities into this step):

```bash
python -m decisionbench_dd_docking.score_candidate_screen \
    --runs-dir decoy_panel_runs/ \
    --candidate-manifest decisionbench_dd_configs_v1.0/candidate_screen_v1.0/decoy_panel_v1.0/decoy_panel_candidate_manifest.csv \
    --microstate-manifest decisionbench_dd_configs_v1.0/candidate_screen_v1.0/decoy_panel_v1.0/ligand_microstate_manifest.csv \
    --out-dir decoy_panel_results/
```

Note: `score_candidate_screen.py`'s built-in `generators` summary block
(genmol/molmim funnel) is meaningless here since every entry's `tool`
field is `decoy` or the candidate's real tool -- ignore that block and use
`candidate_results.csv` / `pose_scores.csv` directly, which is what step 3
does.

**3. De-blind, decompose the gate, and run the primary/secondary statistics**
(this is the step that actually answers the addendum's question):

```bash
python -m decisionbench_dd_docking.analyze_decoy_panel \
    --candidate-results decoy_panel_results/candidate_results.csv \
    --pose-scores decoy_panel_results/pose_scores.csv \
    --n-boot 5000
```

Writes `decoy_specificity_report.json` / `.md` (primary p_decoy vs. the
frozen p_candidate=16/69=23.2%, matched cluster-bootstrap CI, risk
difference/ratio, the pre-registered interpretation-table verdict) and
`decoy_gate_audit.csv` (stage decomposition: requested -> 5-poses-returned
-> geometry-valid -> catalytic-contact, decoys only, both receptor
states -- answers secondary question 2, "which component rejects the
decoys"). Smoke-tested end-to-end against fabricated data (logic verified,
not real results) before handoff.

**4. Size-bias checks** are included in step 3's output
(`size_bias_checks`: Spearman CNNaffinity-vs-HAC, and a logistic
`pass ~ HAC + cLogP` model). Pass-rate-by-quartile (the protocol's
secondary visual check) is not scripted -- `decoy_panel_results/
candidate_results.csv` joined to `property_matched_decoys.csv` on
`decoy_chembl_id` has everything needed for a quick quartile table if you
want it.

**5. Reranker sensitivity (optional, subordinate)**: rerun scoring with
whatever CNN_VS / minimized-affinity reranking logic the primary screen
already used, on the same decoy poses -- do not select a reranker because
it produces the lowest decoy rate; report all pre-specified alternatives
and keep native CNNscore rank-1 as primary, exactly as the primary 16/69
screen already does.

## Do not touch the frozen primary or sensitivity files

Every script here (`prepare_candidate_screen_ligands.py`,
`run_candidate_screen_gnina.py`, `score_candidate_screen.py`) defaults to
the frozen primary paths when its override flags are omitted -- always
pass the `decoy_panel_v1.0/...` paths explicitly, exactly as shown above.
Verified this session: none of the frozen primary
`candidate_screen_v1.0/{candidate_manifest.csv, ligand_microstate_manifest.csv,
docking_input_ligands/}` or the earlier `sensitivity_rerun/` files changed
while building this panel (`git status` clean on those paths throughout).

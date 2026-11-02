# Experimental-validation panel and assay plan v1.0 (amended v1.1, corrected v1.1.1)

Status: **frozen before any wet-lab data exists**. This document specifies which
compounds get tested, in what order, with what assays, and what would count as a
pass/fail *before* any experimental result is available, per this project's
standing pre-registration discipline (see `redocking_protocol_v1.0.json` and
`downstream_gcase_screening_protocol.md` for the same discipline applied to the
two prior computational stages). No result exists yet for anything in this
document -- it is a plan, not a report. DecisionBench-DD's own computational
contribution ends at this panel's design; execution requires a wet lab this
project does not have.

Timeline: v1.0 frozen 2026-08-26; v1.1 amended 2026-08-26 (same day -- v1.0's
own text had a mechanistic self-contradiction caught before any external
distribution); v1.1.1 corrected 2026-08-26T23:31:21Z (UTC, per external
review; v1.1's changelog had mislabeled its own amendment date one day into
the future). Compound membership (Tranche 1/Tranche 2) has never changed
across any of these revisions.

## v1.1.1 amendment log (2026-08-26T23:31:21Z UTC, pre-data -- compound membership unchanged)

External review of v1.1 confirmed the panel membership and overall assay
architecture as scientifically acceptable, and found eight further pre-data
corrections, all applied below:

1. Ambroxol is a **mixed-type**, pH-dependent GCase inhibitor, not a
   competitive inhibitor -- the primary study (Maegawa et al.) explicitly
   reports mixed-type inhibition; every "competitive inhibitor" occurrence
   below is corrected to "mixed-type, pH-dependent inhibitor."
2. **N370S and N409S are the same variant** (GBA1 c.1226A>G,
   p.Asn409Ser), under legacy mature-protein numbering (N370S) vs. HGVS
   numbering including the 39-residue signal peptide (N409S) respectively --
   not two candidate variants. Every "N370S (and/or N409S)"-style phrasing
   below is corrected to name the one variant under both conventions.
3. Section 3a previously listed *what* to pre-register without actually
   specifying values -- now specifies concrete defaults (replicate counts,
   randomization/blinding, curve model, minimum effect size, CI/alpha,
   multiple-comparison correction, outlier/QC rules), still adjustable per
   section 6 but no longer an open checklist.
4. The Tier 1->Tier 2 cytotoxicity gate ("CC50 >= 10x IC50/EC50") was
   undefined for a compound with a positive stabilization signal (assay 3a)
   but no measurable catalytic modulation (assay 3b) -- now branches
   explicitly by which signal a compound actually shows.
5. The overall-pass criteria said "ALL must be satisfied" while separately
   describing the hepatocyte-stability bar as non-excluding -- a direct
   contradiction. Resolved by moving hepatocyte stability out of the
   mandatory set into an explicit, tracked optimization flag.
6. PAMPA-BBB measures passive permeability only and cannot produce a
   P-gp/BCRP efflux ratio -- CNS assessment now explicitly separates PAMPA-BBB
   (passive) from a required MDCK-MDR1 (P-gp) and BCRP-competent (or
   dual-transfected) assay (transporter efflux).
7. hERG/cellular-assay language tightened: the 30x hERG index must be
   computed from a validated patch-clamp IC50, not the thallium-flux triage
   signal; "GBA1-specific lysosomal activity" is now operationally defined
   (CBE-inhibitable-fraction or equivalent selective-substrate method);
   fibroblast donor/genotype/passage/authentication/mycoplasma status and
   exact treatment/washout durations are now explicitly required in the
   executing lab's SOP annex rather than left implicit.
8. Provenance/wording: this document's own v1.1 amendment date was
   mislabeled 2026-08-27 (one day in the future relative to when it was
   actually written) -- corrected to the real UTC timestamps above. The
   Tranche-1 table's "GM_035: clean ADMET" and "GM_054: negative control"
   language had already been corrected in v1.1; this round additionally
   corrected the companion README's stale "docking outputs...are
   intentionally absent" sentence (docking has long since completed) and
   aligned its patent-membership summary line with the narrower wording
   already used in `patent_membership.md` itself.

## v1.1 amendment log (2026-08-26, pre-data -- compound membership unchanged)

External review caught a real mechanistic self-contradiction in v1.0: section 4
of this same document already stated Ambroxol shows "weaker **inhibition** at
acidic pH" (pH-dependent *inhibitor* pharmacology), while section 2/3's Tier 1
gate required "statistically significant GCase **activation**" at neutral pH.
These cannot both be true. Per the primary literature on Ambroxol and GCase
(Maegawa et al., cited in `downstream_gcase_screening_protocol.md` section 9,
https://pmc.ncbi.nlm.nih.gov/articles/PMC2749124/), Ambroxol is a mixed-type,
pH-dependent **inhibitor** of GCase in acute biochemical assays (reported
approximate IC50 3.7-8.1 uM at pH 6.7, ~31 uM at pH 5.6, ~810-950 uM at pH 4.7,
no inhibition at pH 4.3 -- consult the primary source for exact values before
using them to size an assay), while its pharmacological-chaperone effect
(increased lysosomal GCase abundance/activity) is a separate, slower, cell-based
phenomenon from stabilizing the enzyme during ER folding/trafficking -- not the
same signal as acute enzymatic activation. A v1.0 gate requiring acute
neutral-pH activation would have rejected Ambroxol itself and any genuine
Ambroxol-like chaperone. This is corrected below (assay 3 replaced, gate
reworded) without touching Tranche 1/Tranche 2 compound membership, which the
review separately confirmed as defensible and unaffected by this issue.

Also corrected in v1.1, all pre-data: enzyme-source specificity (recombinant
protein vs. lysate), 4-MUG assay protocol detail, an orthogonal natural-substrate
confirmation step, explicit cellular-rescue endpoints and washout requirement,
patient-fibroblast-as-primary-model language, a full statistical
pre-registration section, an analytical (not nephelometry-only) solubility
method, a CNS-specific permeability assay separate from Caco-2, a renamed hERG
index (no unearned "regulatory margin" framing), a corrected assay execution
sequence, and several wording fixes flagged below inline. See
`git log -- decisionbench_dd_configs_v1.0/candidate_screen_v1.0/experimental_validation_panel_v1.0.md`
for the pre-amendment v1.0 text.

## 1. Relationship to the frozen computational funnel

All 16 primary candidate-screen passers (`candidate_screen_results/summary.md`)
remain qualified; nothing here removes or downgrades any of them. This document
selects a **first experimental tranche of 6** for practical reasons (assay cost,
compound availability, throughput), per the review recommendation that produced
this priority order. The other 10 are an explicit **Tranche 2 reserve**, not
excluded -- if resources allow, they follow the same protocol below unchanged.

**Tranche-1 selection order is a multi-objective panel priority, NOT the
original CNNaffinity-first triage rank** (`candidate_screen_results/primary_candidate_triage.csv`).
The two orderings differ and both are reported below to avoid the ambiguity a
single "Rank" column previously created:

| Panel priority | Candidate | Tool | Original triage rank (CNNaffinity desc) | Role | Why selected |
| ---: | --- | --- | ---: | --- | --- |
| 1 | GM_035 | genmol | 3 | Comparatively balanced predicted profile | CNNaffinity 7.017, ligand-efficiency proxy 0.351, no invalid ADMET predictions -- "balanced" relative to the rest of the panel, not "clean": predicted hERG (0.766) is still elevated and must be tracked, not treated as resolved. |
| 2 | GM_015 | genmol | 1 | Binding-efficacy anchor | Highest CNNaffinity of all 16 (7.370); tests whether top computational affinity translates to real potency despite its weaker predicted solubility/clearance profile. |
| 3 | MM_002 | molmim | 4 | Orthogonal-generator representative | The sole MolMIM passer -- included to keep a MolMIM-derived chemotype in the experimental funnel, but **n=1 cannot support a statistically meaningful generator-level (GenMol-vs-MolMIM) efficacy comparison**; treat any MM_002 result as a single data point about that compound, not as evidence about MolMIM as a generator. |
| 4 | GM_034 | genmol | 8 | Ambroxol-like anchor | Smallest, most Ambroxol-proximal analogue (MW 392, cLogP 3.43) among the panel; a mechanistic bridge to the reference compound. |
| 5 | GM_054 | genmol | 2 | Prediction-challenge comparator | Second-highest CNNaffinity (7.060) but a near-zero pH-sensitivity delta (-0.028, the only panel member NOT predicted to favor the neutral state) -- included to directly challenge the pH-dependence hypothesis below with a compound predicted NOT to fit it, not as a validated negative control (no wet-lab data yet exists to validate anything). Also the panel member with the invalid (negative) predicted hepatocyte clearance, making it the priority case for real metabolic-stability data. |
| 6 | GM_057 | genmol | 9 | Low-toxicity / pH-sensitivity lead | Lowest hERG (0.352) and AMES (0.126) risk of the panel, plus the single largest neutral-vs-acidic CNNaffinity delta of all 16 candidates (+0.935) -- the strongest computational candidate for testing genuine Ambroxol-like pH-dependent chaperone behavior, traded off against reduced predicted BBB/HIA. |

### Compound identity must be frozen before any assay (new in v1.1)

The canonical SMILES in `candidate_manifest.csv` do not specify absolute
stereochemistry, and several panel members have multiple stereocentres. The
docked/scored panel and the physical panel are not the same thing until each
compound's identity is pinned down. Before synthesis or procurement, record for
every Tranche-1 compound (and controls):

- Exact stereoisomer synthesized/procured, or an explicit statement that the
  material is a racemic/diastereomeric mixture (and which one).
- Salt form vs. free base.
- Purity threshold (e.g. >=95%) and the analytical method used to confirm it.
- LC-MS (mass confirmation) and NMR (structural identity) records, archived per
  compound.
- Stock solvent and concentration, and the maximum final DMSO percentage used
  in any assay (a standard assay-validity constraint, typically <=0.1-1% v/v
  depending on the assay -- confirm against each assay's own validated range).

This record is a prerequisite for every assay below, not an optional appendix;
an assay result for a compound whose stereochemistry/salt form/purity was not
recorded cannot be attributed to a specific, reproducible structure.

### Controls (every assay below, not just the panel)

| Control | Role |
| --- | --- |
| Ambroxol | Positive reference: the seed compound and a marketed pharmacological chaperone with pH-dependent enzymatic behavior (mixed-type, pH-dependent inhibitor, more potent near neutral pH, much less potent/inactive at acidic pH -- see the amendment log above) and separately reported cellular chaperone activity. Sets the expected pattern for every pH-dependence readout. |
| Isofagomine (IFM) | Mechanistically distinct active-site chaperone reference (the redocking benchmark's own reference ligand, PDB 3GXF) -- distinguishes "any chaperone effect" from "an Ambroxol-like allosteric/pH-dependent effect" specifically. |
| Vehicle (DMSO, matched to test-compound stock concentration) | Negative control for every cell-based and biochemical assay. |
| Assay-specific positive controls (assigned per assay, not by this project): a validated hERG blocker for the hERG assay, a known CYP substrate for microsomal-stability LC-MS/MS method validation | Standard assay-quality controls; not scientific comparators for this project's compounds. Left to the executing lab's existing validated protocols rather than specified here. |

## 2. Assay tiers

Two tiers, cheapest/highest-throughput first, so a compound only consumes
expensive assay time (cell-based chaperone rescue, hERG, microsomal/hepatocyte
LC-MS/MS, CNS/oral permeability) after clearing identity confirmation,
solubility, cytotoxicity, and basic biochemical pharmacology.

### Tier 1 (run on all 6 panel candidates + Ambroxol + IFM + vehicle)

1. **Analytical solubility**, pH 7.4 and pH 5.0. Kinetic (nephelometric/
   turbidimetric) solubility alone is not sufficient to certify the
   concentrations used in assays 2-3: confirm the actual dissolved
   concentration by an analytical method (LC-UV or LC-MS) at the nominal test
   concentrations, not turbidity onset alone. Directly follows up the
   in-silico solubility flags (`admet_predictions.md`): GM_015 has the panel's
   worst predicted solubility (log solubility -4.19) and is the priority case
   to confirm or refute experimentally.
2. **Cytotoxicity/viability**, 8-point dose-response (e.g. 0.1-100 uM,
   half-log spacing), 24-48 h exposure, in the same cell background used for
   Tier 2's chaperone-rescue assay (so the resulting therapeutic-index
   calculation in section 3 uses matched cells). Standard viability readout
   (e.g. CellTiter-Glo or MTT); report CC50 per compound.
3. **GCase binding/stabilization AND signed catalytic modulation across pH**
   (replaces v1.0's single "enzymatic activation" assay -- see amendment log):
   - **3a. Neutral-pH binding/stabilization.** Thermal-shift (DSF/nanoDSF) or a
     heat-inactivation protection assay against **purified recombinant
     GBA1 c.1226A>G, p.Asn409Ser (legacy N370S) GCase** -- N370S and N409S are
     the same single amino-acid substitution under two different numbering
     conventions (legacy mature-protein numbering vs. HGVS numbering including
     the 39-residue signal peptide), not two candidate variants to choose
     between; not cell lysate; lysate-based activity belongs
     in the Tier 2 cellular assay, not here, since lysate introduces
     uncontrolled matrix effects into a direct-binding readout. Report delta-Tm
     or retained activity after a defined thermal challenge, at neutral pH.
     This directly tests the chaperone-binding mechanism independent of any
     assumption about the sign of the acute catalytic effect.
   - **3b. Acute catalytic modulation**, dose-response, at BOTH pH 7.4
     (ER-like) and pH 5.0 (lysosomal-like), against the same purified
     recombinant enzyme, using 4-methylumbelliferyl-beta-D-glucopyranoside
     (4-MUG) with taurocholate included at a specified, validated
     concentration (required for GCase activity in this assay format), a
     fixed substrate concentration and reaction time, and a standardized
     alkaline stop solution before fluorescence reading (4-MU fluorescence is
     strongly pH-sensitive; an unstopped or inconsistently-stopped reaction is
     not comparable across pH conditions). Include compound-only
     (no-enzyme) fluorescence/absorbance controls to rule out intrinsic
     compound fluorescence or quenching. Fit concentration-response curves
     **without assuming a sign**: report inhibition IC50 where the compound
     inhibits, activation EC50 where it activates, residual activity at the
     top tested concentration, and the maximal signed effect. For compounds
     showing inhibition, additionally report the pH-selectivity ratio
     IC50(pH 5.0) / IC50(pH 7.4) -- a larger ratio is consistent with an
     Ambroxol-like pattern (potent near-neutral inhibition, much weaker
     lysosomal inhibition), which is the actual experimental analogue of this
     project's docking-derived `delta_cnnaffinity_neutral_minus_acidic` proxy
     (`candidate_screen_results/candidate_results.csv`), not a same-signed
     "activation ratio" as v1.0 stated.
   - **Confirm any Tranche-1 finalist advancing past Tier 1 with an orthogonal
     natural-substrate assay** (e.g. a glucosylceramide-based readout) before
     relying on the fluorogenic-substrate result alone -- 4-MUG inhibition
     does not always reproduce native-substrate pharmacology.

### Tier 2 (only for candidates passing the Tier 1 gate in section 3)

4. **Cellular chaperone-rescue assay**, with explicit endpoints (v1.0's
   "activity and/or maturation" was not specific enough to execute
   consistently):
   - Primary endpoint: **GBA1-specific** lysosomal enzymatic activity measured
     AFTER a defined compound washout (not while compound is still present in
     the assay well, to separate a genuine chaperone/trafficking effect from
     residual direct enzyme engagement). Operationally define
     "GBA1-specific": total lysosomal beta-glucosidase activity minus the
     conduritol-B-epoxide (CBE)-inhibitable fraction (CBE is a
     GBA1-selective irreversible inhibitor; the CBE-sensitive signal is the
     GBA1 component, isolating it from GBA2/GBA3 background activity in the
     same lysate), or an equivalent validated selective-substrate/
     inhibitor-subtraction method -- do not report raw total
     beta-glucosidase signal as if it were GBA1-specific.
   - Secondary endpoint: mature/Endo-H-resistant GCase abundance (e.g. by
     Western blot glycoform shift) and lysosomal colocalization (e.g. by
     immunofluorescence against a lysosomal marker).
   - Required design: multi-dose treatment, a fixed treatment duration, and
     the washout step before lysate measurement/imaging, for every compound
     and control. Exact treatment and washout durations, and the fibroblast
     donor/genotype, passage-number range, line-authentication method, and
     mycoplasma-testing status, must be frozen in the executing lab's SOP
     annex before Tier 2 begins (this document specifies the endpoints and
     design constraints; it does not substitute for that lab-specific SOP).
   - **Primary model: GBA1 p.Asn409Ser/p.Asn409Ser (legacy N370S/N370S)
     patient-derived fibroblasts.** An engineered N409S-GCase-expressing line
     may be used for assay development or as a secondary/orthogonal model,
     but is not interchangeable with patient cells for the primary claim.
5. **hERG counterscreen.** Thallium-flux (or an equivalent
   fluorescence-based first pass) is **triage only** -- it selects which
   compounds proceed to concentration-response patch-clamp, it does not
   itself produce the potency value used in the section 3 hERG index.
   **The 30x hERG-to-cellular-efficacy index must be computed from a
   validated automated- or manual-patch-clamp IC50**, not from the triage
   assay's signal. Directly motivated by `admet_predictions.md`'s predicted
   hERG liabilities -- GM_054 (0.919) and, to a lesser extent, GM_034 (0.857)
   are the priority cases; GM_057 (0.352) is the panel's lowest-risk
   comparator, i.e. this assay is itself a test of whether the ADMET-AI hERG
   predictions track real electrophysiology across the panel's predicted
   range, not only a safety gate.
6. **Metabolic stability**, human liver microsomes AND cryopreserved
   hepatocytes in parallel (LC-MS/MS parent-compound depletion), report
   in-vitro t1/2 and CLint for both matrices. GM_054 is the priority case: its
   predicted hepatocyte clearance is negative (`Clearance_Hepatocyte_AZ_valid
   = False` in `admet_predictions.csv`), a physically impossible model output
   flagged as an extrapolation artifact rather than reinterpreted as good
   stability -- real data is the only way to resolve what its actual
   clearance is.
7. **Permeability, oral AND CNS separately, with passive permeability and
   transporter efflux ALSO reported separately within CNS** (v1.0 conflated
   several distinct measurements):
   - Oral/intestinal: Caco-2 bidirectional (Papp A-to-B and B-to-A, efflux
     ratio).
   - CNS passive permeability: PAMPA-BBB. This measures passive diffusion
     across an artificial phospholipid membrane ONLY -- it contains no
     transporters and cannot produce a P-gp or BCRP efflux ratio; do not
     report a PAMPA-BBB result as if it characterized transporter effects.
   - CNS transporter efflux: a separate cell-based assay is required for
     this -- MDCK-MDR1 (or equivalent P-gp-transfected monolayer) for P-gp
     efflux ratio; BCRP efflux requires its own BCRP-transfected line or a
     dual-transfected MDCK-MDR1/BCRP system, not assumed covered by an
     MDR1-only line. Required given the GBA1/Parkinson's indication's
     dependence on CNS exposure; PAMPA-BBB alone says nothing about
     transporter-mediated efflux, and Caco-2 alone says nothing about brain
     penetration.
   - GM_057's comparatively low predicted BBB (0.540) and HIA (0.784) make it
     the priority case across all three permeability/efflux assays.

### Tier 3 (beyond this document's scope, named for completeness)

8. **Neuronal validation** (e.g. patient-iPSC-derived dopaminergic neurons or
   an equivalent neuronal model) before any in-vivo progression decision.
   Not specified further here -- this document's scope ends at Tier 2; a
   neuronal-model protocol would be its own frozen amendment once a compound
   reaches this stage.

## 3. Decision gates

Stated as defaults with an explicit rationale, not as validated clinical
thresholds -- the executing lab should adjust for its own assay
characteristics, but should record and justify any deviation rather than
silently changing the gate after seeing data, per this project's amendment
policy (section 6). Every gate below also requires the full statistical
pre-registration in section 3a before execution.

**Tier 1 -> Tier 2 gate** (a compound must satisfy ALL of the following to
advance). The cytotoxicity criterion is branch-aware (v1.1.1 fix: v1.1's
"CC50 >= 10x IC50/EC50" was undefined for a compound that shows a
stabilization signal in 3a but no measurable modulation in 3b):
- Analytically-confirmed solubility at the Tier 1 assay-3 test concentration
  is within 3x of nominal (i.e. not so poorly soluble that the biochemical
  read is confounded by precipitation).
- Cytotoxicity therapeutic index, branch depending on which Tier 1 assay 3
  signal the compound actually shows:
  - **Catalytic modulators** (assay 3b shows a fitted IC50 or EC50 at either
    pH): CC50 (assay 2) >= 10x that IC50/EC50, at whichever pH gives the more
    potent value.
  - **Stabilization-only candidates** (a positive assay-3a thermal-shift/
    protection signal with no fitted assay-3b IC50/EC50, i.e. no measurable
    acute catalytic effect): CC50 >= 10x the stabilization assay's effective
    concentration (e.g. the concentration giving half-maximal delta-Tm), OR,
    if that concentration is not well-defined, CC50 >= 10x the maximum
    concentration planned for the assay-4 cellular exposure.
- **Neutral-pH engagement or stabilization** (a positive thermal-shift/
  protection signal in assay 3a, OR a defined minimum inhibitory/activating
  potency in assay 3b at pH 7.4) **plus acceptable residual catalytic
  activity at acidic pH** (assay 3b at pH 5.0 does not show potent inhibition
  at the concentrations relevant to the neutral-pH signal) -- corrected in
  v1.1 from v1.0's requirement of neutral-pH *activation* specifically (see
  amendment log). This phrasing does not presuppose whether a genuine
  Ambroxol-like compound will show inhibition or activation acutely; it
  requires evidence of neutral-pH engagement, of either sign, that plausibly
  relaxes at acidic pH. "Positive signal" / "defined minimum potency" /
  "acceptable residual activity" are quantified in section 3a below.

**Overall pass, for prioritizing beyond this panel** (e.g. into Tier 3 or a
synthesis-scale-up decision). v1.1.1 fix: v1.0/v1.1 said "ALL" criteria are
required while simultaneously describing the hepatocyte-stability criterion
as non-excluding -- a direct contradiction. Resolved by moving hepatocyte
stability OUT of the mandatory set into an explicit optimization flag, since
early-discovery metabolic-stability shortfalls are routinely addressable by
later formulation/analogue work and are not, by themselves, a reason to stop
investigating an otherwise-promising compound at this stage:

*Mandatory (ALL required):*
- Positive chaperone rescue in patient-derived cells (assay 4, primary
  endpoint), not just Tier 1 biochemical engagement.
- **Early-discovery hERG-to-cellular-efficacy index** (computed from a
  validated patch-clamp IC50, not the thallium-flux triage signal -- see
  assay 5): hERG IC50 at least 30x the cellular EC50 from assay 4. Renamed
  from v1.0's "hERG safety margin" -- this is a useful internal
  discovery-stage index, not a regulatory safety margin; regulatory hERG
  interpretation compares hERG potency against projected unbound systemic
  exposure and reference compounds, which do not exist yet for any of these
  compounds. Reserve regulatory-margin language until real exposure estimates
  exist.
- Oral (Caco-2 Papp), CNS passive (PAMPA-BBB Pe), and CNS transporter
  (MDCK-MDR1 P-gp efflux ratio, plus a BCRP-competent system's efflux ratio)
  all above the executing lab's own validated in-house cutoffs for a
  "permeable"/"non-effluxed" call -- deliberately not fixed here, since these
  cutoffs are assay-and-lab-specific (default illustrative cutoffs an
  executing lab commonly starts from: Caco-2 Papp(A-to-B) > 2x10^-6 cm/s,
  efflux ratio < 2; PAMPA-BBB Pe above the kit/vendor's own "CNS+" cutoff --
  confirm against the specific validated assay in use, do not treat these
  illustrative numbers as this project's own validated thresholds).

*Optimization flag (reported, tracked, but NOT gating overall pass):*
- Human hepatocyte t1/2 >= 30 minutes (a common early-stability screening
  bar). A compound below this bar is flagged as needing a
  metabolism-focused follow-up (e.g. site-of-metabolism identification,
  analogue design) before further investment, but is not excluded from
  Tier 3 consideration on this criterion alone.

### 3a. Statistical pre-registration

v1.1 listed the categories to specify; v1.1.1 actually specifies them as
defaults (still adjustable by the executing lab per section 6's amendment
policy, but a documented deviation is now required to change them, not free
choice at execution time):

- **Replicate counts**: n=3 independent biological replicates (each from a
  separate cell passage / separate enzyme preparation / separate compound
  dilution from stock), each run in n=3 technical replicates (same
  preparation, same plate or matched plates), for every assay in section 2.
- **Randomization/blinding**: compound identity coded (not visible to the
  operator) on every plate map; plate position of each compound/control
  randomized per biological replicate, not fixed across replicates.
- **Curve-fitting model**: four-parameter logistic (Hill equation), Hill
  slope floating unless the fit fails to converge, in which case refit with
  Hill slope constrained to 1.0 and report which was used. Acceptance
  criterion: R-squared >= 0.90 for a reportable IC50/EC50; curves below this
  are reported as "not determinable," not force-fit.
- **Minimum effect size**: >=20% change from vehicle for catalytic-modulation
  and cellular-rescue readouts; >=2 degrees C delta-Tm for the
  thermal-shift/stabilization readout -- below these, a statistically
  significant but sub-threshold effect is reported as such, not treated as a
  qualifying "positive" signal for the gates in this section.
- **Confidence interval and alpha**: 95% CI, alpha = 0.05, two-sided, for
  every significance claim referenced by the gates above.
- **Multiple-comparison correction**: Benjamini-Hochberg false-discovery-rate
  correction across the compound-by-condition comparisons within each assay
  (6 Tranche-1 compounds + Ambroxol + IFM, each vs. vehicle, at each pH/dose
  condition tested in that assay).
- **Outlier/QC rules**: plate-level Z'-factor >= 0.5 required for a plate to
  be used (enzymatic/biochemical assays); ROUT or Grubbs' test (alpha = 0.05)
  for technical-replicate outlier exclusion, applied consistently across all
  compounds and controls, never selectively.

## 4. The pH-dependence hypothesis this panel is specifically designed to test

> Ambroxol is a pH-dependent, mixed-type inhibitor of GCase in acute
> biochemical assays -- more potent near neutral pH, much less potent at
> acidic/lysosomal pH -- and separately increases lysosomal GCase abundance
> and activity in cells through a pharmacological-chaperone mechanism
> operating on a different (slower, trafficking-dependent) timescale than the
> acute enzymatic effect (see the amendment log above and
> `downstream_gcase_screening_protocol.md` section 9).

This panel was deliberately NOT chosen by CNNaffinity alone. GM_057, MM_002,
and GM_035 were selected in part for their strong positive in-silico
neutral-minus-acidic delta (+0.935, +0.679, +0.631 respectively), while GM_054
was included specifically because its delta is near zero (-0.028) --
a case predicted NOT to show an Ambroxol-like pH-dependent pattern, included
to challenge the hypothesis rather than only showcase compounds predicted to
confirm it. Tier 1 assay 3b's pH-selectivity ratio, compared against
Ambroxol's own ratio as the reference pattern, is the direct experimental test
of whether this project's docking-derived pH-sensitivity proxy
(`candidate_screen_results/summary.md`'s own
`ph_sensitivity_endpoint_status: exploratory_unvalidated` finding) tracks real
pH-dependent pharmacology at all. Per that same finding, this project's own
in-silico pH signal was NOT validated across controls (3/4 docking controls
disagreed with Ambroxol's direction) -- this experimental panel is what would
actually validate or refute it, not a restatement of the computational result.

## 5. Corrected assay execution sequence

1. Compound identity and analytical QC (stereochemistry, salt form, purity,
   LC-MS/NMR confirmation -- section 1).
2. Quantitative (analytical) solubility and cytotoxicity (Tier 1 assays 1-2).
3. GCase binding/stabilization (Tier 1 assay 3a).
4. Signed catalytic modulation across pH (Tier 1 assay 3b), plus orthogonal
   natural-substrate confirmation for finalists.
5. Cellular rescue after washout (Tier 2 assay 4).
6. hERG, metabolic stability, and CNS/oral permeability, in parallel (Tier 2
   assays 5-7).
7. Neuronal validation before any in-vivo progression decision (Tier 3,
   out of this document's scope).

## 6. Amendment policy

Same rule as every other frozen artifact in this project
(`redocking_protocol_v1.0.json:amendment_policy`,
`downstream_gcase_screening_protocol.md` section 1): compound membership in
Tranche 1, the assay list, and the decision-gate thresholds in section 3 may
not be changed after any wet-lab result exists for this panel. A gate may be
revised only for a documented technical reason discovered during assay
development, logged here with its rationale and a `made_before_seeing_results`
flag -- exactly the discipline used for the v1.1 amendment above, which was
made entirely pre-data. No compound may be added to or dropped from Tranche 1
because it performed well or badly in an assay -- underperformance moves a
compound's priority within Tranche 2 sequencing, it does not retroactively
rewrite Tranche 1's membership.

## 7. Explicit scope limits

- This project has no wet lab and does not execute any assay in this
  document. This is a specification for whoever does the experimental work,
  not a report of work performed.
- No numeric result in this document is a real measurement. Every EC50, IC50,
  CC50, delta-Tm, t1/2, and Papp mentioned above is a placeholder role name
  for a measurement that does not yet exist.
- The exact Maegawa et al. IC50 figures quoted in the amendment log above are
  reproduced from external review's citation of the primary literature, not
  independently re-derived by this project; consult the primary source
  directly before using them to size any assay.
- The decision-gate thresholds in section 3 are reasonable field defaults,
  not validated against this specific chemotype or target; the executing lab
  is expected to review and, if needed, adjust them before running anything,
  and to record any change per section 6.

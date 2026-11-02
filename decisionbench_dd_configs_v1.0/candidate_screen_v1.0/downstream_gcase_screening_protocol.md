# DecisionBench-DD downstream GCase candidate screen v1.0

Status: **frozen before candidate docking**  
Scope: compare downstream structural-prioritization yield for the chemically qualified GenMol and MolMIM outputs.

## 1. Frozen population

- GenMol: 66 qualified unique candidates from 300 requested outputs.
- MolMIM: 3 qualified unique candidates from 300 requested outputs.
- Total generated candidates to dock: 69.
- Controls, excluded from generator denominators: Ambroxol, isofagomine (3GXF/IFM), IMX8 (6Q1N), and norIMX8 (6Q1P).
- Candidate membership is defined only by `candidate_manifest.csv`; it must not be changed after docking scores are visible.
- If a molecule occurs in more than one replicate, dock the molecular identity once and map the same result back to every retained replicate occurrence. The present qualified set contains no cross-replicate duplicate identities.

The chemical gate remains DecisionBench-DD v1.2: valid RDKit molecule; within-replicate isomeric-canonical deduplication; not exact Ambroxol; ECFP4/Morgan radius 2, 2,048 bits, Tanimoto 0.30 to <0.95; QED >=0.50; SA <=5.0; MW 200-550 Da; cLogP 0-5; TPSA <=100 A^2; no PAINS; and no new Brenk occurrence beyond the single seed-position dibrominated-core aniline.

## 2. Question and claim boundary

Primary question:

> After the same frozen chemical gates, what fraction of each generator's 300 requested outputs survives a seed-relative, neutral-pH GCase structural-prioritization proxy?

This is not an experimental binding, efficacy, or pharmacological-chaperone label. Docking scores are used only as within-target prioritization proxies.

## 3. Receptor states

| Track | PDB | Protein | Chain | Experimental pH | Role |
|---|---|---|---|---:|---|
| Primary | 3KEH | human N370S GCase | A | 7.4 | ER-like neutral-state screen |
| Secondary | 3KE0 | human N370S GCase | A | 5.4 | lysosome-like sensitivity analysis |

Use the deposited structures as distinct experimental receptor states; do not morph one structure into the other. RCSB identifies 3KEH as N370S GCase at pH 7.4 and 3KE0 as the acidic-pH structure.

Apply the same cleanup policy used in the completed 14-case redocking benchmark: retain the selected protein chain; remove crystallization additives, free ions, waters, and glycans under the frozen rules; preserve resolved protein heavy atoms; resolve alternate locations using the prior occupancy hierarchy; add hydrogens at the state-specific pH; and log every rebuilt or unresolved residue within 6 A of the search box.

## 4. Active-site box

Use the already selected 3GXF isofagomine reference instance (`IFM`) from the frozen redocking manifest.

1. Align the selected 3GXF receptor chain onto 3KEH chain A by protein C-alpha atoms.
2. Transform the deposited IFM coordinates with the same matrix.
3. Define the GNINA box as the transformed IFM heavy-atom extent plus exactly 6 A on each side.
4. Repeat the alignment and transfer independently for 3KE0 chain A.
5. Freeze the resulting numeric centers and dimensions before docking any generated molecule.

The IFM coordinates define the known active-site location only. No generated ligand is initialized from IFM or any crystal pose.

## 5. Ligand preparation

- Start from each manifest SMILES, not any previously generated 3D pose.
- Prepare one pre-selected dominant microspecies for pH 7.4 and one for pH 5.4 using the same pinned protonation workflow used in the corrected redocking run.
- Use a deterministic ETKDG embedding seed and MMFF minimization; record failures.
- Explicitly prevent protonation of nitrogen directly bonded to `S(=O)(=O)` unless independently justified.
- Preserve specified stereochemistry. Do not invent stereocentres at unspecified atoms.
- If no single dominant microspecies can be assigned, set `microstate_ambiguous=true`. The molecule remains in the primary denominator, but its pH-difference result is not interpreted.
- Archive the input SMILES, prepared SMILES, formal charge, atom mapping, and preparation log for each pH state.

## 6. GNINA execution

The engine, CNN model, binary/container digest, and atom-typing toolchain must be inherited byte-for-byte from the final 14-case GNINA redocking manifest. A `latest` image tag is prohibited.

Primary configuration per ligand-receptor pair:

```text
exhaustiveness = 8
num_modes      = 5
seed           = 42
cnn_scoring    = rescore
box            = frozen state-specific active-site box
receptor       = rigid
```

Run 69 candidates plus four controls against both receptor states: 73 x 2 = 146 docking jobs and 730 requested poses. A failed job remains a failure; it is not removed from a denominator. Do not rerun only failures under more favorable settings.

## 7. Pose selection and validity

- Preserve all five poses in native output order.
- Primary pose selector: highest native `CNNscore`; ties use higher `CNNaffinity`, then lower `minimizedAffinity`, then lower original pose rank.
- Apply the exact geometry-validity proxy and thresholds already frozen in the final redocking `summary.md`; do not call it official PoseBusters.
- Report both native Top-1 validity and whether any valid pose exists in Top-5.
- Active-site occupancy requires at least one ligand heavy atom within 4.5 A of a side-chain carboxylate oxygen of catalytic residue E235 or E340.

GNINA defines `CNNscore` as its pose-ranking output and `CNNaffinity` as its predicted affinity output. They must not be silently interchanged.

## 8. Primary structural-prioritization proxy

A candidate is a primary neutral-state structural pass only when all conditions hold:

1. the 3KEH job returns all five poses;
2. the native Top-1 pose passes the frozen geometry-validity proxy;
3. the Top-1 pose satisfies the catalytic-site occupancy rule; and
4. its `CNNaffinity` is greater than or equal to Ambroxol's `CNNaffinity` under the same 3KEH preparation and invocation.

No minimum `CNNscore` is added post hoc. `minimizedAffinity` and `CNN_VS`, when present, are sensitivity readouts rather than extra primary gates.

For generator `g`:

```text
Y_structural_proxy(g) =
  number of unique generated candidates passing chemistry and the neutral structural proxy
  / 300 requested generator outputs
```

Also report conditional retention:

```text
R_structural_given_chemical(GenMol) = passes / 66
R_structural_given_chemical(MolMIM) = passes / 3
```

Use exact binomial 95% confidence intervals. With only three MolMIM inputs, report the comparison descriptively and avoid a strong superiority claim.

## 9. pH-state sensitivity analysis

For candidates with interpretable microstates and valid active-site poses in both states:

```text
delta_CNNaffinity = CNNaffinity(3KEH, pH 7.4) - CNNaffinity(3KE0, pH 5.4)
```

Positive values are directionally consistent with stronger neutral-state engagement. This is an exploratory receptor-state docking proxy, not a binding free-energy estimate or evidence of lysosomal release.

Ambroxol is the assay sanity control. If Ambroxol does not show a positive delta under this protocol, the pH-difference endpoint is declared non-informative for the entire run; it is not repaired by changing thresholds, protonation choices, or receptor preparation after candidate results are inspected. The primary neutral-state endpoint remains reportable.

## 10. Bounded reranking sensitivity

Because the redocking benchmark found a near-native pose within GNINA Top-5 for 8/14 cases but ranked only 3/14 first, retain these pre-specified, non-fitted sensitivity selectors:

1. native `CNNscore` descending;
2. `CNN_VS` descending, if emitted by the pinned build;
3. `minimizedAffinity` ascending.

Report how each fixed selector changes redocking Success@1 and candidate structural yield. Do not fit weights, choose a selector on all 14 structures, or describe the best post-hoc selector as independently validated.

## 11. Advancement to ADMET

Rank primary passers by `CNNaffinity` descending, then `CNNscore` descending, then `minimizedAffinity` ascending, then candidate ID. Cluster passers by ECFP4 Tanimoto using a 0.60 similarity cutoff and select round-robin from clusters until at most 20 candidates are retained. Ambroxol is carried as a control and does not consume a candidate slot.

If 20 or fewer candidates pass, advance all. If none pass, report zero downstream yield; do not relax the frozen gate.

## 12. Required outputs

- `candidate_manifest.csv`
- `chemical_gate_audit.csv`
- `receptor_state_manifest.json`
- `ligand_microstate_manifest.csv`
- `docking_run_manifest.json`
- `pose_scores.csv` (one row per pose)
- `candidate_results.csv` (one row per candidate)
- `generator_funnel.csv`
- `summary.md`
- SHA-256 hashes for all inputs, configurations, and outputs

The result package must state that GNINA was chosen from secondary pose-recovery and validity evidence; the 14-case primary Success@1 comparison against cropped DiffDock-L was inconclusive.

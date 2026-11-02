# DecisionBench-DD GCase redocking summary

GNINA is box-conditioned (precise 6 A padding around the crystal ligand). 'diffdock' below is DiffDock-L with ligand-centered 15 A receptor cropping (see redocking_protocol_v1.0.json:diffdock.receptor_cropping) -- an approximation of pocket-conditioning, not equivalent to GNINA's box, and not native/uncropped DiffDock-L.

Pose-validity proxy (decisionbench_dd_docking/pose_validity.py; a simplified PoseBusters-style check, not the official PoseBusters suite): valid RDKit valences; every bond length in [0.7, 2.2] A; no non-bonded heavy-atom pair closer than 1.5 A (internal clash); no ligand-to-receptor heavy-atom pair closer than 1.5 A (protein clash, flat cutoff, not VDW-scaled). Does not check ring planarity or torsion-angle plausibility.

This was a targeted correction rather than an independent stochastic replicate. Under the pinned DiffDock-L container and invocation used here, repeated executions produced byte-identical poses across all 14 cases, and the interface exposed no seed control; consequently, stochastic uncertainty could not be estimated. This reproducibility is empirically observed under the tested environment, not a claim that DiffDock is inherently or universally deterministic -- identical outputs could reflect internal fixed seeding or deterministic execution in this specific image, and do not establish the behavior of every DiffDock deployment.

Formal-charge normalization was applied to 15 DiffDock poses before RMSD calculation (see n_poses_charge_artifact_fixed below and rmsd._fix_known_pose_charge_artifact). Programmatic comparison confirmed zero changes to atomic coordinates, connectivity, stereochemistry, or pose ranking.

## gnina
- Success@1 (2.0 A) = 21.4% (n=14, 0 failed)
- Success@5 (2.0 A) = 57.1%
- Median top-1 RMSD = 4.64 A
- Median best-of-5 RMSD = 1.55 A
- Top-1 pose geometry valid = 100.0%
- All scored poses geometry valid = 100.0%
  - allosteric (n=11): Success@1 = 27.3%, Success@5 = 54.5%
  - active_site_chaperone (n=3): Success@1 = 0.0%, Success@5 = 66.7%

## diffdock
- Success@1 (2.0 A) = 14.3% (n=14, 0 failed)
- Success@5 (2.0 A) = 14.3%
- Median top-1 RMSD = 4.26 A
- Median best-of-5 RMSD = 4.01 A
- Top-1 pose geometry valid = 78.6%
- All scored poses geometry valid = 64.3%
- 15 scored pose(s) had a known output-representation charge artifact corrected before RMSD scoring (see rmsd._fix_known_pose_charge_artifact; per_case_rmsd.csv's n_poses_charge_artifact_fixed column names exactly which cases).
  - allosteric (n=11): Success@1 = 9.1%, Success@5 = 9.1%
  - active_site_chaperone (n=3): Success@1 = 33.3%, Success@5 = 33.3%

# GNINA rerun (fresh embeddings) vs. frozen primary redocking result

Same receptor, box, and GNINA parameters (identical pinned image digest) as the frozen primary run; only the ligand's RDKit ETKDGv3 starting conformer differs (redocking_rerun_v1.0/docking_input_ligands/, see embedding_reproducibility_report.md for the per-case coordinate deltas).

- Frozen Success@1 = 3/14; rerun Success@1 = 4/14
- Success@1 verdict changed for 3/14 cases
- Frozen Success@5 = 8/14; rerun Success@5 = 9/14
- Success@5 verdict changed for 1/14 cases

| PDB | Frozen Top-1 RMSD | Rerun Top-1 RMSD | Frozen S@1 | Rerun S@1 | Frozen S@5 | Rerun S@5 |
|---|---|---|---|---|---|---|
| 9F9Z | 0.89 | 0.48 | True | True | True | True |
| 9FA3 | 2.21 | 4.88 | False | False | False | False |
| 9FA6 | 5.89 | 5.86 | False | False | True | True |
| 9FAD | 6.04 | 7.76 | False | False | True | True |
| 9FAL  * | 5.24 | 4.90 | False | False | False | True |
| 9FAY | 5.56 | 6.30 | False | False | False | False |
| 9FAZ | 0.88 | 0.89 | True | True | True | True |
| 9FB2 | 7.27 | 7.57 | False | False | True | True |
| 9FDI ** | 1.53 | 5.56 | True | False | True | True |
| 8P3E | 4.17 | 5.42 | False | False | False | False |
| 8P41 | 5.11 | 5.74 | False | False | False | False |
| 3GXF ** | 3.43 | 1.71 | False | True | True | True |
| 6Q1N ** | 8.73 | 1.96 | False | True | True | True |
| 6Q1P | 3.40 | 2.79 | False | False | False | False |

`**` = Success@1 verdict changed, `*` = only Success@5 verdict changed.

Conclusion: the primary 14-complex redocking benchmark's GNINA arm is **not robust** to RDKit ETKDGv3 embedding non-determinism -- the same risk found in the decoy panel transfers here. Table 2/10's frozen numbers remain the reported primary result (single fixed realization, per the original protocol), but should be read as one draw from a run-sensitive process, not an exact reproducible point estimate.
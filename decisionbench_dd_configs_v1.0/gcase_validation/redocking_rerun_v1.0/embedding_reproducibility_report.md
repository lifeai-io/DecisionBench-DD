# Primary 14-complex redocking benchmark: embedding-reproducibility check

Re-runs the frozen protonation-selection + RDKit ETKDGv3 embedding pipeline (prepare_ligands.py's pick_variant/embed_ligand, unchanged) in a fresh process, writing output to redocking_rerun_v1.0/ without touching the frozen docking_input_ligands/, reference_ligands/, or gcase_validation_set_v1.0.json. Tests whether the same ETKDGv3 non-determinism found in the decoy panel (GM_009, up to 1.70 A despite randomSeed=42) also affects the primary 14-case set.

- Protonated-SMILES selection changed: 0/14
- Embedded coordinates differ (>=1e-6 A) from the frozen input: 14/14
- Max coordinate delta across all 14 cases: 10.493 A

| PDB | SMILES changed | Embed OK | Max delta, all atoms (A) | Max delta, heavy atoms (A) |
|---|---|---|---|---|
| 9F9Z | False | True | 0.0138 | 0.0107 |
| 9FA3 | False | True | 0.2791 | 0.2253 |
| 9FA6 | False | True | 10.493 | 8.4759 |
| 9FAD | False | True | 4.4925 | 3.8638 |
| 9FAL | False | True | 2.5649 | 1.841 |
| 9FAY | False | True | 0.139 | 0.1251 |
| 9FAZ | False | True | 0.2956 | 0.2193 |
| 9FB2 | False | True | 2.0229 | 0.4231 |
| 9FDI | False | True | 0.151 | 0.1109 |
| 8P3E | False | True | 0.1736 | 0.1479 |
| 8P41 | False | True | 0.3913 | 0.3913 |
| 3GXF | False | True | 0.2584 | 0.209 |
| 6Q1N | False | True | 0.4546 | 0.354 |
| 6Q1P | False | True | 5.1249 | 3.0352 |

DiffDock-L is out of scope: it consumes docking_input_protonated_smiles directly (a bare SMILES string), never the embedded conformer, so this risk cannot transfer to its arm regardless of the result above. Only GNINA's `-l` input depends on the embedded conformer.

If any case shows a nonzero coordinate delta, GNINA must be re-run on the freshly-embedded ligands in redocking_rerun_v1.0/docking_input_ligands/ (receptor and box unchanged) to test whether Success@1/5 and per-case RMSD change relative to the frozen Table 2/10 result -- see decisionbench_dd_docking/RUNNING_ON_GPU_INSTANCE.md for the rerun command.
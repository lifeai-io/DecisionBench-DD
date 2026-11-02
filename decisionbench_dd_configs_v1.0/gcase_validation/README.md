# GCase redocking validation set (Experiment B)

Frozen 14-structure GCase redocking set from `GCASE_VALIDATION_SET.md`. See
`gcase_validation_set_v1.0.json` for the full frozen record: inclusion/exclusion
criteria, the ligand-instance selection hierarchy and its RSCC/RSR/occupancy
audit trail, and three amendments resolved during preparation (documented
there, not silently applied):

1. `BAQ` (pyrrolidin-2-one, a crystallization-solvent fragment) reclassified
   as a non-LOI exclusion, resolving 9FAL to its one real ligand.
2. 9FA6's two different bound enantiomers (A1IBE vs A1IBG) resolved to
   **A1IBG** (better RSCC/RSR/occupancy) as the primary case, per user
   decision -- the frozen doc's selection hierarchy only covers multiple
   instances of the *same* ligand, not two different ones.
3. 3GXF's near-tied ligand copies resolved via RCSB's own `is_best_instance`
   flag rather than the ~0.001-0.005 RSCC/RSR gap, which is noise-level.

**A fourth, more serious issue was caught and fixed, not just noted:** the
first extraction pass wrote reference ligands as legacy PDB via BioPython's
`PDBIO`. Legacy PDB's residue-name field is only 3 characters; the nine `9F*`
ligand codes (e.g. `A1IBD`) are 5, so `PDBIO` wrote them anyway, silently
shifting every downstream fixed-width column -- including X/Y/Z coordinates --
by 2 characters. Verified directly against the file (reading the standard
column offsets returned garbled numbers) before anything downstream consumed
these files. Re-extracted from the (unaffected) mmCIF source as SDF instead,
with bond orders assigned from each ligand's RCSB canonical SMILES and
coordinates preserved from the deposited structure. See the JSON's
`amendments` for the full writeup. Receptor files were never affected --
standard amino acid codes always fit in 3 characters.

## Layout

```
raw_pdb/<PDB_ID>.cif                          Full mmCIF structure as downloaded from RCSB
receptors/<PDB_ID>_receptor_raw.pdb           Polymer residues only, not yet protonated
receptors_prepared/<PDB_ID>_prepared.pdb      Protonated (PDB2PQR 3.7.1, pH 7.4, AMBER) receptor
receptors_cropped_for_diffdock/<PDB_ID>_cropped.pdb   receptors_prepared/ cropped to 15 A around the docking-box center, for DiffDock's pocket-conditioning (it has no native box parameter)
reference_ligands/<PDB_ID>_<COMP_ID>.sdf      The one selected ligand instance, heavy atoms only, EXPERIMENTAL coordinates -- RMSD ground truth only, never given to either docking tool
docking_input_ligands/<PDB_ID>_ligand_input.sdf   Freshly 3D-embedded (RDKit ETKDGv3, seed 42) + pH-7.4-protonated (dimorphite-dl) ligand -- GNINA's actual -l input
docking_boxes.json                            Per-case GNINA box (6 A padding around the reference ligand's heavy-atom extent)
redocking_protocol_v1.0.json                  Frozen protocol: receptor/ligand prep, docking box, GNINA/DiffDock-L settings, RMSD method
gcase_validation_set_v1.0.json                Frozen case list + selection rationale + amendments + per-case file paths + docking SMILES
extraction_report_ligands.json                Audit log of the ligand extraction/bond-assignment step
ligand_docking_input_report.json              Audit log of the protonation-variant selection + 3D embedding step
receptor_cropping_report.json                 Audit log of the DiffDock pocket-cropping step
```

Legacy `.pdb` format is unavailable for the nine `9F*` structures' full
entries either -- RCSB only serves them as mmCIF, for the same reason
(`A1IBE`-style 5-character ligand codes don't fit the legacy format).
`.cif` was used for all 14 structures for consistency.

Actually running GNINA and DiffDock-L needs a GPU this dev environment
doesn't have -- see `decisionbench_dd_docking/RUNNING_ON_GPU_INSTANCE.md`.

## Embedding-reproducibility rerun (`redocking_rerun_v1.0/`)

Post-hoc, prompted by the decoy panel finding RDKit ETKDGv3 embedding
non-determinism despite a fixed seed. `redocking_rerun_v1.0/docking_input_ligands/`
holds a **freshly re-embedded** set of all 14 ligands (same frozen protonation
+ embedding logic, run again in a new process; see
`decisionbench_dd_docking/redocking_reembed_rerun.py`, already run -- no GPU
needed for this step). It does **not** replace or modify anything above:
`docking_input_ligands/`, `reference_ligands/`, and
`gcase_validation_set_v1.0.json` are untouched. See
`redocking_rerun_v1.0/embedding_reproducibility_report.md` for the per-case
coordinate deltas (all 14/14 cases differ from the frozen embedding; 5/14 by
more than 2 A).

**The GNINA-only rerun this motivates has been run** (DiffDock-L is
unaffected, since it consumes the SMILES string, not the embedded
conformer): `redocking_rerun_v1.0/docking_runs/gnina/` holds the rerun poses
(same pinned image digest as the frozen primary run) and
`redocking_rerun_v1.0/docking_results/` the rescored output. Result: GNINA's
Success@1 rose from the frozen 3/14 (21.4%) to 4/14 (28.6%), Success@5 from
8/14 (57.1%) to 9/14 (64.3%), with 3/14 complexes changing Success@1 verdict
-- see `redocking_rerun_v1.0/gnina_rerun_vs_frozen.md` for the full per-case
comparison. See `decisionbench_dd_docking/RUNNING_ON_GPU_INSTANCE.md`
section 5 for how this was run.

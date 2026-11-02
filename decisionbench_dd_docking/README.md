# decisionbench_dd_docking

GCase redocking benchmark (Experiment B). Companion to `decisionbench_dd_eval`
(the generator benchmark) -- same philosophy: freeze every parameter before
running anything, common downstream scoring regardless of which tool
produced a pose, full audit trail for every non-default decision.

## What's here

| File | Purpose |
| --- | --- |
| `rmsd.py` | Symmetry-aware, in-place docking-pose RMSD (`rdMolAlign.CalcRMS`, deliberately not `GetBestRMS` -- see its docstring). |
| `evaluate_docking.py` | CLI: scores GNINA/DiffDock pose SDFs against the frozen reference ligands, writes Success@1/@5 (overall + per site stratum). |
| `docker_utils.py` | Shared bind-mount / host-to-container path translation for the two docker-based runners below. |
| `run_gnina.py` | Runs dockerized GNINA (`gnina/gnina` image, `--gpus all`) over all 14 cases; run on your GPU instance. |
| `run_diffdock.py` | Runs the official `rbgcsail/diffdock` image (batch/CSV mode, not the NIM REST API) over all 14 cases; run on your GPU instance. |
| `RUNNING_ON_GPU_INSTANCE.md` | The only two GPU-dependent steps, spelled out. |

Frozen protocol, case list, prepared receptors/ligands, and docking boxes all
live in `decisionbench_dd_configs_v1.0/gcase_validation/` -- see that
directory's own README and `redocking_protocol_v1.0.json`.

## What already ran locally (no GPU needed) vs. what needs your GPU instance

Already done, frozen, and committed:
- Structure fetch, ligand-instance selection (`gcase_validation_set_v1.0.json`)
- Receptor protonation (PDB2PQR, pH 7.4) -> `receptors_prepared/`
- Ligand protonation (dimorphite-dl, pH 7.4) + 3D embedding (RDKit ETKDGv3) -> `docking_input_ligands/`
- Docking box computation (6 A padding) -> `docking_boxes.json`
- DiffDock pocket-cropping (15 A radius) -> `receptors_cropped_for_diffdock/`

Needs your GPU instance: actually running dockerized `gnina` and DiffDock-L's
inference (see `RUNNING_ON_GPU_INSTANCE.md`). `evaluate_docking.py` itself
needs no GPU and can run wherever the resulting pose SDFs end up.

## Tests

```
python -m unittest discover -s decisionbench_dd_docking/tests -p "test_*.py"
```

Tests use the real, already-frozen reference ligand SDFs (translated
programmatically to build synthetic "poses" at known RMSD) -- not real
GNINA/DiffDock output, which doesn't exist in this dev environment. The
critical test is `test_translation_is_not_silently_realigned_away`: it
verifies `CalcRMS` reports a uniform 3 A shift as ~3.0 A RMSD rather than
superposing it away to ~0, which is exactly the failure mode `GetBestRMS`
would have caused if used here by mistake.

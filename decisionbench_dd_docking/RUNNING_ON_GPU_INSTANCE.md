# Running GNINA / DiffDock-L on your GPU instance

Everything that doesn't need a GPU (structure fetching, ligand-instance
selection, receptor protonation, ligand protonation + 3D embedding, docking
box computation, DiffDock pocket-cropping) is already done and frozen under
`decisionbench_dd_configs_v1.0/gcase_validation/`. This doc covers only the
two steps that need to run on your GPU instance -- both via `docker run`,
matching your setup (official `gnina/gnina` image with GPU passthrough;
official `rbgcsail/diffdock` image, pulled per the DiffDock repo's own
Docker instructions).

## 1. Copy the repo onto the GPU instance

The scripts assume `decisionbench_dd_configs_v1.0/` and `decisionbench_dd_docking/`
live together under one repo root, mounted into the containers as a whole
(see `docker_utils.py`). Copy (or `git clone`) the full repo over.

`python -m decisionbench_dd_docking.*` needs only `rdkit` on the host/instance
(for building commands and merging DiffDock's output) -- GNINA and DiffDock's
own dependencies live inside their respective images.

## 2. GNINA

```bash
python -m decisionbench_dd_docking.run_gnina --out-dir docking_runs/ --dry-run   # sanity-check the 14 commands first
python -m decisionbench_dd_docking.run_gnina --out-dir docking_runs/
```

This runs, per case:

```bash
docker run --rm --gpus all -v <repo_root>:/workspace gnina/gnina:latest \
    gnina -r /workspace/.../receptors_prepared/<PDB_ID>_prepared.pdb \
          -l /workspace/.../docking_input_ligands/<PDB_ID>_ligand_input.sdf \
          --center_x ... --size_x ... --num_modes 5 --exhaustiveness 8 --seed 42 --cnn_scoring rescore \
          -o /workspace/docking_runs/gnina/<PDB_ID>_poses.sdf --log ...
```

If your image tag differs from `gnina/gnina:latest`, pass `--docker-image`.
If GPU passthrough isn't working, pass `--no-gpu` (GNINA falls back to
CPU-only CNN scoring, slower but functional). Every docking parameter (box,
`--num_modes`, `--exhaustiveness`, `--seed`, `--cnn_scoring`) is read from
`redocking_protocol_v1.0.json` and `docking_boxes.json` -- nothing is
hardcoded in the script. If you need to change a docking parameter, change it
there (and record why, per that file's own `amendment_policy`), not in the
script.

## 3. DiffDock-L (`rbgcsail/diffdock`)

```bash
docker pull rbgcsail/diffdock   # if you haven't already
python -m decisionbench_dd_docking.run_diffdock --out-dir docking_runs/ --dry-run   # sanity-check first
python -m decisionbench_dd_docking.run_diffdock --out-dir docking_runs/
```

This is verified against the actual image (gcorso/DiffDock repo, commit
`85c49b60d3e0b0182a59ee43a34a6d7036981284`, and its Dockerfile), not assumed
from the README prose -- the README's own single-complex-mode description
turned out to name a `--ligand` flag that doesn't exist (the real flag is
`--ligand_description`). Because of that, this script uses the fully-verified
**batch/CSV mode** instead: it builds one CSV with all 14 (or `--cases`
subset) rows and runs one docker invocation, equivalent to:

```bash
docker run --rm --gpus all -v <repo_root>:/workspace rbgcsail/diffdock \
    sh -c 'micromamba run -n diffdock python -m inference \
        --config default_inference_args.yaml \
        --protein_ligand_csv /workspace/docking_runs/diffdock_batch_input.csv \
        --out_dir /workspace/docking_runs/diffdock_raw \
        --samples_per_complex 5'
```

(No `cd` is needed -- the image's `WORKDIR` is already `/home/appuser/DiffDock`,
where `default_inference_args.yaml` lives. `micromamba run -n diffdock <cmd>`
is the correct non-interactive equivalent of `micromamba activate diffdock`;
it's confirmed to work in this exact image because the Dockerfile uses that
same pattern for its own build step.)

DiffDock writes `rank{N}_confidence{score}.sdf` for every rank, **plus** a
second, unsuffixed `rank1.sdf` duplicate of just the top pose.
`run_diffdock.py`'s `merge_ranked_sdfs()` deliberately reads only the
confidence-suffixed files (regex-matched, sorted by rank number) so that
duplicate doesn't get double-counted as an extra pose.

If your build of the image differs (different `WORKDIR`, env name, or output
naming), the things to change are `CONDA_ENV_NAME` and the `inference_cmd`
string in `run_diffdock.py`'s `main()` -- the CSV-building and output-merging
logic doesn't need to change.

Both runners also write `<out-dir>/<tool>/manifest.json` (skipped only in
`--dry-run`): resolved Docker image digest (not just the mutable tag),
sha256 of the protocol/case-list files actually read, this repo's git
commit, and per-case command/runtime/exit-status -- see
`decisionbench_dd_docking/provenance.py`. Keep it alongside the poses when
copying results back; it's what lets a later re-run be checked against this
one rather than trusted on the tag name alone.

## 4. Copy results back and score

Copy the `docking_runs/` directory (containing `gnina/` and `diffdock/`
subdirectories of `<PDB_ID>_poses.sdf` files, plus each tool's
`manifest.json`) back to wherever you're running the evaluator, then:

```bash
python -m decisionbench_dd_docking.evaluate_docking \
    --poses-dir docking_runs/ --out-dir docking_results/
```

This step needs no GPU and can run anywhere with RDKit installed. It produces
`docking_results/summary.md` (Success@1/Success@5 overall and per site
stratum, per `redocking_protocol_v1.0.json`'s `rmsd_scoring` section) and
`per_case_rmsd.csv` (full per-case, per-pose-rank audit trail).

## 5. Embedding-reproducibility rerun of the primary 14-case benchmark (GNINA only) -- DONE

**Status: complete.** Both the re-embedding (CPU) and the GNINA rerun (GPU,
run 2026-09-05, same pinned image digest as the primary run
`gnina/gnina@sha256:9da3dc6...`) have been executed and committed. Results:
GNINA's Success@1 rose from the frozen 3/14 (21.4%) to 4/14 (28.6%) and
Success@5 from 8/14 (57.1%) to 9/14 (64.3%), but these aggregates mask
larger per-case churn -- 3/14 complexes changed Success@1 verdict and 1/14
changed Success@5 verdict. See
`redocking_rerun_v1.0/gnina_rerun_vs_frozen.md` (built by
`decisionbench_dd_docking.compare_redocking_rerun`) for the full per-case
comparison, and manuscript Appendix D / Table 11 for the reported version.
**Conclusion: the primary redocking benchmark's GNINA arm is not robust to
this embedding non-determinism** -- no further action needed unless you want
to repeat the rerun with a different embedding draw. The steps below are
kept for reference/reproducibility.

Prompted by the decoy panel finding that re-embedding produced a different
conformer despite a fixed seed (GM_009, up to 1.70 A) -- diagnosed by
`decisionbench_dd_docking.diagnose_embedding_determinism` as reproducible
within one fixed environment (0.0 A across fresh-process invocations for
three cases), so the deployed pipeline's cross-occasion non-reproducibility
is established but its root cause is not -- `decisionbench_dd_docking.redocking_reembed_rerun`
(no GPU needed, already run and committed) re-embedded all 14 primary cases
fresh, into `decisionbench_dd_configs_v1.0/gcase_validation/redocking_rerun_v1.0/
docking_input_ligands/`, without touching any frozen file. Result: the chosen
protonated SMILES was unchanged in all 14 cases, but the embedded starting
conformer differed from the frozen input in all 14/14 cases (5/14 by >2 A,
max 10.49 A for 9FA6) -- see `redocking_rerun_v1.0/embedding_reproducibility_report.md`.

DiffDock-L is out of scope for the rerun below: it consumes the SMILES
string directly, never the embedded conformer (see `run_diffdock.py`'s
`build_batch_csv`), and is already established as byte-identical across
repeated executions (`docking_results/summary.md`). Only GNINA's `-l` input
depends on the embedded conformer, so only GNINA needs to be redocked to
test whether Table 2's Success@1/5 are robust to this:

```bash
python -m decisionbench_dd_docking.run_gnina \
    --ligand-dir decisionbench_dd_configs_v1.0/gcase_validation/redocking_rerun_v1.0/docking_input_ligands \
    --out-dir redocking_rerun_v1.0/docking_runs \
    --dry-run   # sanity-check the 14 commands first
python -m decisionbench_dd_docking.run_gnina \
    --ligand-dir decisionbench_dd_configs_v1.0/gcase_validation/redocking_rerun_v1.0/docking_input_ligands \
    --out-dir redocking_rerun_v1.0/docking_runs
```

Receptor, box, and every GNINA parameter are unchanged from the frozen
primary run -- only the ligand's starting conformer differs. Copy
`redocking_rerun_v1.0/docking_runs/` back and score with the existing,
unmodified evaluator (no GPU needed):

```bash
python -m decisionbench_dd_docking.evaluate_docking \
    --poses-dir redocking_rerun_v1.0/docking_runs/ --tools gnina \
    --out-dir redocking_rerun_v1.0/docking_results/
```

Compare `redocking_rerun_v1.0/docking_results/summary.md`'s GNINA
Success@1/5 directly against the frozen `docking_results/summary.md` (Table 2
in the manuscript: 21.4%/57.1%). Do not re-run DiffDock-L for this check --
it is structurally unaffected, per above.

## 6. Candidate-screen experiment (146 jobs, after the redocking benchmark)

Separate from the redocking benchmark above: docks the 69 chemically-qualified
generated candidates + 4 controls against 3KEH (pH 7.4) and 3KE0 (pH 5.4),
per `decisionbench_dd_configs_v1.0/candidate_screen_v1.0/downstream_gcase_screening_protocol.md`.
Receptor prep, box alignment, and ligand microstate prep are already done
(CPU-only, no GPU needed) -- this step is GNINA-only, no DiffDock track.

```bash
python -m decisionbench_dd_docking.run_candidate_screen_gnina --out-dir candidate_screen_runs/ --dry-run   # sanity-check the 146 commands
python -m decisionbench_dd_docking.run_candidate_screen_gnina --out-dir candidate_screen_runs/
```

The default `--docker-image` is pinned to the exact digest resolved for the
14-case redocking run (`docking_runs/gnina/manifest.json:docker_image_digest`),
not the mutable `gnina/gnina:latest` tag, per the protocol's "no latest tag"
rule -- this is what makes it provably the byte-identical image. Writes
`candidate_screen_runs/docking_run_manifest.json` (same provenance format as
`run_gnina.py`) plus `<3KEH|3KE0>/<ligand_id>_poses.sdf` and `.log` per job.
Copy `candidate_screen_runs/` back and score with
`decisionbench_dd_docking.score_candidate_screen` (no GPU needed).

# runs/

Real GenMol/MolMIM run outputs go here. This directory is gitignored except for
this file and `.gitkeep`-style placeholders — raw API responses are regenerable
but not meant to bloat the repo history; commit them deliberately if you want
them versioned.

Expected layout, one manifest + one raw response per replicate:

```
runs/
  genmol_replicate_01.manifest.json
  genmol_replicate_02.manifest.json
  genmol_replicate_03.manifest.json
  molmim_replicate_01.manifest.json
  molmim_replicate_02.manifest.json
  molmim_replicate_03.manifest.json
  raw/
    genmol_replicate_01.json   # raw NIM response, saved before any RDKit processing
    genmol_replicate_02.json
    genmol_replicate_03.json
    molmim_replicate_01.json
    molmim_replicate_02.json
    molmim_replicate_03.json
```

- Each `*.manifest.json` must follow `decisionbench_dd_configs_v1.0/run_manifest_template.json`
  (required fields: `tool`, `run_id`, `raw_response_file`, `requested_molecules`).
- `raw_response_file` is resolved relative to the manifest's own directory, e.g.
  `"raw/genmol_replicate_01.json"`.
- `tool` must be exactly `genmol` or `molmim`; the evaluator dispatches on that
  field, never on the filename.
- Save the raw API response verbatim (common_protocol.json rule: "Save raw
  response before any filtering") — the evaluator does its own RDKit
  canonicalization and scoring, so nothing needs to be pre-cleaned.

Once the six files are in place, run:

```
venv/bin/python -m decisionbench_dd_eval.evaluate_generators
```

which reads `runs/`, applies `decisionbench_dd_configs_v1.0/qualification_gates_v1.0.json`,
and writes `results/` (Table 1, Figure 2 scatter data, the Figure 4 funnel, and a
molecule-level CSV for the appendix).

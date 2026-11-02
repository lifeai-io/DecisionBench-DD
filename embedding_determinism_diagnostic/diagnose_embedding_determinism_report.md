# Embedding-determinism diagnostic

## Call-path facts

- **rdkit_version**: 2026.03.5
- **embedding_function**: AllChem.EmbedMolecule (not EmbedMultipleConfs)
- **randomSeed_set_explicitly_to**: 42
- **numThreads_default_ETKDGv3**: 1
- **numThreads_note**: numThreads only affects EmbedMultipleConfs; EmbedMolecule does not use it, so this parameter is not in play for this pipeline.
- **useRandomCoords_default**: False
- **enforceChirality_default**: True
- **pruneRmsThresh_default**: -1.0
- **post_embedding_optimization**: AllChem.MMFFOptimizeMolecule(mol, maxIters=2000)
- **overridden_from_ETKDGv3_defaults**: ['randomSeed']

## Reproducibility tests

- Within-process repeat (2 embeddings, same process): max delta = 0.0 A
- Cross-process repeats (5 fresh `python3` invocations): max deltas vs. the first = [0.0, 0.0, 0.0, 0.0] A (all identical)
- Comparison against committed frozen file `decisionbench_dd_configs_v1.0/gcase_validation/docking_input_ligands/9FA6_ligand_input.sdf`: delta = 10.493043292581994 A

If within-process and cross-process deltas are both 0, embedding is fully reproducible in THIS environment for this molecule. A nonzero delta against the frozen file then indicates the frozen file was produced under a different environment (RDKit build, OS-level math library, or hardware) at a different time -- not that RDKit's seeded embedding is inherently nondeterministic. This script cannot test 'only across machines' directly (this sandbox is one environment); that remains a disclosed, unconfirmed possibility, not a established cause.
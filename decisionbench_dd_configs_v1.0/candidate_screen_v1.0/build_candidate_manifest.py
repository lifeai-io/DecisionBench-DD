#!/usr/bin/env python3
"""Reproduce DecisionBench-DD v1.2 qualification and freeze docking inputs."""

from __future__ import annotations

import csv
import glob
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from rdkit import Chem, DataStructs, rdBase
from rdkit.Chem import Crippen, Descriptors, FilterCatalog, QED, rdFingerprintGenerator, rdMolDescriptors
from rdkit.Contrib.SA_Score import sascorer


SEED_SMILES = "C1=C(C(=C(C=C1Br)Br)N)CNC2CCC(CC2)O"
INPUT_GLOBS = {
    "genmol": "inputs/genmol_replicate_*.json",
    "molmim": "inputs/molmim_replicate_*.json",
}


def catalog(kind: FilterCatalog.FilterCatalogParams.FilterCatalogs):
    params = FilterCatalog.FilterCatalogParams()
    params.AddCatalog(kind)
    return FilterCatalog.FilterCatalog(params)


PAINS = catalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS)
BRENK = catalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.BRENK)
FPGEN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
SEED = Chem.MolFromSmiles(SEED_SMILES)
SEED_CANONICAL = Chem.MolToSmiles(SEED, isomericSmiles=True)
SEED_FP = FPGEN.GetFingerprint(SEED)
SEED_ANILINE_CORE = Chem.MolFromSmarts("[NH2]-c1c(Br)cc(Br)cc1")
ANILINE_N = Chem.MolFromSmarts("[NH2]-[c]")


def load_records(tool: str):
    records = []
    for path_str in sorted(glob.glob(INPUT_GLOBS[tool])):
        path = Path(path_str)
        payload = json.loads(path.read_text())
        molecules = payload["molecules"]
        if isinstance(molecules, str):
            molecules = json.loads(molecules)
        run = int(path.stem.rsplit("_", 1)[1])
        for returned_rank, item in enumerate(molecules, start=1):
            records.append(
                {
                    "tool": tool,
                    "run": run,
                    "returned_rank": returned_rank,
                    "raw_smiles": item.get("smiles", item.get("sample", "")),
                    "generator_score": item.get("score"),
                }
            )
    return records


def brenk_alerts(mol):
    return [entry.GetDescription() for entry in BRENK.GetMatches(mol)]


def inherited_alert_pass(mol, alerts):
    """v1.2 instance-aware seed-alert rule for this Ambroxol benchmark.

    The only allowed Brenk occurrence is the single primary aniline carried by
    the seed's dibrominated aromatic core. A second aniline instance, an aniline
    elsewhere, or any other Brenk alert fails.
    """
    if not alerts:
        return True
    if set(alerts) != {"aniline"}:
        return False
    return len(mol.GetSubstructMatches(ANILINE_N)) == 1 and mol.HasSubstructMatch(SEED_ANILINE_CORE)


def evaluate(tool: str):
    records = load_records(tool)
    seen_by_run = defaultdict(set)
    audit = []
    qualified = []
    stage_order = [
        "valid",
        "unique",
        "not_exact_seed",
        "similarity_band_0.30_to_0.95",
        "qed",
        "sa_score",
        "molecular_weight",
        "clogp",
        "tpsa",
        "no_pains",
        "chemically_qualified",
    ]
    counts = Counter()

    for record in records:
        row = dict(record)
        mol = Chem.MolFromSmiles(record["raw_smiles"]) if record["raw_smiles"] else None
        row.update({stage: False for stage in stage_order})
        row["failed_at"] = "valid"
        if mol is None:
            audit.append(row)
            continue

        row["valid"] = True
        counts["valid"] += 1
        canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
        row["canonical_smiles"] = canonical
        run_seen = seen_by_run[record["run"]]
        if canonical in run_seen:
            row["failed_at"] = "unique"
            audit.append(row)
            continue
        run_seen.add(canonical)
        row["unique"] = True
        counts["unique"] += 1

        if canonical == SEED_CANONICAL:
            row["failed_at"] = "not_exact_seed"
            audit.append(row)
            continue
        row["not_exact_seed"] = True
        counts["not_exact_seed"] += 1

        similarity = DataStructs.TanimotoSimilarity(SEED_FP, FPGEN.GetFingerprint(mol))
        qed = QED.qed(mol)
        sa = sascorer.calculateScore(mol)
        mw = Descriptors.MolWt(mol)
        clogp = Crippen.MolLogP(mol)
        tpsa = rdMolDescriptors.CalcTPSA(mol)
        alerts = brenk_alerts(mol)
        row.update(
            {
                "ecfp4_tanimoto": similarity,
                "qed_value": qed,
                "sa_value": sa,
                "mw_da": mw,
                "clogp_value": clogp,
                "tpsa_a2": tpsa,
                "brenk_alerts": ";".join(alerts),
            }
        )

        checks = [
            ("similarity_band_0.30_to_0.95", 0.30 <= similarity < 0.95),
            ("qed", qed >= 0.50),
            ("sa_score", sa <= 5.0),
            ("molecular_weight", 200 <= mw <= 550),
            ("clogp", 0 <= clogp <= 5),
            ("tpsa", tpsa <= 100),
            ("no_pains", not PAINS.HasMatch(mol)),
        ]
        failed = False
        for stage, passed in checks:
            if not passed:
                row["failed_at"] = stage
                failed = True
                break
            row[stage] = True
            counts[stage] += 1
        if failed:
            audit.append(row)
            continue

        if not inherited_alert_pass(mol, alerts):
            row["failed_at"] = "new_brenk_alert"
            audit.append(row)
            continue

        row["chemically_qualified"] = True
        row["failed_at"] = ""
        counts["chemically_qualified"] += 1
        qualified.append(row)
        audit.append(row)

    return records, audit, qualified, counts


def write_csv(path: Path, rows, fields):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = Path("candidate_screen_v1.0")
    output.mkdir(exist_ok=True)
    all_audit = []
    all_qualified = []
    summary = {
        "schema_version": "DecisionBench-DD_candidate_screen_inputs_v1.0",
        "seed_smiles": SEED_SMILES,
        "seed_canonical_smiles": SEED_CANONICAL,
        "rdkit_version": rdBase.rdkitVersion,
        "gates": {
            "valid": "RDKit MolFromSmiles succeeds",
            "deduplication": "within each generator replicate by isomeric canonical SMILES; first occurrence retained",
            "not_exact_seed": True,
            "ecfp4": {"radius": 2, "n_bits": 2048, "tanimoto_min_inclusive": 0.30, "tanimoto_max_exclusive": 0.95},
            "qed_min_inclusive": 0.50,
            "sa_max_inclusive": 5.0,
            "mw_da": [200, 550],
            "clogp": [0, 5],
            "tpsa_a2_max_inclusive": 100,
            "pains": "none",
            "brenk": "only the single seed-position dibrominated-core aniline occurrence is allowlisted",
        },
        "generators": {},
    }
    expected = {"genmol": 66, "molmim": 3}
    id_prefix = {"genmol": "GM", "molmim": "MM"}

    for tool in ("genmol", "molmim"):
        records, audit, qualified, counts = evaluate(tool)
        if len(qualified) != expected[tool]:
            raise RuntimeError(f"{tool}: expected {expected[tool]} qualified, reproduced {len(qualified)}")
        for index, row in enumerate(qualified, start=1):
            row["candidate_id"] = f"{id_prefix[tool]}_{index:03d}"
        all_audit.extend(audit)
        all_qualified.extend(qualified)
        summary["generators"][tool] = {
            "requested": len(records),
            "qualified_unique": len(qualified),
            "qualified_yield_of_requested": len(qualified) / len(records),
            "stage_counts": dict(counts),
        }

    candidate_fields = [
        "candidate_id", "tool", "run", "returned_rank", "canonical_smiles",
        "generator_score", "ecfp4_tanimoto", "qed_value", "sa_value",
        "mw_da", "clogp_value", "tpsa_a2", "brenk_alerts",
    ]
    audit_fields = [
        "tool", "run", "returned_rank", "raw_smiles", "canonical_smiles",
        "generator_score", "ecfp4_tanimoto", "qed_value", "sa_value",
        "mw_da", "clogp_value", "tpsa_a2", "brenk_alerts", "failed_at",
        "valid", "unique", "not_exact_seed", "similarity_band_0.30_to_0.95",
        "qed", "sa_score", "molecular_weight", "clogp", "tpsa",
        "no_pains", "chemically_qualified",
    ]
    candidates_path = output / "candidate_manifest.csv"
    audit_path = output / "chemical_gate_audit.csv"
    summary_path = output / "candidate_manifest_summary.json"
    write_csv(candidates_path, all_qualified, candidate_fields)
    write_csv(audit_path, all_audit, audit_fields)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")

    checksum_paths = [candidates_path, audit_path, summary_path]
    for extra_name in ("downstream_gcase_screening_protocol.md", "README.md"):
        extra_path = output / extra_name
        if extra_path.exists():
            checksum_paths.append(extra_path)
    manifest = {
        "files": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in checksum_paths
        }
    }
    (output / "SHA256SUMS.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary["generators"], indent=2))


if __name__ == "__main__":
    main()

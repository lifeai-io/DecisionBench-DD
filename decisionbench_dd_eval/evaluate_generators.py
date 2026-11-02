#!/usr/bin/env python3
"""DecisionBench-DD generator-evaluation CLI.

Ingests raw GenMol/MolMIM NIM run outputs (via their run manifests), scores every
generated molecule with a single common evaluator (chem_metrics.py), applies the
pre-registered qualification gates (decisionbench_dd_configs_v1.0/qualification_gates_v1.0.json,
v1.2), and writes:

  molecule_level.csv               -- every generated candidate, every metric, every gate
  table1_generator_scorecard.csv   -- DESCRIPTION.md Section 3 Table 1, per replicate + pooled
  figure2_similarity_qed_scatter.csv
  figure4_funnel.csv               -- DESCRIPTION.md Section 13 Figure 4, per tool
  summary.md / summary.json        -- headline numbers with bootstrap 95% CIs

Structural alerts (v1.2): PAINS is an absolute gate. Brenk is seed-relative and
INSTANCE-aware -- a candidate Brenk occurrence counts as seed-inherited only if
it has the same alert type AND its matched atoms equal a seed alert instance's
atoms mapped onto the candidate via an MCS atom correspondence (see
qualification_gates_v1.0.json:seed_relative_alert_rule / instance_mapping).
Ambroxol's own aniline at its own position does not block qualification; a
second, independent occurrence of the same alert type elsewhere does. Every
instance is reported for every molecule, never silently dropped.

Usage:
    python -m decisionbench_dd_eval.evaluate_generators \\
        --manifest-dir runs/ --out-dir results/

Each manifest must follow decisionbench_dd_configs_v1.0/run_manifest_template.json
and point (via raw_response_file) at the tool's raw JSON response.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from rdkit import Chem

from decisionbench_dd_eval import aggregate, chem_metrics, gates as gates_mod
from decisionbench_dd_eval.io_runs import ManifestError, discover_manifests, load_run

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROTOCOL_PATH = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "common_protocol.json"
DEFAULT_SEED_ALERT_CATALOG_PATH = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "seed_alert_catalog.json"


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--manifest-dir", type=Path, default=REPO_ROOT / "runs", help="Directory of *.manifest.json run manifests (default: runs/)")
    p.add_argument("--manifests", type=Path, nargs="*", default=None, help="Explicit manifest file paths (overrides --manifest-dir)")
    p.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL_PATH, help="Path to common_protocol.json (frozen seed SMILES)")
    p.add_argument("--gates", type=Path, default=gates_mod.DEFAULT_GATES_PATH, help="Path to qualification_gates_v1.0.json")
    p.add_argument("--seed-alert-catalog", type=Path, default=DEFAULT_SEED_ALERT_CATALOG_PATH, help="Path to seed_alert_catalog.json (frozen A_seed)")
    p.add_argument("--out-dir", type=Path, default=REPO_ROOT / "results", help="Output directory (default: results/)")
    p.add_argument("--n-boot", type=int, default=2000, help="Bootstrap resamples for 95%% CIs (default: 2000)")
    p.add_argument("--seed", type=int, default=0, help="RNG seed for bootstrap resampling (default: 0)")
    return p.parse_args(argv)


class SeedAllowlistMismatch(RuntimeError):
    pass


def load_seed(protocol_path: Path):
    with open(protocol_path, "r", encoding="utf-8") as fh:
        protocol = json.load(fh)
    seed_info = protocol["seed_molecule"]
    generator_input = seed_info["generator_input_smiles_frozen"]
    canonical_recorded = seed_info["canonical_smiles_for_downstream_identity_and_metrics"]
    canonical_computed = chem_metrics.canonicalize(generator_input)
    if canonical_computed != canonical_recorded:
        print(
            f"WARNING: recomputed canonical seed SMILES ({canonical_computed!r}) does not match "
            f"common_protocol.json's recorded value ({canonical_recorded!r}). "
            "Using the recomputed value for identity checks.",
            file=sys.stderr,
        )
        canonical = canonical_computed
    else:
        canonical = canonical_recorded
    seed_mol = Chem.MolFromSmiles(canonical)
    fp = chem_metrics.morgan_fingerprint(canonical)
    scaffold = chem_metrics.seed_scaffold_smiles(canonical)
    return canonical, seed_mol, fp, scaffold


def load_frozen_seed_brenk_instances(path: Path) -> list[chem_metrics.SeedAlertInstance]:
    with open(path, "r", encoding="utf-8") as fh:
        catalog = json.load(fh)
    return [
        chem_metrics.SeedAlertInstance(
            seed_instance_id=i["seed_instance_id"],
            alert_type=i["alert_type"],
            atom_indices=frozenset(i["matched_atom_indices"]),
        )
        for i in catalog["brenk_alert_instances"]
        if i.get("status") == "seed_inherent_allowlist"
    ]


def resolve_seed_brenk_instances(seed_mol, seed_alert_catalog_path: Path) -> list[chem_metrics.SeedAlertInstance]:
    """Cross-checks the frozen seed_alert_catalog.json (alert type AND matched
    atom indices, per instance) against a fresh RDKit computation on the seed
    alone. Per the file's own 'no additional alert after inspecting results'
    policy, a mismatch is a hard failure, not a warning -- the frozen record must
    be deliberately regenerated and re-reviewed, not silently superseded by
    whatever the running RDKit version now computes."""
    computed = chem_metrics.compute_seed_brenk_instances(seed_mol)
    frozen = load_frozen_seed_brenk_instances(seed_alert_catalog_path)
    computed_set = {(i.alert_type, i.atom_indices) for i in computed}
    frozen_set = {(i.alert_type, i.atom_indices) for i in frozen}
    if computed_set != frozen_set:
        raise SeedAllowlistMismatch(
            f"Recomputed seed Brenk instances {computed} do not match the frozen record in "
            f"{seed_alert_catalog_path} ({frozen}). Regenerate and deliberately re-review that file "
            "(e.g. after an RDKit upgrade) before running the evaluator -- do not silently trust "
            "either value."
        )
    return frozen


def score_run(run, seed_canonical, seed_mol, seed_fp, seed_scaffold, seed_brenk_instances):
    """Score every molecule in a run and mark within-run first occurrences."""
    records = []
    seen = set()
    for mol in run.molecules:
        rec = chem_metrics.score_molecule(
            tool=run.tool,
            run_id=run.run_id,
            raw_smiles=mol.raw_smiles,
            api_score=mol.api_score,
            seed_canonical_smiles=seed_canonical,
            seed_mol=seed_mol,
            seed_fingerprint=seed_fp,
            seed_scaffold_smiles=seed_scaffold,
            seed_brenk_instances=seed_brenk_instances,
        )
        if rec.valid:
            if rec.canonical_smiles not in seen:
                rec.is_first_occurrence_in_run = True
                seen.add(rec.canonical_smiles)
        records.append(rec)
    return records


def summarize_run(run, records, gate_results_per_record, gate_spec, n_boot, rng):
    valid = [r for r in records if r.valid]
    unique = [r for r in valid if r.is_first_occurrence_in_run]

    qualified_flags = [gates_mod.fully_qualified(g, gate_spec["gate_order"]) for g in gate_results_per_record]
    qualified_count = sum(qualified_flags)
    requested = run.requested_molecules

    ci = aggregate.bootstrap_proportion_ci(qualified_count, requested, n_boot=n_boot, rng=rng)

    scaffolds = {r.murcko_scaffold_smiles for r in valid if r.murcko_scaffold_smiles}
    seed_scaffold_hits = sum(1 for r in valid if r.scaffold_matches_seed)
    diversity = chem_metrics.internal_diversity([r.canonical_smiles for r in unique])

    # DESCRIPTION.md v1.1 Section 9: three Brenk rates, computed over valid molecules.
    has_any_brenk = sum(1 for r in valid if r.brenk_alerts_all)
    has_only_seed_brenk = sum(1 for r in valid if r.brenk_alerts_all and not r.brenk_alerts_new)
    has_new_brenk = sum(1 for r in valid if r.brenk_alerts_new)
    pains_hits = sum(1 for r in valid if r.pains_alerts)

    mps = (requested / run.runtime_seconds) if run.runtime_seconds else float("nan")

    return {
        "tool": run.tool,
        "run_id": run.run_id,
        "requested": requested,
        "returned": len(records),
        "valid_count": len(valid),
        "validity_pct": 100.0 * len(valid) / requested if requested else float("nan"),
        "unique_count": len(unique),
        "uniqueness_pct": 100.0 * len(unique) / len(valid) if valid else float("nan"),
        "exact_seed_count": sum(1 for r in valid if r.exact_seed_match),
        "exact_seed_rate_pct": 100.0 * sum(1 for r in valid if r.exact_seed_match) / requested if requested else float("nan"),
        "tanimoto_to_seed_mean": aggregate.mean_or_nan([r.tanimoto_to_seed for r in valid]),
        "tanimoto_to_seed_median": aggregate.median_or_nan([r.tanimoto_to_seed for r in valid]),
        "internal_diversity": diversity if diversity is not None else float("nan"),
        "unique_scaffold_count": len(scaffolds),
        "seed_scaffold_retention_pct": 100.0 * seed_scaffold_hits / len(valid) if valid else float("nan"),
        "qed_mean": aggregate.mean_or_nan([r.qed for r in valid]),
        "qed_median": aggregate.median_or_nan([r.qed for r in valid]),
        "sa_score_mean": aggregate.mean_or_nan([r.sa_score for r in valid]),
        "sa_score_median": aggregate.median_or_nan([r.sa_score for r in valid]),
        "mw_mean": aggregate.mean_or_nan([r.mw for r in valid]),
        "clogp_mean": aggregate.mean_or_nan([r.clogp for r in valid]),
        "tpsa_mean": aggregate.mean_or_nan([r.tpsa for r in valid]),
        "pains_pass_rate_pct": 100.0 * (len(valid) - pains_hits) / len(valid) if valid else float("nan"),
        "r_brenk_pct": 100.0 * has_any_brenk / len(valid) if valid else float("nan"),
        "r_seed_alert_pct": 100.0 * has_only_seed_brenk / len(valid) if valid else float("nan"),
        "r_new_alert_pct": 100.0 * has_new_brenk / len(valid) if valid else float("nan"),
        "qualified_count": qualified_count,
        "qualified_yield_pct": ci.point * 100.0,
        "qualified_yield_ci95_lo_pct": ci.lo * 100.0,
        "qualified_yield_ci95_hi_pct": ci.hi * 100.0,
        "runtime_seconds": run.runtime_seconds if run.runtime_seconds is not None else float("nan"),
        "molecules_per_second": mps,
    }


NUMERIC_SUMMARY_FIELDS = [
    "requested", "returned", "valid_count", "validity_pct", "unique_count", "uniqueness_pct",
    "exact_seed_count", "exact_seed_rate_pct", "tanimoto_to_seed_mean", "tanimoto_to_seed_median",
    "internal_diversity", "unique_scaffold_count", "seed_scaffold_retention_pct", "qed_mean", "qed_median",
    "sa_score_mean", "sa_score_median", "mw_mean", "clogp_mean", "tpsa_mean",
    "pains_pass_rate_pct", "r_brenk_pct", "r_seed_alert_pct", "r_new_alert_pct",
    "qualified_count", "qualified_yield_pct", "qualified_yield_ci95_lo_pct", "qualified_yield_ci95_hi_pct",
    "runtime_seconds", "molecules_per_second",
]

POOLED_ONLY_FIELDS = [
    "run_to_run_validity_pct_stdev",
    "run_to_run_qualified_yield_pct_stdev",
    "cross_replicate_duplicate_canonical_smiles",
]


def pooled_summary(tool, per_run_summaries, pooled_records, n_boot, rng):
    total_requested = sum(s["requested"] for s in per_run_summaries)
    total_qualified = sum(s["qualified_count"] for s in per_run_summaries)
    ci = aggregate.bootstrap_proportion_ci(total_qualified, total_requested, n_boot=n_boot, rng=rng)

    valid = [r for r in pooled_records if r.valid]
    canon_counts = defaultdict(int)
    for r in valid:
        canon_counts[r.canonical_smiles] += 1
    cross_replicate_duplicates = sum(1 for c in canon_counts.values() if c > 1)

    has_any_brenk = sum(1 for r in valid if r.brenk_alerts_all)
    has_only_seed_brenk = sum(1 for r in valid if r.brenk_alerts_all and not r.brenk_alerts_new)
    has_new_brenk = sum(1 for r in valid if r.brenk_alerts_new)
    pains_hits = sum(1 for r in valid if r.pains_alerts)

    row = {
        "tool": tool,
        "run_id": "pooled",
        "requested": total_requested,
        "returned": sum(s["returned"] for s in per_run_summaries),
        "valid_count": sum(s["valid_count"] for s in per_run_summaries),
        "validity_pct": 100.0 * sum(s["valid_count"] for s in per_run_summaries) / total_requested if total_requested else float("nan"),
        "unique_count": sum(s["unique_count"] for s in per_run_summaries),
        "uniqueness_pct": aggregate.mean_or_nan([s["uniqueness_pct"] for s in per_run_summaries]),
        "exact_seed_count": sum(s["exact_seed_count"] for s in per_run_summaries),
        "exact_seed_rate_pct": aggregate.mean_or_nan([s["exact_seed_rate_pct"] for s in per_run_summaries]),
        "tanimoto_to_seed_mean": aggregate.mean_or_nan([r.tanimoto_to_seed for r in valid]),
        "tanimoto_to_seed_median": aggregate.median_or_nan([r.tanimoto_to_seed for r in valid]),
        "internal_diversity": float("nan"),
        "unique_scaffold_count": len({r.murcko_scaffold_smiles for r in valid if r.murcko_scaffold_smiles}),
        "seed_scaffold_retention_pct": aggregate.mean_or_nan([s["seed_scaffold_retention_pct"] for s in per_run_summaries]),
        "qed_mean": aggregate.mean_or_nan([r.qed for r in valid]),
        "qed_median": aggregate.median_or_nan([r.qed for r in valid]),
        "sa_score_mean": aggregate.mean_or_nan([r.sa_score for r in valid]),
        "sa_score_median": aggregate.median_or_nan([r.sa_score for r in valid]),
        "mw_mean": aggregate.mean_or_nan([r.mw for r in valid]),
        "clogp_mean": aggregate.mean_or_nan([r.clogp for r in valid]),
        "tpsa_mean": aggregate.mean_or_nan([r.tpsa for r in valid]),
        "pains_pass_rate_pct": 100.0 * (len(valid) - pains_hits) / len(valid) if valid else float("nan"),
        "r_brenk_pct": 100.0 * has_any_brenk / len(valid) if valid else float("nan"),
        "r_seed_alert_pct": 100.0 * has_only_seed_brenk / len(valid) if valid else float("nan"),
        "r_new_alert_pct": 100.0 * has_new_brenk / len(valid) if valid else float("nan"),
        "qualified_count": total_qualified,
        "qualified_yield_pct": ci.point * 100.0,
        "qualified_yield_ci95_lo_pct": ci.lo * 100.0,
        "qualified_yield_ci95_hi_pct": ci.hi * 100.0,
        "runtime_seconds": aggregate.mean_or_nan([s["runtime_seconds"] for s in per_run_summaries]),
        "molecules_per_second": aggregate.mean_or_nan([s["molecules_per_second"] for s in per_run_summaries]),
        # diagnostics, not part of Table 1's core columns:
        "run_to_run_validity_pct_stdev": aggregate.stdev_or_nan([s["validity_pct"] for s in per_run_summaries]),
        "run_to_run_qualified_yield_pct_stdev": aggregate.stdev_or_nan([s["qualified_yield_pct"] for s in per_run_summaries]),
        "cross_replicate_duplicate_canonical_smiles": cross_replicate_duplicates,
    }
    diversity = chem_metrics.internal_diversity(list({r.canonical_smiles for r in valid}))
    row["internal_diversity"] = diversity if diversity is not None else float("nan")
    return row


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv=None) -> int:
    args = parse_args(argv)

    if args.manifests:
        manifest_paths = args.manifests
    else:
        manifest_paths = discover_manifests(args.manifest_dir)
        if not manifest_paths:
            print(
                f"No *.manifest.json files found in {args.manifest_dir}. "
                "Run the generation experiments first, or pass --manifests explicitly.",
                file=sys.stderr,
            )
            return 1

    try:
        gate_spec = gates_mod.load_gate_spec(args.gates)
        seed_canonical, seed_mol, seed_fp, seed_scaffold = load_seed(args.protocol)
        seed_brenk_instances = resolve_seed_brenk_instances(seed_mol, args.seed_alert_catalog)
        runs = [load_run(p) for p in manifest_paths]
    except (ManifestError, SeedAllowlistMismatch) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    rng = __import__("numpy").random.default_rng(args.seed)
    gate_names_sorted = sorted(gate_spec["gates"].keys())

    runs_by_tool = defaultdict(list)
    for run in runs:
        runs_by_tool[run.tool].append(run)

    molecule_rows: list[dict] = []
    scatter_rows: list[dict] = []
    table1_rows: list[dict] = []
    funnel_rows: list[dict] = []
    mcs_timeout_warnings: list[str] = []

    for tool, tool_runs in sorted(runs_by_tool.items()):
        per_run_summaries = []
        pooled_records: list[chem_metrics.MoleculeRecord] = []
        pooled_gate_results: list[dict] = []

        for run in sorted(tool_runs, key=lambda r: r.run_id):
            records = score_run(run, seed_canonical, seed_mol, seed_fp, seed_scaffold, seed_brenk_instances)
            gate_results = [gates_mod.evaluate_gates(r, gate_spec) for r in records]

            for rec, gr in zip(records, gate_results):
                qualified = gates_mod.fully_qualified(gr, gate_spec["gate_order"])
                if rec.valid and rec.alert_mapping_timed_out:
                    mcs_timeout_warnings.append(f"{rec.tool}/{rec.run_id}: {rec.canonical_smiles}")
                row = {
                    "tool": rec.tool,
                    "run_id": rec.run_id,
                    "raw_smiles": rec.raw_smiles,
                    "api_score": rec.api_score,
                    "canonical_smiles": rec.canonical_smiles,
                    "valid": rec.valid,
                    "exact_seed_match": rec.exact_seed_match,
                    "tanimoto_to_seed": rec.tanimoto_to_seed,
                    "qed": rec.qed,
                    "sa_score": rec.sa_score,
                    "mw": rec.mw,
                    "clogp": rec.clogp,
                    "tpsa": rec.tpsa,
                    "hbd": rec.hbd,
                    "hba": rec.hba,
                    "murcko_scaffold_smiles": rec.murcko_scaffold_smiles,
                    "scaffold_matches_seed": rec.scaffold_matches_seed,
                    # Required alert reporting fields (v1.1 Section 6 names, v1.2 instance-aware values):
                    "pains_alerts": ";".join(rec.pains_alerts),
                    "brenk_alerts_all": ";".join(rec.brenk_alerts_all),
                    "brenk_alerts_seed_inherent": ";".join(rec.brenk_alerts_seed_inherent),
                    "brenk_alerts_new": ";".join(rec.brenk_alerts_new),
                    "passes_pains_gate": rec.passes_pains_gate,
                    "passes_seed_relative_alert_gate": rec.passes_seed_relative_alert_gate,
                    # v1.2 instance-level detail (full per-occurrence audit trail):
                    "brenk_alert_instances": json.dumps(rec.brenk_alert_instances),
                    "n_seed_inherited_alert_instances": rec.n_seed_inherited_alert_instances,
                    "n_new_alert_instances": rec.n_new_alert_instances,
                    "alert_mapping_timed_out": rec.alert_mapping_timed_out,
                    "is_first_occurrence_in_run": rec.is_first_occurrence_in_run,
                    "qualified": qualified,
                }
                for gate_name in gate_names_sorted:
                    row[f"gate_{gate_name}"] = gr[gate_name]
                molecule_rows.append(row)

                if rec.valid:
                    scatter_rows.append(
                        {
                            "tool": rec.tool,
                            "run_id": rec.run_id,
                            "canonical_smiles": rec.canonical_smiles,
                            "tanimoto_to_seed": rec.tanimoto_to_seed,
                            "qed": rec.qed,
                            "qualified": qualified,
                        }
                    )

            summary = summarize_run(run, records, gate_results, gate_spec, args.n_boot, rng)
            per_run_summaries.append(summary)
            table1_rows.append(summary)

            pooled_records.extend(records)
            pooled_gate_results.extend(gate_results)

        table1_rows.append(pooled_summary(tool, per_run_summaries, pooled_records, args.n_boot, rng))

        pooled_requested = sum(r.requested_molecules for r in tool_runs)
        for stage in gates_mod.funnel_counts(
            list(zip(pooled_records, pooled_gate_results)), gate_spec, pooled_requested
        ):
            funnel_rows.append({"tool": tool, **stage})

    if mcs_timeout_warnings:
        print(
            f"WARNING: seed-vs-candidate MCS atom mapping timed out for {len(mcs_timeout_warnings)} "
            "molecule(s); their seed-relative Brenk classification used the best-so-far (possibly "
            "partial) mapping. First few: " + "; ".join(mcs_timeout_warnings[:5]),
            file=sys.stderr,
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)

    molecule_fields = list(molecule_rows[0].keys()) if molecule_rows else []
    write_csv(args.out_dir / "molecule_level.csv", molecule_rows, molecule_fields)
    write_csv(
        args.out_dir / "table1_generator_scorecard.csv",
        table1_rows,
        ["tool", "run_id"] + NUMERIC_SUMMARY_FIELDS + POOLED_ONLY_FIELDS,
    )
    write_csv(
        args.out_dir / "figure2_similarity_qed_scatter.csv",
        scatter_rows,
        ["tool", "run_id", "canonical_smiles", "tanimoto_to_seed", "qed", "qualified"],
    )
    write_csv(args.out_dir / "figure4_funnel.csv", funnel_rows, ["tool", "stage", "count", "pct_of_requested"])

    write_summary(args.out_dir, table1_rows, funnel_rows)

    print(f"Wrote results to {args.out_dir}")
    return 0


def write_summary(out_dir: Path, table1_rows: list[dict], funnel_rows: list[dict]) -> None:
    pooled = {row["tool"]: row for row in table1_rows if row["run_id"] == "pooled"}

    lines = ["# DecisionBench-DD generator scorecard summary (v1.2 gates)", ""]
    for tool, row in sorted(pooled.items()):
        lines.append(f"## {tool}")
        lines.append(
            f"- Qualified candidate yield (Y_chemical) = {row['qualified_yield_pct']:.1f}% "
            f"(95% CI {row['qualified_yield_ci95_lo_pct']:.1f}-{row['qualified_yield_ci95_hi_pct']:.1f}%), "
            f"pooled over {row['requested']} requested molecules"
        )
        lines.append(f"- Validity = {row['validity_pct']:.1f}%, run-to-run stdev = {row['run_to_run_validity_pct_stdev']:.1f} pp")
        lines.append(f"- Uniqueness (of valid) = {row['uniqueness_pct']:.1f}%")
        lines.append(f"- Internal diversity (pooled unique set) = {row['internal_diversity']:.3f}")
        lines.append(f"- Median Tanimoto to seed = {row['tanimoto_to_seed_median']:.3f}")
        lines.append(f"- Mean QED = {row['qed_mean']:.3f}, mean SA score = {row['sa_score_mean']:.2f}")
        lines.append(f"- PAINS pass rate = {row['pains_pass_rate_pct']:.1f}%")
        lines.append(
            f"- Brenk: R_Brenk (any alert) = {row['r_brenk_pct']:.1f}%, "
            f"R_seed_alert (only seed-inherent) = {row['r_seed_alert_pct']:.1f}%, "
            f"R_new_alert (>=1 new alert, used for qualification) = {row['r_new_alert_pct']:.1f}%"
        )
        lines.append("")

    lines.append("## Funnel (pooled across replicates)")
    lines.append("")
    lines.append("| tool | stage | count | % of requested |")
    lines.append("| --- | --- | ---: | ---: |")
    for row in funnel_rows:
        lines.append(f"| {row['tool']} | {row['stage']} | {row['count']} | {row['pct_of_requested']:.1f}% |")
    lines.append("")

    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "summary.json").write_text(
        json.dumps({"pooled": pooled, "funnel": funnel_rows}, indent=2, default=str), encoding="utf-8"
    )


if __name__ == "__main__":
    sys.exit(main())

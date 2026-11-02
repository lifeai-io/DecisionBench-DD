"""Applies the pre-registered qualification gates from
decisionbench_dd_configs_v1.0/qualification_gates_v1.0.json to scored molecules.

Gates are loaded from that frozen JSON file, never hardcoded here, so that
changing a threshold always shows up as a diff to the frozen protocol file
(DESCRIPTION.md Section 15: "selecting thresholds after seeing which tool wins"
is exactly what this indirection is meant to make visible).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from decisionbench_dd_eval.chem_metrics import MoleculeRecord

DEFAULT_GATES_PATH = (
    Path(__file__).resolve().parent.parent / "decisionbench_dd_configs_v1.0" / "qualification_gates_v1.0.json"
)


def load_gate_spec(path: Path = DEFAULT_GATES_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _threshold_pass(value: Optional[float], spec: dict) -> bool:
    if value is None:
        return False
    if "min" in spec:
        lo = spec["min"]
        ok = value >= lo if spec.get("inclusive_min", True) else value > lo
        if not ok:
            return False
    if "max" in spec:
        hi = spec["max"]
        ok = value <= hi if spec.get("inclusive_max", True) else value < hi
        if not ok:
            return False
    return True


# Metrics that are already booleans on MoleculeRecord (possibly negated), rather
# than a min/max threshold on a numeric field.
_BOOLEAN_METRICS = {
    "valid": lambda r: r.valid,
    "is_first_occurrence_in_run": lambda r: r.valid and r.is_first_occurrence_in_run,
    "not_exact_seed_match": lambda r: r.valid and not r.exact_seed_match,
    "passes_pains_gate": lambda r: r.valid and r.passes_pains_gate,
    "passes_seed_relative_alert_gate": lambda r: r.valid and r.passes_seed_relative_alert_gate,
}


def gate_pass(gate_name: str, gate_spec: dict, record: MoleculeRecord) -> bool:
    metric = gate_spec["metric"]
    if metric in _BOOLEAN_METRICS:
        return _BOOLEAN_METRICS[metric](record)
    if not record.valid:
        return False
    value = getattr(record, metric)
    return _threshold_pass(value, gate_spec)


def evaluate_gates(record: MoleculeRecord, gate_spec: dict) -> dict[str, bool]:
    """Return {gate_name: passed} for every gate defined in gate_spec['gates']."""
    gates = gate_spec["gates"]
    return {name: gate_pass(name, spec, record) for name, spec in gates.items()}


def fully_qualified(gate_results: dict[str, bool], gate_order: list[str]) -> bool:
    return all(gate_results[name] for name in gate_order)


def funnel_counts(
    records_with_gates: list[tuple[MoleculeRecord, dict[str, bool]]],
    gate_spec: dict,
    requested_molecules: int,
) -> list[dict]:
    """Cumulative-AND funnel per decisionbench_dd_configs_v1.0/qualification_gates_v1.0.json:funnel_stages.

    Percentages use N_requested as the denominator (DESCRIPTION.md Section 3's
    Y_qualified = N_pass_all_gates / N_requested), not N_returned, so a tool that
    silently returns fewer molecules than requested does not get an inflated rate.
    """
    stages = gate_spec["funnel_stages"]
    out = []
    for stage in stages:
        needed = stage["cumulative_gates"]
        if not needed:
            count = requested_molecules
        else:
            count = sum(1 for _, g in records_with_gates if all(g[gate] for gate in needed))
        out.append(
            {
                "stage": stage["name"],
                "count": count,
                "pct_of_requested": (100.0 * count / requested_molecules) if requested_molecules else 0.0,
            }
        )
    return out

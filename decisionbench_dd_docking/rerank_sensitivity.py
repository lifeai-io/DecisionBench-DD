"""Bounded reranking-sensitivity analysis
(decisionbench_dd_configs_v1.0/candidate_screen_v1.0/downstream_gcase_screening_protocol.md,
section 10): "Because the redocking benchmark found a near-native pose
within GNINA Top-5 for 8/14 cases but ranked only 3/14 first, retain these
pre-specified, non-fitted sensitivity selectors: (1) native CNNscore
descending; (2) CNN_VS descending; (3) minimizedAffinity ascending. Report
how each fixed selector changes redocking Success@1 and candidate
structural yield. Do not fit weights, choose a selector on all 14
structures, or describe the best post-hoc selector as independently
validated."

This module only picks which pose index a fixed, pre-specified rule would
have called "top-1" -- it never inspects outcomes before choosing a rule,
and it never blends or tunes selectors. Both callers (this module's own
users in evaluate_docking-style redocking scoring and
score_candidate_screen-style structural-proxy scoring) must treat every
selector's result as an equally-valid sensitivity readout, not a search for
the best-performing one.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from rdkit import Chem

SELECTORS = ["native_rank1", "cnn_vs_desc", "minimized_affinity_asc"]


def load_raw_pose_props(pose_sdf_path: Path) -> list[dict]:
    """Per-pose CNN/affinity properties in native GNINA output order (rank 1
    first) -- NOT re-sorted by any of this module's own selectors, so callers
    can apply each selector to the same untouched pool."""
    suppl = Chem.SDMolSupplier(str(pose_sdf_path), removeHs=False)
    mols = [m for m in suppl if m is not None]
    out = []
    for i, m in enumerate(mols):
        out.append({
            "rank": i + 1,
            "mol": m,
            "cnnscore": float(m.GetProp("CNNscore")),
            "cnnaffinity": float(m.GetProp("CNNaffinity")),
            "cnn_vs": float(m.GetProp("CNN_VS")) if m.HasProp("CNN_VS") else None,
            "minimized_affinity": float(m.GetProp("minimizedAffinity")),
        })
    return out


def pick_index(poses: list[dict], selector: str) -> Optional[int]:
    """Index into `poses` (native rank order) that `selector` would call
    top-1. None if the pool is empty or the selector's required field is
    missing from every pose (e.g. an older GNINA build without CNN_VS)."""
    if not poses:
        return None
    if selector == "native_rank1":
        return 0
    if selector == "cnn_vs_desc":
        if any(p["cnn_vs"] is None for p in poses):
            return None
        return max(range(len(poses)), key=lambda i: poses[i]["cnn_vs"])
    if selector == "minimized_affinity_asc":
        return min(range(len(poses)), key=lambda i: poses[i]["minimized_affinity"])
    raise ValueError(f"unknown selector: {selector}")

"""Per-run and per-tool summary statistics, including bootstrap 95% CIs.

Follows DESCRIPTION.md Section 12: three independent replicates, distributions +
bootstrap 95% CIs rather than significance testing on a small sample.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Optional

import numpy as np

from decisionbench_dd_eval.chem_metrics import MoleculeRecord


@dataclass
class CI:
    point: float
    lo: float
    hi: float

    def as_tuple(self):
        return (self.point, self.lo, self.hi)


def bootstrap_proportion_ci(successes: int, n: int, n_boot: int = 2000, alpha: float = 0.05, rng: Optional[np.random.Generator] = None) -> CI:
    """Bootstrap CI for a proportion successes/n by resampling n Bernoulli draws."""
    if n == 0:
        return CI(point=float("nan"), lo=float("nan"), hi=float("nan"))
    rng = rng or np.random.default_rng(0)
    point = successes / n
    data = np.zeros(n, dtype=np.float64)
    data[:successes] = 1.0
    boot_means = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        sample = rng.choice(data, size=n, replace=True)
        boot_means[i] = sample.mean()
    lo, hi = np.quantile(boot_means, [alpha / 2, 1 - alpha / 2])
    return CI(point=point, lo=float(lo), hi=float(hi))


def bootstrap_mean_ci(values: list[float], n_boot: int = 2000, alpha: float = 0.05, rng: Optional[np.random.Generator] = None) -> CI:
    arr = np.array([v for v in values if v is not None], dtype=np.float64)
    if arr.size == 0:
        return CI(point=float("nan"), lo=float("nan"), hi=float("nan"))
    rng = rng or np.random.default_rng(0)
    point = float(arr.mean())
    n = arr.size
    boot_means = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        sample = rng.choice(arr, size=n, replace=True)
        boot_means[i] = sample.mean()
    lo, hi = np.quantile(boot_means, [alpha / 2, 1 - alpha / 2])
    return CI(point=point, lo=float(lo), hi=float(hi))


def median_or_nan(values: list[Optional[float]]) -> float:
    clean = [v for v in values if v is not None]
    return statistics.median(clean) if clean else float("nan")


def mean_or_nan(values: list[Optional[float]]) -> float:
    clean = [v for v in values if v is not None]
    return statistics.mean(clean) if clean else float("nan")


def stdev_or_nan(values: list[float]) -> float:
    clean = [v for v in values if v is not None]
    return statistics.stdev(clean) if len(clean) > 1 else float("nan")

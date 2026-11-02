"""Statistical significance check for Item-2 compliance counts.

Originally added after an AgenticLS-style review pointed out that the
manuscript's "80% -> 60% -> 40%" framing of Haiku 4.5's Item-2 violation
rate (at n=5 per condition) reads as an established trend without stating
whether it clears conventional significance. It did not clear significance
at n=5. A follow-up review suggested the fix was to run more replicates
rather than only caveat the small sample, since the runs are cheap; Haiku
was scaled to n=50 per condition (Sonnet was left at n=5, since it already
showed a clean 15/15 ceiling effect with no variance to resolve). Both the
original n=5 numbers and the n=50 numbers are computed below for direct
comparison. Run with: python3 significance_check.py
"""

from scipy import stats
import numpy as np


def clopper_pearson(x, n, alpha=0.05):
    lo = 0.0 if x == 0 else stats.beta.ppf(alpha / 2, x, n - x + 1)
    hi = 1.0 if x == n else stats.beta.ppf(1 - alpha / 2, x + 1, n - x)
    return lo, hi


def cochran_armitage(successes, totals, scores):
    successes = np.array(successes, dtype=float)
    totals = np.array(totals, dtype=float)
    scores = np.array(scores, dtype=float)
    n = totals.sum()
    r = successes.sum()
    xbar = (scores * totals).sum() / n
    num = (scores * (successes - totals * r / n)).sum()
    var = (r / n) * (1 - r / n) * ((totals * (scores - xbar) ** 2).sum())
    z = num / np.sqrt(var)
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    return z, p


if __name__ == "__main__":
    print("=" * 70)
    print("ORIGINAL n=5 PER CONDITION (kept for before/after comparison)")
    print("=" * 70)
    cells5 = [
        ("Haiku free-form", 1, 5),
        ("Haiku prose-guidance", 2, 5),
        ("Haiku explicit contract", 3, 5),
        ("Sonnet (all 3 conditions)", 5, 5),
    ]
    print("Exact (Clopper-Pearson) 95% CIs, Item-2 compliance:")
    for label, x, n in cells5:
        lo, hi = clopper_pearson(x, n)
        print(f"  {label}: {x}/{n} ({x/n*100:.0f}%), 95% CI [{lo*100:.1f}%, {hi*100:.1f}%]")

    print()
    print("Pairwise Fisher's exact (two-sided), Haiku conditions, n=5:")
    pairs5 = [
        ("free-form (1/5) vs prose (2/5)", [[1, 4], [2, 3]]),
        ("prose (2/5) vs contract (3/5)", [[2, 3], [3, 2]]),
        ("free-form (1/5) vs contract (3/5)", [[1, 4], [3, 2]]),
    ]
    for label, table in pairs5:
        _, p = stats.fisher_exact(table)
        print(f"  {label}: p = {p:.3f}")

    print()
    z5, p5 = cochran_armitage([1, 2, 3], [5, 5, 5], [0, 1, 2])
    print(f"Cochran-Armitage trend test (free-form -> prose -> contract), n=5: z={z5:.3f}, p={p5:.3f}")

    print()
    print("=" * 70)
    print("SCALED-UP n=50 PER CONDITION (Haiku only; Sonnet left at n=5, ceiling)")
    print("=" * 70)
    cells50 = [
        ("Haiku free-form", 18, 50),
        ("Haiku prose-guidance", 33, 50),
        ("Haiku explicit contract", 36, 50),
    ]
    print("Exact (Clopper-Pearson) 95% CIs, Item-2 compliance:")
    for label, x, n in cells50:
        lo, hi = clopper_pearson(x, n)
        print(f"  {label}: {x}/{n} ({x/n*100:.1f}%), 95% CI [{lo*100:.1f}%, {hi*100:.1f}%]")

    print()
    print("Pairwise Fisher's exact (two-sided), Haiku conditions, n=50:")
    pairs50 = [
        ("free-form (18/50) vs prose (33/50)", [[18, 32], [33, 17]]),
        ("prose (33/50) vs contract (36/50)", [[33, 17], [36, 14]]),
        ("free-form (18/50) vs contract (36/50)", [[18, 32], [36, 14]]),
    ]
    for label, table in pairs50:
        _, p = stats.fisher_exact(table)
        print(f"  {label}: p = {p:.4f}")

    print()
    z50, p50 = cochran_armitage([18, 33, 36], [50, 50, 50], [0, 1, 2])
    print(f"Cochran-Armitage trend test (free-form -> prose -> contract), n=50: z={z50:.3f}, p={p50:.5f}")

    print()
    print("=" * 70)
    print("CLUSTER BOOTSTRAP (unchanged; GenMol yield, unaffected by Haiku scale-up)")
    print("=" * 70)
    print("Cluster bootstrap on GenMol qualified yield (3 replicates: 30/100, 29/100, 7/100):")
    rng = np.random.default_rng(42)
    reps = np.array([0.30, 0.29, 0.07])
    boot = rng.choice(reps, size=(2000, 3), replace=True).mean(axis=1)
    print(f"  mean={boot.mean()*100:.2f}%, 95% CI [{np.percentile(boot, 2.5)*100:.1f}%, "
          f"{np.percentile(boot, 97.5)*100:.1f}%]")
    print("  (reported pooled-Bernoulli CI in the paper: 22.0% [17.3%, 26.7%] -- "
          "narrower, since it treats the 3 replicates' 300 pooled outcomes as "
          "independent Bernoulli draws rather than resampling replicates.)")

#!/usr/bin/env python3
"""Steps 11-13 of the decoy-panel calibration addendum, POST-HOC AMENDED after
inspecting results (see decoy_addendum_v1.0.md's amendment log): the 69
candidates were re-docked fresh in the same blinded batch as the 345 decoys
as an internal consistency check, and came back 24/69 (34.8%) passing --
not the frozen primary's 16/69 (23.2%). Root-caused to RDKit ETKDGv3
ligand-embedding non-determinism across separate process invocations (same
canonical/protonated SMILES, same atom count, but starting-conformer
coordinates differ by up to ~1.7 A between runs for the same molecule),
which cascades into CNNaffinity differences of up to ~2.2 units and flips
18/69 (26%) of candidates' pass/fail status -- a much larger effect than the
previously-documented ~0.0009 cross-machine CNNaffinity drift (Appendix H),
which only characterized Ambroxol's own score.

Because of this, the SAME-BATCH comparison (candidates and decoys docked
together, same run, same embedding regime) is now the PRIMARY analysis --
it is not confounded by cross-run embedding variance the way the originally
pre-registered comparison (decoy rate vs. the frozen primary 16/69) is. Both
are reported; the pre-registered comparison is kept as a secondary,
explicitly-flagged-as-confounded robustness check, not silently dropped.

Usage:
    python -m decisionbench_dd_docking.analyze_decoy_panel \\
        --candidate-results <out-dir>/candidate_results.csv \\
        --pose-scores <out-dir>/pose_scores.csv \\
        --n-boot 5000
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREEN_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0" / "candidate_screen_v1.0"
OUT_DIR = SCREEN_DIR / "decoy_panel_v1.0"
MAPPING = OUT_DIR / "decoy_panel_mapping.csv"
FROZEN_PRIMARY_RESULTS = REPO_ROOT / "candidate_screen_results" / "candidate_results.csv"

FROZEN_CANDIDATE_PASS = 16
FROZEN_CANDIDATE_N = 69
FROZEN_CANDIDATE_RATE = FROZEN_CANDIDATE_PASS / FROZEN_CANDIDATE_N  # 0.2319... = 23.2%


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--candidate-results", type=Path, required=True, help="score_candidate_screen.py's candidate_results.csv for the blinded decoy-panel run")
    p.add_argument("--pose-scores", type=Path, required=True, help="score_candidate_screen.py's pose_scores.csv for the blinded decoy-panel run")
    p.add_argument("--n-boot", type=int, default=5000)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out-dir", type=Path, default=OUT_DIR)
    return p.parse_args(argv)


def cluster_bootstrap_ratio(cand_pass: dict, decoy_pass_by_cand: dict, n_boot: int, rng: np.random.Generator):
    """Resample the 69 matched clusters (1 candidate + its 5 decoys) with replacement.
    Returns arrays of (p_candidate, p_decoy) per bootstrap draw, both computed over the
    SAME resampled clusters, for the same-batch primary comparison."""
    cluster_ids = list(decoy_pass_by_cand.keys())
    n = len(cluster_ids)
    p_cand_boot = np.empty(n_boot)
    p_decoy_boot = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        csamp = [cand_pass[cluster_ids[i]] for i in idx]
        dsamp = np.concatenate([decoy_pass_by_cand[cluster_ids[i]] for i in idx])
        p_cand_boot[b] = np.mean(csamp)
        p_decoy_boot[b] = dsamp.mean()
    return p_cand_boot, p_decoy_boot


def cluster_bootstrap_decoy_only(decoy_pass_by_cluster: list[np.ndarray], n_boot: int, rng: np.random.Generator):
    n_clusters = len(decoy_pass_by_cluster)
    boot_rates = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n_clusters, size=n_clusters)
        pooled = np.concatenate([decoy_pass_by_cluster[i] for i in idx])
        boot_rates[b] = pooled.mean()
    return boot_rates


def interpret(p_candidate: float, p_decoy: float, rr: float, rr_ci: tuple[float, float]) -> str:
    if p_decoy >= p_candidate:
        return "Decoy rate >= candidate rate: no evidence the structural proxy enriches pipeline candidates over matched unrelated molecules."
    if p_decoy > 0.10 or (rr_ci[0] <= 1 <= rr_ci[1]):
        return "Decoy rate below candidate rate but >10%, or RR CI includes 1: possible but weak discrimination; gate remains poorly calibrated."
    if p_decoy <= 0.10 and rr > 2 and not (rr_ci[0] <= 1 <= rr_ci[1]):
        return "Decoy rate <=10%, matched RR >2, CI excludes 1: evidence the proxy rejects most property-matched unrelated molecules."
    return "Outcome did not cleanly match a pre-registered category; report descriptively."


def main() -> int:
    args = parse_args()
    mapping = pd.read_csv(MAPPING)
    cand_results = pd.read_csv(args.candidate_results)
    pose_scores = pd.read_csv(args.pose_scores)

    merged = cand_results.merge(mapping, left_on="candidate_id", right_on="blinded_id", how="left")
    decoys = merged[merged["role"] == "decoy"].copy()
    redocked_cands = merged[merged["role"] == "candidate"].copy()
    if len(decoys) != 345:
        print(f"WARNING: expected 345 decoys after de-blinding, found {len(decoys)}")
    if len(redocked_cands) != 69:
        print(f"WARNING: expected 69 re-docked candidates, found {len(redocked_cands)}")

    n_decoy_pass = int(decoys["structural_proxy_pass"].sum())
    p_decoy = n_decoy_pass / len(decoys)
    n_cand_samebatch_pass = int(redocked_cands["structural_proxy_pass"].sum())
    p_cand_samebatch = n_cand_samebatch_pass / len(redocked_cands)

    # ---- Embedding-reproducibility diagnostic: compare this run's re-docked candidates
    # against the frozen primary run's candidate_results.csv for the SAME 69 candidates. ----
    repro = {}
    if FROZEN_PRIMARY_RESULTS.exists():
        primary = pd.read_csv(FROZEN_PRIMARY_RESULTS)[["candidate_id", "structural_proxy_pass", "cnnaffinity_3keh"]]
        primary = primary.rename(columns={"structural_proxy_pass": "pass_primary", "cnnaffinity_3keh": "cnnaff_primary"})
        redock_slim = redocked_cands[["true_id", "structural_proxy_pass", "cnnaffinity_3keh"]].rename(
            columns={"structural_proxy_pass": "pass_redock", "cnnaffinity_3keh": "cnnaff_redock"})
        cmp_df = primary.merge(redock_slim, left_on="candidate_id", right_on="true_id")
        flipped = cmp_df[cmp_df["pass_primary"] != cmp_df["pass_redock"]]
        cnnaff_diff = (cmp_df["cnnaff_redock"] - cmp_df["cnnaff_primary"]).to_numpy(dtype=float)
        repro = {
            "n_candidates_compared": int(len(cmp_df)),
            "frozen_primary_pass": int(cmp_df["pass_primary"].sum()),
            "this_run_redock_pass": int(cmp_df["pass_redock"].sum()),
            "n_flipped": int(len(flipped)),
            "n_newly_passing": int((flipped["pass_redock"] == True).sum()),  # noqa: E712
            "n_newly_failing": int((flipped["pass_redock"] == False).sum()),  # noqa: E712
            "cnnaffinity_diff_redock_minus_primary": {
                "mean": round(float(np.mean(cnnaff_diff)), 4), "std": round(float(np.std(cnnaff_diff)), 4),
                "min": round(float(np.min(cnnaff_diff)), 4), "max": round(float(np.max(cnnaff_diff)), 4),
            },
            "plausible_major_source": (
                "RDKit ETKDGv3 embedding is not reproducible across separate process invocations despite an "
                "explicit fixed randomSeed=42 (decisionbench_dd_docking/prepare_ligands.py) -- verified directly "
                "for GM_009 (blinded PMD_0133): identical canonical/protonated SMILES and atom count between the "
                "frozen primary docking_input_ligands/GM_009_3KEH.sdf and this run's freshly-prepared SDF, but "
                "starting-conformer heavy-atom coordinates differ by up to 1.6953 A (mean 0.2744 A). This is a "
                "substantially larger effect than the previously-documented ~0.0009 cross-machine CNNaffinity "
                "drift (Appendix H), which characterized only Ambroxol's own score, not the full candidate "
                "population. This is not a controlled experiment isolating embedding as the sole varying input: "
                "which physical machine ran which docking batch was not recorded, so an additional contribution "
                "from other run-level or hardware factors cannot be ruled out on top of the embedding effect."
            ),
            "bootstrap_interval_caveat": (
                "The matched cluster-bootstrap interval below conditions on one embedding-and-docking realization "
                "per molecule and therefore does not capture within-molecule procedural variability from repeated "
                "ligand embedding."
            ),
        }

    # ---- PRIMARY: same-batch matched comparison (candidates and decoys, same run) ----
    cand_pass = dict(zip(redocked_cands["true_id"], redocked_cands["structural_proxy_pass"].astype(float)))
    decoy_pass_by_cand = decoys.groupby("matched_to_candidate")["structural_proxy_pass"].apply(
        lambda s: s.to_numpy(dtype=float)).to_dict()
    rng = np.random.default_rng(args.seed)
    p_cand_boot, p_decoy_boot_sb = cluster_bootstrap_ratio(cand_pass, decoy_pass_by_cand, args.n_boot, rng)
    rr_boot_sb = np.where(p_decoy_boot_sb > 0, p_cand_boot / np.where(p_decoy_boot_sb > 0, p_decoy_boot_sb, np.nan), np.nan)
    delta_boot_sb = p_cand_boot - p_decoy_boot_sb

    rr_samebatch = p_cand_samebatch / p_decoy if p_decoy > 0 else float("inf")
    rr_ci_samebatch = tuple(np.nanpercentile(rr_boot_sb, [2.5, 97.5]))
    delta_ci_samebatch = tuple(np.percentile(delta_boot_sb, [2.5, 97.5]))
    p_decoy_ci_samebatch = tuple(np.percentile(p_decoy_boot_sb, [2.5, 97.5]))
    interpretation_samebatch = interpret(p_cand_samebatch, p_decoy, rr_samebatch, rr_ci_samebatch)

    # ---- SECONDARY (pre-registered, confounded): decoy rate vs. FROZEN primary 16/69 ----
    rng2 = np.random.default_rng(args.seed + 1)
    clusters_decoy_only = list(decoy_pass_by_cand.values())
    boot_rates_prereg = cluster_bootstrap_decoy_only(clusters_decoy_only, args.n_boot, rng2)
    rr_prereg = FROZEN_CANDIDATE_RATE / p_decoy if p_decoy > 0 else float("inf")
    rr_ci_prereg = tuple(np.nanpercentile(
        np.where(boot_rates_prereg > 0, FROZEN_CANDIDATE_RATE / np.where(boot_rates_prereg > 0, boot_rates_prereg, np.nan), np.nan),
        [2.5, 97.5]))
    delta_ci_prereg = tuple(np.percentile(FROZEN_CANDIDATE_RATE - boot_rates_prereg, [2.5, 97.5]))
    interpretation_prereg = interpret(FROZEN_CANDIDATE_RATE, p_decoy, rr_prereg, rr_ci_prereg)

    # ---- Stage decomposition (decoys only, both receptor states) ----
    decoy_ids = set(decoys["blinded_id"])
    dp = pose_scores[pose_scores["ligand_id"].isin(decoy_ids)]
    stage_rows = []
    for state, sub in dp.groupby("receptor_state"):
        stage_rows.append({
            "receptor_state": state, "requested": len(sub),
            "returned_5_poses": int(sub["all_five_poses_returned"].sum()),
            "geometry_valid_top1": int(sub["top1_valid"].sum()),
            "catalytic_contact_top1": int(sub["top1_active_site_occupied"].sum()),
        })
    stage_df = pd.DataFrame(stage_rows)

    # ---- Gate-mechanism table: candidates vs. decoys, 3KEH only, including the
    # CNNaffinity-vs-Ambroxol threshold marginally (this is what the complete structural
    # proxy actually gates on most heavily -- see gate_mechanism_table below). ----
    ambroxol_thresh = None
    try:
        with open(args.candidate_results.parent / "summary.json") as fh:
            ambroxol_thresh = json.load(fh)["ambroxol_cnnaffinity_3keh"]
    except Exception:
        pass
    gate_mechanism_rows = []
    pose_keh = pose_scores[pose_scores["receptor_state"] == "3KEH"].merge(
        mapping, left_on="ligand_id", right_on="blinded_id", how="left")
    complete_pass_by_role = {"candidate": n_cand_samebatch_pass, "decoy": n_decoy_pass}
    for role, label in [("candidate", "Same-batch candidates"), ("decoy", "Decoys")]:
        sub = pose_keh[pose_keh["role"] == role]
        n = len(sub)
        row = {
            "population": label, "n": n,
            "five_poses_returned": int(sub["all_five_poses_returned"].sum()),
            "geometry_valid_top1": int(sub["top1_valid"].sum()),
            "catalytic_contact_top1": int(sub["top1_active_site_occupied"].sum()),
        }
        if ambroxol_thresh is not None:
            row["cnnaffinity_ge_ambroxol"] = int((sub["top1_cnnaffinity"] >= ambroxol_thresh).sum())
        row["complete_structural_proxy"] = complete_pass_by_role[role]
        gate_mechanism_rows.append(row)
    gate_mechanism_df = pd.DataFrame(gate_mechanism_rows)

    # Marginal, not cumulative-causal, attribution: the gates are conjunctive, so
    # scoring order cannot change the final pass set, only which gate receives
    # marginal attribution. Both catalytic-site contact and the CNNaffinity
    # threshold show a real descriptive population difference -- contact is not
    # merely a passive component that "goes along for the ride" behind CNNaffinity.
    gate_mechanism_interpretation = None
    cand_row, decoy_row = gate_mechanism_rows[0], gate_mechanism_rows[1]
    if "cnnaffinity_ge_ambroxol" in cand_row:
        cand_contact_pct = 100 * cand_row["catalytic_contact_top1"] / cand_row["n"]
        decoy_contact_pct = 100 * decoy_row["catalytic_contact_top1"] / decoy_row["n"]
        cand_cnn_pct = 100 * cand_row["cnnaffinity_ge_ambroxol"] / cand_row["n"]
        decoy_cnn_pct = 100 * decoy_row["cnnaffinity_ge_ambroxol"] / decoy_row["n"]
        gate_mechanism_interpretation = (
            f"The gates are conjunctive, so this table decomposes them marginally (each column scored "
            f"independently against the full population, not cumulatively): reordering them cannot change "
            f"the final pass set, only which gate receives marginal attribution. Both catalytic-site contact "
            f"({cand_contact_pct:.1f}% vs. {decoy_contact_pct:.1f}%) and the CNNaffinity-vs-Ambroxol threshold "
            f"({cand_cnn_pct:.1f}% vs. {decoy_cnn_pct:.1f}%) show a descriptive population difference; "
            f"CNNaffinity is the more restrictive filter in absolute terms for both populations, but contact "
            f"is not merely incidental -- it is not the only gate component that differs between populations."
        )

    # ---- Size-bias checks on decoys (3KEH) ----
    dp_keh = dp[dp["receptor_state"] == "3KEH"].dropna(subset=["top1_cnnaffinity"])
    decoy_props = decoys.merge(dp_keh[["ligand_id", "top1_cnnaffinity"]], left_on="blinded_id", right_on="ligand_id", how="inner")
    matched_decoys = pd.read_csv(OUT_DIR / "property_matched_decoys.csv")
    decoy_props = decoy_props.merge(
        matched_decoys[["decoy_chembl_id", "decoy_hac", "decoy_clogp", "decoy_halogen_count"]],
        left_on="true_id", right_on="decoy_chembl_id", how="left",
    )
    size_bias = {}
    if len(decoy_props) > 5:
        rho, pval = stats.spearmanr(decoy_props["top1_cnnaffinity"], decoy_props["decoy_hac"])
        size_bias["spearman_cnnaffinity_vs_hac"] = {"rho": round(float(rho), 4), "p": round(float(pval), 5)}
        try:
            import statsmodels.api as sm
            X = sm.add_constant(decoy_props[["decoy_hac", "decoy_clogp"]].astype(float))
            y = decoy_props["structural_proxy_pass"].astype(int)
            model = sm.Logit(y, X).fit(disp=0)
            size_bias["logit_pass_on_hac_clogp"] = {k: round(v, 4) for k, v in model.params.items()}
            size_bias["logit_pass_on_hac_clogp_pvalues"] = {k: round(v, 4) for k, v in model.pvalues.items()}
        except Exception as exc:
            size_bias["logit_note"] = f"logistic model skipped: {exc}"

        # Halogen-count balance and sensitivity: matching_balance.csv flagged HalogenCount
        # (SMD 0.34) as exceeding even the 0.20 relaxed tolerance, unlike every other
        # covariate. Reported here rather than silently left as a caveat: (1) the raw
        # candidate-vs-decoy distributions, since the IQR is degenerate for both (a
        # discrete, narrow-range covariate) and a bare SMD doesn't show why; (2) whether
        # CNNaffinity/pass rate actually differ by halogen count among decoys, and (3) a
        # halogen-adjusted logistic model, so the HAC/cLogP result above isn't confounded
        # by the one covariate matching could not balance.
        candidate_reference = pd.read_csv(OUT_DIR / "candidate_reference_v1.0.csv")
        cand_halogen = candidate_reference["halogen_count"]
        decoy_halogen_all = matched_decoys["decoy_halogen_count"]

        def bucket_proportions(s: pd.Series) -> dict:
            n = len(s)
            buckets = {"0": int((s == 0).sum()), "1": int((s == 1).sum()),
                       "2": int((s == 2).sum()), ">2": int((s > 2).sum())}
            return {k: {"n": v, "pct": round(100 * v / n, 1)} for k, v in buckets.items()}

        size_bias["halogen_count_balance"] = {
            "candidate_n": int(len(cand_halogen)),
            "candidate_mean": round(float(cand_halogen.mean()), 4),
            "candidate_median": float(cand_halogen.median()),
            "candidate_range": [int(cand_halogen.min()), int(cand_halogen.max())],
            "candidate_value_counts": {int(k): int(v) for k, v in cand_halogen.value_counts().sort_index().items()},
            "candidate_proportions_0_1_2_gt2": bucket_proportions(cand_halogen),
            "decoy_n": int(len(decoy_halogen_all)),
            "decoy_mean": round(float(decoy_halogen_all.mean()), 4),
            "decoy_median": float(decoy_halogen_all.median()),
            "decoy_range": [int(decoy_halogen_all.min()), int(decoy_halogen_all.max())],
            "decoy_value_counts": {int(k): int(v) for k, v in decoy_halogen_all.value_counts().sort_index().items()},
            "decoy_proportions_0_1_2_gt2": bucket_proportions(decoy_halogen_all),
            "smd": 0.3385,  # from matching_balance.csv; recomputed here only for the raw distributions
        }
        decoy_props_h = decoy_props.dropna(subset=["decoy_halogen_count"])
        if len(decoy_props_h) > 5:
            rho_h, pval_h = stats.spearmanr(decoy_props_h["top1_cnnaffinity"], decoy_props_h["decoy_halogen_count"])
            size_bias["spearman_cnnaffinity_vs_halogen"] = {"rho": round(float(rho_h), 4), "p": round(float(pval_h), 5)}
            mono = decoy_props_h[decoy_props_h["decoy_halogen_count"] <= 1]
            multi = decoy_props_h[decoy_props_h["decoy_halogen_count"] >= 2]
            if len(mono) > 0 and len(multi) > 0:
                size_bias["pass_rate_by_halogen_stratum"] = {
                    "monohalogenated_or_fewer": {
                        "n": int(len(mono)), "n_pass": int(mono["structural_proxy_pass"].sum()),
                        "pass_rate": round(float(mono["structural_proxy_pass"].mean()), 4),
                    },
                    "dihalogenated_or_more": {
                        "n": int(len(multi)), "n_pass": int(multi["structural_proxy_pass"].sum()),
                        "pass_rate": round(float(multi["structural_proxy_pass"].mean()), 4),
                    },
                }
            try:
                import statsmodels.api as sm
                Xh = sm.add_constant(decoy_props_h[["decoy_hac", "decoy_clogp", "decoy_halogen_count"]].astype(float))
                yh = decoy_props_h["structural_proxy_pass"].astype(int)
                model_h = sm.Logit(yh, Xh).fit(disp=0)
                size_bias["logit_pass_on_hac_clogp_halogen"] = {k: round(v, 4) for k, v in model_h.params.items()}
                size_bias["logit_pass_on_hac_clogp_halogen_pvalues"] = {k: round(v, 4) for k, v in model_h.pvalues.items()}
            except Exception as exc:
                size_bias["logit_halogen_note"] = f"halogen-adjusted logistic model skipped: {exc}"

    report = {
        "embedding_reproducibility_diagnostic": repro,
        "posthoc_amended_samebatch_analysis": {
            "note": "Post-hoc amended same-batch analysis: candidates and decoys docked in the same blinded batch, emphasized as the less-confounded DESCRIPTIVE estimate (not a confirmatory primary analysis -- this emphasis was adopted after inspecting results; see decoy_addendum_v1.0.md's amendment log).",
            "p_candidate_samebatch": round(p_cand_samebatch, 4), "n_candidate_pass": n_cand_samebatch_pass, "n_candidate": len(redocked_cands),
            "p_decoy": round(p_decoy, 4), "n_decoy_pass": n_decoy_pass, "n_decoy": len(decoys),
            "p_decoy_cluster_bootstrap_95ci": [round(float(x), 4) for x in p_decoy_ci_samebatch],
            "bootstrap_interval_caveat": repro.get("bootstrap_interval_caveat"),
            "risk_difference_candidate_minus_decoy": round(p_cand_samebatch - p_decoy, 4),
            "risk_difference_95ci": [round(float(x), 4) for x in delta_ci_samebatch],
            "risk_ratio_candidate_over_decoy": round(rr_samebatch, 4) if np.isfinite(rr_samebatch) else None,
            "risk_ratio_95ci": [round(float(x), 4) if np.isfinite(x) else None for x in rr_ci_samebatch],
            "interpretation": interpretation_samebatch,
        },
        "preregistered_crossrun_analysis_confounded": {
            "note": "Preregistered cross-run analysis, subsequently identified as confounded: as originally pre-registered in decoy_addendum_v1.0.md, decoy rate vs. the FROZEN primary 16/69. Retained, not withdrawn -- known to be confounded by cross-run embedding variance (see embedding_reproducibility_diagnostic).",
            "p_candidate_frozen_16_of_69": FROZEN_CANDIDATE_RATE,
            "p_decoy": round(p_decoy, 4), "n_decoy_pass": n_decoy_pass, "n_decoy": len(decoys),
            "risk_difference_candidate_minus_decoy": round(FROZEN_CANDIDATE_RATE - p_decoy, 4),
            "risk_difference_95ci": [round(float(x), 4) for x in delta_ci_prereg],
            "risk_ratio_candidate_over_decoy": round(rr_prereg, 4) if np.isfinite(rr_prereg) else None,
            "risk_ratio_95ci": [round(float(x), 4) if np.isfinite(x) else None for x in rr_ci_prereg],
            "interpretation": interpretation_prereg,
        },
        "n_bootstrap_resamples": args.n_boot,
        "n_matched_clusters": len(decoy_pass_by_cand),
        "stage_decomposition_decoys": stage_rows,
        "gate_mechanism_table_3keh": gate_mechanism_rows,
        "gate_mechanism_interpretation": gate_mechanism_interpretation,
        "size_bias_checks": size_bias,
        "caveat": ("Decoys are not experimentally confirmed GCase inactives; this estimates background "
                   "acceptance/discrimination, not biological specificity or target-specific binding. Without "
                   "measured affinities, the CNNaffinity-HAC association below cannot distinguish model bias "
                   "from a genuine physical size-affinity relationship."),
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(args.out_dir / "decoy_specificity_report.json", "w") as fh:
        json.dump(report, fh, indent=2)
    stage_df.to_csv(args.out_dir / "decoy_gate_audit.csv", index=False)
    gate_mechanism_df.to_csv(args.out_dir / "decoy_gate_mechanism_3keh.csv", index=False)

    lines = ["# Decoy-panel structural-proxy background-calibration report", "",
             "## Embedding-reproducibility diagnostic (discovered post-hoc)", ""]
    if repro:
        lines.append(f"Re-docking the 69 frozen candidates fresh in this batch gave "
                     f"{repro['this_run_redock_pass']}/{repro['n_candidates_compared']} passing, "
                     f"vs. the frozen primary run's {repro['frozen_primary_pass']}/{repro['n_candidates_compared']} -- "
                     f"{repro['n_flipped']} candidates ({repro['n_newly_passing']} newly passing, "
                     f"{repro['n_newly_failing']} newly failing) flipped status. "
                     f"CNNaffinity (redock - primary) ranged {repro['cnnaffinity_diff_redock_minus_primary']['min']} "
                     f"to {repro['cnnaffinity_diff_redock_minus_primary']['max']} "
                     f"(mean {repro['cnnaffinity_diff_redock_minus_primary']['mean']}).")
        lines.append("")
        lines.append(f"**Plausible major source:** {repro['plausible_major_source']}")
    lines.append("")
    lines.append("## Post-hoc amended same-batch analysis (emphasized descriptive estimate)")
    lines.append("")
    pa = report["posthoc_amended_samebatch_analysis"]
    lines.append(f"Candidates (this batch): {pa['n_candidate_pass']}/{pa['n_candidate']} = {pa['p_candidate_samebatch']*100:.1f}%")
    lines.append(f"Decoys: {pa['n_decoy_pass']}/{pa['n_decoy']} = {pa['p_decoy']*100:.1f}% "
                 f"(cluster-bootstrap 95% CI {pa['p_decoy_cluster_bootstrap_95ci'][0]*100:.1f}-{pa['p_decoy_cluster_bootstrap_95ci'][1]*100:.1f}%)")
    lines.append(f"Risk difference = {pa['risk_difference_candidate_minus_decoy']*100:.1f} pp "
                 f"(95% CI {pa['risk_difference_95ci'][0]*100:.1f}-{pa['risk_difference_95ci'][1]*100:.1f})")
    if pa["risk_ratio_candidate_over_decoy"] is not None:
        lines.append(f"Risk ratio = {pa['risk_ratio_candidate_over_decoy']:.2f} "
                     f"(95% CI {pa['risk_ratio_95ci'][0]:.2f}-{pa['risk_ratio_95ci'][1]:.2f})")
    if pa.get("bootstrap_interval_caveat"):
        lines.append(f"*{pa['bootstrap_interval_caveat']}*")
    lines.append("")
    lines.append(f"**Interpretation:** {pa['interpretation']} The panel therefore provides, at most, weak and "
                 f"inconclusive evidence that the gate distinguishes pipeline candidates from this property-matched "
                 f"background. Because the decoys are not experimentally confirmed GCase inactives, the experiment "
                 f"does not estimate biological specificity or target-specific binding.")
    lines.append("")
    lines.append("## Gate mechanism (3KEH, marginal breakdown)")
    lines.append("")
    lines.append(gate_mechanism_df.to_markdown(index=False))
    lines.append("")
    if gate_mechanism_interpretation:
        lines.append(gate_mechanism_interpretation)
        lines.append("")
    lines.append("## Size-bias and covariate-balance checks")
    lines.append("")
    if "spearman_cnnaffinity_vs_hac" in size_bias:
        s = size_bias["spearman_cnnaffinity_vs_hac"]
        lines.append(f"Spearman(CNNaffinity, HAC) among decoys: rho={s['rho']}, p={s['p']}.")
    if "logit_pass_on_hac_clogp" in size_bias:
        lines.append(f"Logistic pass~HAC+cLogP coefficients: {size_bias['logit_pass_on_hac_clogp']} "
                     f"(p-values: {size_bias['logit_pass_on_hac_clogp_pvalues']}).")
    if "halogen_count_balance" in size_bias:
        hb = size_bias["halogen_count_balance"]
        lines.append("")
        lines.append(f"**Halogen-count balance** (matching_balance.csv: SMD={hb['smd']}, the only covariate "
                     f"exceeding even the 0.20 relaxed tolerance): candidates (n={hb['candidate_n']}) mean="
                     f"{hb['candidate_mean']}, median={hb['candidate_median']}, range={hb['candidate_range']}, "
                     f"value counts {hb['candidate_value_counts']}; decoys (n={hb['decoy_n']}) mean="
                     f"{hb['decoy_mean']}, median={hb['decoy_median']}, range={hb['decoy_range']}, value counts "
                     f"{hb['decoy_value_counts']}. IQR is degenerate (2-2) for both populations -- this is a "
                     f"discrete, narrow-range covariate, so mean/value-counts are more informative than IQR here.")
        lines.append(f"Proportions with 0/1/2/>2 halogens -- candidates: {hb['candidate_proportions_0_1_2_gt2']}; "
                     f"decoys: {hb['decoy_proportions_0_1_2_gt2']}.")
        if "spearman_cnnaffinity_vs_halogen" in size_bias:
            s2 = size_bias["spearman_cnnaffinity_vs_halogen"]
            lines.append(f"Spearman(CNNaffinity, halogen count) among decoys: rho={s2['rho']}, p={s2['p']}.")
        if "pass_rate_by_halogen_stratum" in size_bias:
            st = size_bias["pass_rate_by_halogen_stratum"]
            mono, multi = st["monohalogenated_or_fewer"], st["dihalogenated_or_more"]
            lines.append(f"Structural-proxy pass rate by halogen stratum (decoys): "
                        f"<=1 halogen {mono['n_pass']}/{mono['n']} ({mono['pass_rate']*100:.1f}%) vs. "
                        f">=2 halogens {multi['n_pass']}/{multi['n']} ({multi['pass_rate']*100:.1f}%).")
        if "logit_pass_on_hac_clogp_halogen" in size_bias:
            lines.append(f"Halogen-adjusted logistic pass~HAC+cLogP+halogen_count coefficients: "
                        f"{size_bias['logit_pass_on_hac_clogp_halogen']} "
                        f"(p-values: {size_bias['logit_pass_on_hac_clogp_halogen_pvalues']}).")
    lines.append("")
    lines.append("## Preregistered cross-run analysis, subsequently identified as confounded")
    lines.append("")
    sa = report["preregistered_crossrun_analysis_confounded"]
    lines.append(f"Candidates (frozen primary): 16/69 = {sa['p_candidate_frozen_16_of_69']*100:.1f}%")
    lines.append(f"Decoys (this batch): {sa['n_decoy_pass']}/{sa['n_decoy']} = {sa['p_decoy']*100:.1f}%")
    if sa["risk_ratio_candidate_over_decoy"] is not None:
        lines.append(f"Risk ratio = {sa['risk_ratio_candidate_over_decoy']:.2f} "
                     f"(95% CI {sa['risk_ratio_95ci'][0]:.2f}-{sa['risk_ratio_95ci'][1]:.2f})")
    lines.append("")
    lines.append(f"**Interpretation:** {sa['interpretation']}")
    lines.append("")
    lines.append(f"**Caveat:** {report['caveat']}")
    (args.out_dir / "decoy_specificity_report.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

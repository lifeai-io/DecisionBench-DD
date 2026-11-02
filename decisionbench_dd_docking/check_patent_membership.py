#!/usr/bin/env python3
"""Patent-literature membership check for the 16 frozen primary
candidate-screen passers, plus Ambroxol as a sanity control
(decisionbench_dd_configs_v1.0/candidate_screen_v1.0/downstream_gcase_screening_protocol.md,
section 11 "... and patent proximity").

Uses molbloom (https://pypi.org/project/molbloom/) against its 'surechembl'
catalog: a Bloom filter over ~30.9M molecules text-mined from full-text
patent documents (EPO/USPTO/WIPO) by EBI's SureChEMBL project. False
positive rate 0.000025 (negligible for this population size); a downloaded,
externally-hosted binary artifact (~200 MB, cached at
~/.cache/molbloom/surechembl.bloom on first use) -- its SHA-256 is recorded
in the output for provenance, same treatment as this project's Docker image
digests, since it is not independently re-derivable from source.

Scope, stated plainly: this is an EXACT-STRUCTURE membership test (by
canonical SMILES/InChI, not similarity), so it answers "has this precise
molecule been text-mined out of at least one indexed patent" -- nothing
more. It is explicitly NOT: a similarity-based proximity search (a close
analogue one bond away from a patented compound will not be flagged), a
freedom-to-operate or patentability legal opinion, or a claim-scope
analysis. False negatives are expected and normal for genuinely novel
generated analogues; a True hit is a stronger signal than a False miss
(SureChEMBL's coverage of patent chemistry, while large, is not
exhaustive). Sanity-checked against Ambroxol itself (a marketed, patented
drug), which must return True.

Also reports ZINC-instock membership (molbloom's bundled
zinc-instock-mini catalog, no download needed) as a complementary,
already-available signal: whether the exact molecule is a known
purchasable screening/building-block compound, relevant to both synthesis-
feasibility and "how novel is this really" framing alongside the patent
check.

Usage:
    python -m decisionbench_dd_docking.check_patent_membership
"""
from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

from decisionbench_dd_docking.predict_admet import AMBROXOL_SMILES
from decisionbench_dd_docking.triage_primary_candidates import CANDIDATE_RESULTS, load_passing_candidates

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "candidate_screen_results"
SURECHEMBL_CACHE = Path.home() / ".cache" / "molbloom" / "surechembl.bloom"


def main(argv=None) -> int:
    if not CANDIDATE_RESULTS.is_file():
        print(f"ERROR: {CANDIDATE_RESULTS} not found -- run score_candidate_screen.py first.", file=sys.stderr)
        return 1

    import molbloom

    candidates = load_passing_candidates()
    ligands = [("CTRL_AMBROXOL", AMBROXOL_SMILES)] + [(c["candidate_id"], c["canonical_smiles"]) for c in candidates]

    rows = []
    for ligand_id, smiles in ligands:
        rows.append({
            "candidate_id": ligand_id,
            "canonical_smiles": smiles,
            "in_surechembl_patent_literature": molbloom.buy(smiles, catalog="surechembl"),
            "in_zinc_instock_purchasable": molbloom.buy(smiles, catalog="zinc-instock-mini"),
        })

    ambroxol_row = rows[0]
    if not ambroxol_row["in_surechembl_patent_literature"]:
        print(
            "ERROR: sanity check failed -- Ambroxol (a marketed, patented drug) was NOT "
            "found in SureChEMBL. Do not trust these results without investigating "
            "(stale/corrupt cache, wrong SMILES, or a molbloom regression).",
            file=sys.stderr,
        )
        return 1

    out_csv = OUT_DIR / "patent_membership.csv"
    with open(out_csv, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    n_in_patents = sum(1 for r in rows[1:] if r["in_surechembl_patent_literature"])
    purchasable_ids = [r["candidate_id"] for r in rows[1:] if r["in_zinc_instock_purchasable"]]
    n_purchasable = len(purchasable_ids)
    no_hit_ids = [r["candidate_id"] for r in rows[1:] if not r["in_surechembl_patent_literature"] and not r["in_zinc_instock_purchasable"]]

    filter_sha256 = hashlib.sha256(SURECHEMBL_CACHE.read_bytes()).hexdigest() if SURECHEMBL_CACHE.is_file() else None

    lines = [
        "# Patent-literature and purchasable-catalog membership: 16 primary candidates",
        "",
        "Exact-structure membership only (molbloom/SureChEMBL Bloom filter, FPR 0.000025), "
        "NOT a similarity-based patent-proximity search, freedom-to-operate opinion, or "
        "claim-scope analysis. Sanity-checked against Ambroxol (a marketed patented drug), "
        "which correctly returns True.",
        "",
        f"SureChEMBL filter provenance: {SURECHEMBL_CACHE} "
        f"(SHA-256: {filter_sha256 if filter_sha256 else 'N/A -- file not found locally'}). "
        "This is a downloaded, externally-hosted artifact, not re-derivable from source; "
        "record this hash to know if a later run used a different filter version.",
        "",
        f"Ambroxol control: in_surechembl={ambroxol_row['in_surechembl_patent_literature']} "
        "(sanity check passed).",
        f"Of the 16 primary candidates: {n_in_patents}/16 found in SureChEMBL (exact-structure "
        f"patent-literature hit), {n_purchasable}/16 found in ZINC in-stock (known purchasable "
        f"compound).",
        f"{len(no_hit_ids)}/16 candidates are in NEITHER database: "
        f"{', '.join(no_hit_ids) if no_hit_ids else 'none'}. Per external review, this must be "
        "read narrowly as: **no exact-structure membership detected in the tested SureChEMBL "
        "Bloom-filter snapshot (or ZINC in-stock)**. A Bloom filter is a membership mechanism, "
        "not a similarity, Markush-claim, tautomer/salt, or freedom-to-operate search; "
        "canonicalization choices and database coverage gaps can still cause relevant prior art "
        "to be missed. This is NOT a novelty or patentability claim.",
        "",
        (
            f"{', '.join(purchasable_ids)} (ZINC in-stock hit{'s' if n_purchasable != 1 else ''}) "
            "being purchasable is operationally useful for rapid assay procurement, but that also "
            "specifically warrants a direct compound-identity and prior-art check before treating "
            "it as available for unencumbered use."
            if purchasable_ids else
            "No candidate matched a known purchasable ZINC in-stock compound."
        ),
        "",
        "| Candidate | In SureChEMBL (patent lit.) | In ZINC in-stock (purchasable) |",
        "| --- | :---: | :---: |",
    ]
    for r in rows:
        lines.append(f"| {r['candidate_id']} | {r['in_surechembl_patent_literature']} | {r['in_zinc_instock_purchasable']} |")
    (OUT_DIR / "patent_membership.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv} and patent_membership.md ({len(rows)} molecules, {n_in_patents}/16 candidates in SureChEMBL)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

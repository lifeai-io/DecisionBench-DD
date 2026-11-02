"""Per-molecule chemistry metrics for the DecisionBench-DD generator scorecard.

All molecules are re-canonicalized and re-scored by this common evaluator so that
GenMol and MolMIM outputs are compared on identical, tool-independent definitions
(see decisionbench_dd_configs_v1.0/common_protocol.json: "Canonicalize molecules
only in the common downstream evaluation pipeline"). Each tool's own self-reported
`score` field is carried through as `api_score` for audit purposes only and is
never used in a metric.

Structural alerts (v1.2, decisionbench_dd_configs_v1.0/qualification_gates_v1.0.json):
PAINS and Brenk are scored as two separate catalogs. PAINS remains an absolute gate
(N_PAINS = 0). Brenk is seed-relative and INSTANCE-aware (v1.2 supersedes v1.1's
plain type-level set difference, which could not tell "the seed's own aniline" apart
from "an unrelated second aniline elsewhere"). Each Brenk alert occurrence in the
seed is recorded with its own matched atom indices; a candidate's occurrence is
"seed_inherited" only if it has the same alert type AND its atoms equal the seed
instance's atoms mapped onto the candidate via a maximum-common-substructure (MCS)
atom correspondence. Any occurrence that doesn't map to a seed instance -- including
a second, unmapped occurrence of an already-allowlisted type, or the seed's alert
relocated to a different position -- counts as new. See
qualification_gates_v1.0.json:seed_relative_alert_rule for the full rationale.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from rdkit import Chem, RDLogger
from rdkit.Chem import Crippen, Descriptors, QED, rdFingerprintGenerator, rdFMCS, rdMolDescriptors
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog("rdApp.*")

_VENDOR_DIR = Path(__file__).parent / "vendor" / "sascorer"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))
import sascorer  # noqa: E402  (vendored RDKit Contrib/SA_Score, BSD license)

_MORGAN_RADIUS = 2
_MORGAN_NBITS = 2048
_morgan_gen = rdFingerprintGenerator.GetMorganGenerator(radius=_MORGAN_RADIUS, fpSize=_MORGAN_NBITS)

_PAINS_CATALOG: Optional[FilterCatalog] = None
_BRENK_CATALOG: Optional[FilterCatalog] = None


def _pains_catalog() -> FilterCatalog:
    global _PAINS_CATALOG
    if _PAINS_CATALOG is None:
        params = FilterCatalogParams()
        for name in ("PAINS_A", "PAINS_B", "PAINS_C"):
            params.AddCatalog(getattr(FilterCatalogParams.FilterCatalogs, name))
        _PAINS_CATALOG = FilterCatalog(params)
    return _PAINS_CATALOG


def _brenk_catalog() -> FilterCatalog:
    global _BRENK_CATALOG
    if _BRENK_CATALOG is None:
        params = FilterCatalogParams()
        params.AddCatalog(FilterCatalogParams.FilterCatalogs.BRENK)
        _BRENK_CATALOG = FilterCatalog(params)
    return _BRENK_CATALOG


def canonicalize(smiles: str) -> Optional[str]:
    """Return the RDKit canonical SMILES, or None if the string does not parse."""
    if not smiles:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Chem.MolToSmiles(mol)


def morgan_fingerprint(smiles: str):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return _morgan_gen.GetFingerprint(mol)


def pains_alert_types(mol) -> list[str]:
    """Sorted, deduplicated PAINS alert-type identifiers triggered by `mol`."""
    return sorted({entry.GetDescription() for entry in _pains_catalog().GetMatches(mol)})


def get_brenk_instances(mol) -> list[tuple[str, frozenset]]:
    """Every Brenk alert OCCURRENCE in `mol` as (alert_type, matched_atom_indices).

    NOTE: `FilterCatalogEntry.GetFilterMatches(mol)` only returns the FIRST
    occurrence of a pattern per entry, even when a molecule has several disjoint
    matches (verified directly: benzidine, Nc1ccccc1-c1ccc(N)cc1, has two
    chemically separate anilines but GetFilterMatches reports one). To actually
    enumerate every occurrence -- required for instance-aware seed-relative
    classification -- this pulls each entry's underlying SMARTS query mol via
    `GetPattern()` and matches it directly with `GetSubstructMatches(uniquify=True)`.
    """
    instances = []
    for entry in _brenk_catalog().GetMatches(mol):
        first_matches = entry.GetFilterMatches(mol)
        if not first_matches:
            continue
        pattern = first_matches[0].filterMatch.GetPattern()
        for match in mol.GetSubstructMatches(pattern, uniquify=True):
            instances.append((entry.GetDescription(), frozenset(match)))
    return instances


@dataclass(frozen=True)
class SeedAlertInstance:
    seed_instance_id: str
    alert_type: str
    atom_indices: frozenset


def compute_seed_brenk_instances(seed_mol) -> list[SeedAlertInstance]:
    """M_seed: the seed's own Brenk alert occurrences, each with a stable id.
    See decisionbench_dd_configs_v1.0/seed_alert_catalog.json for the frozen,
    audited record of this same set (including atom indices)."""
    raw = sorted(get_brenk_instances(seed_mol), key=lambda x: (x[0], sorted(x[1])))
    return [
        SeedAlertInstance(seed_instance_id=f"BRENK_SEED_{i + 1:03d}", alert_type=t, atom_indices=atoms)
        for i, (t, atoms) in enumerate(raw)
    ]


_MCS_ATOM_COMPARE = rdFMCS.AtomCompare.CompareElements
_MCS_BOND_COMPARE = rdFMCS.BondCompare.CompareOrder
_MCS_TIMEOUT_SECONDS = 10


def seed_to_candidate_atom_map(seed_mol, candidate_mol) -> tuple[dict, bool]:
    """f: seed atom index -> candidate atom index, via each mol's first substructure
    match against their MCS query (both matches are ordered by the same query atom
    order, so zipping them gives the correspondence). Returns (mapping, timed_out).

    Known simplification: GetSubstructMatch returns only the first match RDKit
    finds. For a seed or candidate with symmetry-equivalent substructures, a
    different, equally valid mapping could exist; this is not resolved by trying
    all automorphisms. Documented here, not silently assumed away -- revisit if it
    causes a misclassification on real data.
    """
    result = rdFMCS.FindMCS(
        [seed_mol, candidate_mol],
        timeout=_MCS_TIMEOUT_SECONDS,
        ringMatchesRingOnly=True,
        atomCompare=_MCS_ATOM_COMPARE,
        bondCompare=_MCS_BOND_COMPARE,
    )
    if result.numAtoms == 0 or not result.smartsString:
        return {}, result.canceled
    query = Chem.MolFromSmarts(result.smartsString)
    if query is None:
        return {}, result.canceled
    seed_match = seed_mol.GetSubstructMatch(query)
    cand_match = candidate_mol.GetSubstructMatch(query)
    if not seed_match or not cand_match:
        return {}, result.canceled
    return dict(zip(seed_match, cand_match)), result.canceled


def classify_brenk_instances(candidate_mol, seed_mol, seed_instances: list[SeedAlertInstance]) -> dict:
    """v1.2 instance-aware classification: an occurrence in the candidate is
    seed_inherited only if some seed instance of the SAME alert type maps, atom
    for atom via the seed->candidate correspondence, onto EXACTLY that occurrence's
    matched atoms. Everything else -- a new type, a second unmapped occurrence of
    an allowlisted type, or the seed's alert relocated elsewhere -- is new."""
    cand_instances = get_brenk_instances(candidate_mol)
    if not cand_instances:
        return {"instances": [], "new_count": 0, "seed_inherited_count": 0, "mapping_timed_out": False}

    atom_map, timed_out = seed_to_candidate_atom_map(seed_mol, candidate_mol)

    mapped_seed = []
    for si in seed_instances:
        if si.atom_indices and all(a in atom_map for a in si.atom_indices):
            mapped_seed.append((si.seed_instance_id, si.alert_type, frozenset(atom_map[a] for a in si.atom_indices)))
        else:
            mapped_seed.append((si.seed_instance_id, si.alert_type, None))

    instances = []
    for alert_type, atoms in cand_instances:
        matched_seed_id = None
        for sid, stype, mapped_atoms in mapped_seed:
            if stype == alert_type and mapped_atoms is not None and mapped_atoms == atoms:
                matched_seed_id = sid
                break
        classification = "seed_inherited" if matched_seed_id else "new_unmapped"
        instances.append(
            {
                "alert_type": alert_type,
                "matched_atom_indices": sorted(atoms),
                "classification": classification,
                "seed_instance_id": matched_seed_id,
            }
        )

    new_count = sum(1 for i in instances if i["classification"] == "new_unmapped")
    return {
        "instances": instances,
        "new_count": new_count,
        "seed_inherited_count": len(instances) - new_count,
        "mapping_timed_out": timed_out,
    }


@dataclass
class MoleculeRecord:
    """One generated candidate after common-evaluator scoring."""

    tool: str
    run_id: str
    raw_smiles: str
    api_score: Optional[float]
    valid: bool
    canonical_smiles: Optional[str] = None
    exact_seed_match: bool = False
    tanimoto_to_seed: Optional[float] = None
    qed: Optional[float] = None
    sa_score: Optional[float] = None
    mw: Optional[float] = None
    clogp: Optional[float] = None
    tpsa: Optional[float] = None
    hbd: Optional[int] = None
    hba: Optional[int] = None
    murcko_scaffold_smiles: Optional[str] = None
    scaffold_matches_seed: bool = False
    # PAINS: absolute gate, not seed-relative (qualification_gates_v1.0.json Section 5).
    pains_alerts: list = field(default_factory=list)
    passes_pains_gate: bool = True
    # Brenk: instance-aware, seed-relative (v1.2). brenk_alert_instances is the
    # full per-occurrence record; brenk_alerts_all/seed_inherent/new are
    # type-level summaries derived from it (a type can appear in both
    # seed_inherent and new if one occurrence is inherited and another is not).
    brenk_alert_instances: list = field(default_factory=list)
    brenk_alerts_all: list = field(default_factory=list)
    brenk_alerts_seed_inherent: list = field(default_factory=list)
    brenk_alerts_new: list = field(default_factory=list)
    n_seed_inherited_alert_instances: int = 0
    n_new_alert_instances: int = 0
    alert_mapping_timed_out: bool = False
    passes_seed_relative_alert_gate: bool = True
    is_first_occurrence_in_run: bool = False


def score_molecule(
    tool: str,
    run_id: str,
    raw_smiles: str,
    api_score: Optional[float],
    seed_canonical_smiles: str,
    seed_mol,
    seed_fingerprint,
    seed_scaffold_smiles: str,
    seed_brenk_instances: list[SeedAlertInstance],
) -> MoleculeRecord:
    """Compute every common-evaluator metric for a single generated SMILES."""
    mol = Chem.MolFromSmiles(raw_smiles) if raw_smiles else None
    if mol is None:
        return MoleculeRecord(tool=tool, run_id=run_id, raw_smiles=raw_smiles, api_score=api_score, valid=False)

    canonical = Chem.MolToSmiles(mol)
    fp = _morgan_gen.GetFingerprint(mol)
    tanimoto = Chem.DataStructs.TanimotoSimilarity(fp, seed_fingerprint)

    scaffold_mol = MurckoScaffold.GetScaffoldForMol(mol)
    scaffold_smiles = Chem.MolToSmiles(scaffold_mol) if scaffold_mol is not None else ""

    pains = pains_alert_types(mol)
    brenk = classify_brenk_instances(mol, seed_mol, seed_brenk_instances)

    all_types = sorted({i["alert_type"] for i in brenk["instances"]})
    seed_inherited_types = sorted({i["alert_type"] for i in brenk["instances"] if i["classification"] == "seed_inherited"})
    new_types = sorted({i["alert_type"] for i in brenk["instances"] if i["classification"] == "new_unmapped"})

    return MoleculeRecord(
        tool=tool,
        run_id=run_id,
        raw_smiles=raw_smiles,
        api_score=api_score,
        valid=True,
        canonical_smiles=canonical,
        exact_seed_match=(canonical == seed_canonical_smiles),
        tanimoto_to_seed=float(tanimoto),
        qed=float(QED.qed(mol)),
        sa_score=float(sascorer.calculateScore(mol)),
        mw=float(Descriptors.MolWt(mol)),
        clogp=float(Crippen.MolLogP(mol)),
        tpsa=float(Descriptors.TPSA(mol)),
        hbd=int(rdMolDescriptors.CalcNumHBD(mol)),
        hba=int(rdMolDescriptors.CalcNumHBA(mol)),
        murcko_scaffold_smiles=scaffold_smiles,
        scaffold_matches_seed=(scaffold_smiles == seed_scaffold_smiles and scaffold_smiles != ""),
        pains_alerts=pains,
        passes_pains_gate=(len(pains) == 0),
        brenk_alert_instances=brenk["instances"],
        brenk_alerts_all=all_types,
        brenk_alerts_seed_inherent=seed_inherited_types,
        brenk_alerts_new=new_types,
        n_seed_inherited_alert_instances=brenk["seed_inherited_count"],
        n_new_alert_instances=brenk["new_count"],
        alert_mapping_timed_out=brenk["mapping_timed_out"],
        passes_seed_relative_alert_gate=(brenk["new_count"] == 0),
    )


def seed_scaffold_smiles(seed_canonical_smiles: str) -> str:
    mol = Chem.MolFromSmiles(seed_canonical_smiles)
    scaffold_mol = MurckoScaffold.GetScaffoldForMol(mol)
    return Chem.MolToSmiles(scaffold_mol) if scaffold_mol is not None else ""


def internal_diversity(canonical_smiles_list: list[str]) -> Optional[float]:
    """1 - mean pairwise Tanimoto over a set of (already-deduplicated) molecules."""
    from rdkit import DataStructs

    if len(canonical_smiles_list) < 2:
        return None
    fps = [morgan_fingerprint(s) for s in canonical_smiles_list]
    fps = [fp for fp in fps if fp is not None]
    if len(fps) < 2:
        return None
    total, count = 0.0, 0
    for i in range(len(fps) - 1):
        sims = DataStructs.BulkTanimotoSimilarity(fps[i], fps[i + 1 :])
        total += sum(sims)
        count += len(sims)
    if count == 0:
        return None
    return 1.0 - (total / count)

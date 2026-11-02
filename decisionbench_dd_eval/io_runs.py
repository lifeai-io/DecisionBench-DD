"""Loading of run manifests and raw GenMol/MolMIM NIM responses.

A "run" is one (tool, run_id) replicate, described by a manifest following
decisionbench_dd_configs_v1.0/run_manifest_template.json and pointing at a raw
API response file. This module never trusts filenames for tool/run identity --
only the manifest's own `tool` / `run_id` fields, so mislabeled files fail loudly
instead of silently corrupting the comparison.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

REQUIRED_MANIFEST_FIELDS = (
    "tool",
    "run_id",
    "raw_response_file",
    "requested_molecules",
)

_PLACEHOLDER_MARKERS = ("<required>", "<filename>", "<genmol|molmim>", "<replicate_01|replicate_02|replicate_03>")


class ManifestError(ValueError):
    pass


@dataclass
class Molecule:
    raw_smiles: str
    api_score: Optional[float]


@dataclass
class RunRecord:
    tool: str
    run_id: str
    manifest_path: Path
    raw_response_path: Path
    requested_molecules: int
    runtime_seconds: Optional[float]
    molecules: list[Molecule]


def _check_not_placeholder(field_name: str, value, manifest_path: Path) -> None:
    if isinstance(value, str) and value in _PLACEHOLDER_MARKERS:
        raise ManifestError(
            f"{manifest_path}: field '{field_name}' still holds a template placeholder ({value!r}); "
            "fill in the real run manifest before evaluating."
        )


def load_manifest(manifest_path: Path) -> dict:
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    missing = [f for f in REQUIRED_MANIFEST_FIELDS if f not in manifest]
    if missing:
        raise ManifestError(f"{manifest_path}: missing required field(s): {missing}")
    for f in REQUIRED_MANIFEST_FIELDS:
        _check_not_placeholder(f, manifest.get(f), manifest_path)
    if manifest["tool"] not in ("genmol", "molmim"):
        raise ManifestError(f"{manifest_path}: unknown tool {manifest['tool']!r} (expected 'genmol' or 'molmim')")
    return manifest


def _parse_genmol_raw(raw: dict, manifest_path: Path) -> list[Molecule]:
    if "molecules" not in raw:
        raise ManifestError(f"{manifest_path}: GenMol raw response missing 'molecules' key")
    out = []
    for entry in raw["molecules"]:
        out.append(Molecule(raw_smiles=entry.get("smiles", ""), api_score=entry.get("score")))
    return out


def _parse_molmim_raw(raw: dict, manifest_path: Path) -> list[Molecule]:
    """MolMIM's hosted NIM response (health.api.nvidia.com/v1/biology/nvidia/molmim/generate)
    is {"molecules": "<JSON-encoded string>", "score_type": "..."} -- `molecules` is a
    STRING containing a JSON array of {"sample","score"}, not the array itself. Verified
    directly against a live API call before this parser was written; handled defensively
    in case a future API version returns an already-decoded list instead."""
    if "molecules" not in raw:
        raise ManifestError(f"{manifest_path}: MolMIM raw response missing 'molecules' key")
    payload = raw["molecules"]
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ManifestError(f"{manifest_path}: MolMIM 'molecules' string is not valid JSON: {exc}") from exc
    out = []
    for entry in payload:
        out.append(Molecule(raw_smiles=entry.get("sample", ""), api_score=entry.get("score")))
    return out


_PARSERS = {
    "genmol": _parse_genmol_raw,
    "molmim": _parse_molmim_raw,
}


def load_run(manifest_path: Path) -> RunRecord:
    manifest = load_manifest(manifest_path)
    raw_response_path = (manifest_path.parent / manifest["raw_response_file"]).resolve()
    if not raw_response_path.is_file():
        # also try relative to CWD, in case raw_response_file is an absolute-style path
        alt = Path(manifest["raw_response_file"])
        if alt.is_file():
            raw_response_path = alt
        else:
            raise ManifestError(
                f"{manifest_path}: raw_response_file {manifest['raw_response_file']!r} not found "
                f"(looked at {raw_response_path})"
            )

    with open(raw_response_path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    molecules = _PARSERS[manifest["tool"]](raw, manifest_path)

    runtime_seconds = manifest.get("runtime_seconds")
    if isinstance(runtime_seconds, str):
        runtime_seconds = None

    return RunRecord(
        tool=manifest["tool"],
        run_id=manifest["run_id"],
        manifest_path=manifest_path,
        raw_response_path=raw_response_path,
        requested_molecules=int(manifest["requested_molecules"]),
        runtime_seconds=float(runtime_seconds) if runtime_seconds is not None else None,
        molecules=molecules,
    )


def discover_manifests(manifest_dir: Path) -> list[Path]:
    return sorted(manifest_dir.glob("*.manifest.json"))

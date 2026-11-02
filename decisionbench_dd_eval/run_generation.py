#!/usr/bin/env python3
"""Executes the frozen primary GenMol/MolMIM generation requests against the
hosted NVIDIA NIM APIs and writes runs/ in the layout evaluate_generators.py
expects (see runs/README.md).

Endpoints and request/response shapes were verified directly against live API
calls before this script was written (not assumed from documentation, which
turned out to disagree with the real response on one point -- see
_parse_molmim_raw's docstring in io_runs.py):
  POST https://health.api.nvidia.com/v1/biology/nvidia/genmol/generate
  POST https://health.api.nvidia.com/v1/biology/nvidia/molmim/generate

Per common_protocol.json's rules, this script:
  - sends the exact same literal Ambroxol input SMILES to both tools' requests
    (already frozen identically in genmol_primary.json / molmim_primary.json),
  - sends every frozen config field verbatim (minus internal "_"-prefixed
    documentation keys) without alteration between replicates,
  - saves the raw API response before any RDKit/evaluator processing.

Usage:
    python -m decisionbench_dd_eval.run_generation --tool both --replicates 3
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from decisionbench_dd_eval.io_runs import ManifestError, _parse_genmol_raw, _parse_molmim_raw

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "decisionbench_dd_configs_v1.0"
DEFAULT_OUT_DIR = REPO_ROOT / "runs"
ENV_PATH = REPO_ROOT / ".env"

ENDPOINTS = {
    "genmol": "https://health.api.nvidia.com/v1/biology/nvidia/genmol/generate",
    "molmim": "https://health.api.nvidia.com/v1/biology/nvidia/molmim/generate",
}
CONFIG_FILES = {
    "genmol": CONFIG_DIR / "genmol_primary.json",
    "molmim": CONFIG_DIR / "molmim_primary.json",
}
_PARSERS = {
    "genmol": _parse_genmol_raw,
    "molmim": _parse_molmim_raw,
}
REQUEST_TIMEOUT_SECONDS = 300
RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
DELAY_BETWEEN_CALLS_SECONDS = 2.0


def load_api_key() -> str:
    key = None
    if ENV_PATH.is_file():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("NGC_API_KEY="):
                key = line.split("=", 1)[1].strip()
    import os

    key = os.environ.get("NGC_API_KEY", key)
    if not key:
        raise RuntimeError(f"NGC_API_KEY not found in environment or {ENV_PATH}")
    return key


def load_request_body(tool: str) -> dict:
    with open(CONFIG_FILES[tool], "r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    return {k: v for k, v in cfg.items() if not k.startswith("_")}


def call_api(tool: str, api_key: str, body: dict) -> tuple[int, str, float]:
    """Returns (http_status, raw_response_text, runtime_seconds)."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINTS[tool],
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    for attempt in range(1, MAX_RETRIES + 1):
        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                runtime = time.monotonic() - start
                return resp.status, resp.read().decode("utf-8"), runtime
        except urllib.error.HTTPError as exc:
            runtime = time.monotonic() - start
            body_text = exc.read().decode("utf-8", errors="replace")
            if exc.code in RETRY_STATUSES and attempt < MAX_RETRIES:
                backoff = 5.0 * attempt
                print(f"  [{tool}] HTTP {exc.code}, retrying in {backoff:.0f}s (attempt {attempt}/{MAX_RETRIES})", file=sys.stderr)
                time.sleep(backoff)
                continue
            return exc.code, body_text, runtime
        except urllib.error.URLError as exc:
            runtime = time.monotonic() - start
            if attempt < MAX_RETRIES:
                backoff = 5.0 * attempt
                print(f"  [{tool}] network error ({exc.reason}), retrying in {backoff:.0f}s", file=sys.stderr)
                time.sleep(backoff)
                continue
            return 0, json.dumps({"error": str(exc.reason)}), runtime
    raise RuntimeError("unreachable")  # pragma: no cover


def run_replicate(tool: str, run_id: str, body: dict, api_key: str, out_dir: Path) -> dict:
    print(f"[{tool}/{run_id}] requesting {body.get('num_molecules')} molecules...")
    started_at = datetime.now(timezone.utc)
    status, raw_text, runtime_seconds = call_api(tool, api_key, body)
    finished_at = datetime.now(timezone.utc)

    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{tool}_{run_id}.json"
    raw_path.write_text(raw_text, encoding="utf-8")

    returned_records = None
    parse_note = ""
    if status == 200:
        try:
            raw_json = json.loads(raw_text)
            molecules = _PARSERS[tool](raw_json, manifest_path=raw_path)
            returned_records = len(molecules)
        except (json.JSONDecodeError, ManifestError, KeyError) as exc:
            parse_note = f"WARNING: raw response saved but did not parse cleanly: {exc}"
            print(f"  [{tool}/{run_id}] {parse_note}", file=sys.stderr)
    else:
        parse_note = f"HTTP {status} -- see raw response for error detail"
        print(f"  [{tool}/{run_id}] {parse_note}", file=sys.stderr)

    manifest = {
        "benchmark": "DecisionBench-DD v1.0",
        "tool": tool,
        "run_id": run_id,
        "request_config_file": CONFIG_FILES[tool].name,
        "request_started_at_iso8601": started_at.isoformat(),
        "request_finished_at_iso8601": finished_at.isoformat(),
        "endpoint": ENDPOINTS[tool],
        "service_or_model_version": "hosted_api",
        "container_image_or_api_build": "hosted_api",
        "hardware": {"gpu_model": "hosted_api", "gpu_count": None, "peak_vram_gb": None},
        "runtime_seconds": round(runtime_seconds, 3),
        "http_status": status,
        "requested_molecules": body.get("num_molecules"),
        "returned_records": returned_records,
        "raw_response_file": f"raw/{raw_path.name}",
        "notes": parse_note,
    }
    manifest_path = out_dir / f"{tool}_{run_id}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    status_word = "OK" if status == 200 else "FAILED"
    print(f"  [{tool}/{run_id}] {status_word} (HTTP {status}, {runtime_seconds:.1f}s, {returned_records} molecules returned)")
    return manifest


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tool", choices=["genmol", "molmim", "both"], default="both")
    p.add_argument("--replicates", type=int, default=3)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    tools = ["genmol", "molmim"] if args.tool == "both" else [args.tool]
    api_key = load_api_key()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    manifests = []
    failures = 0
    for tool in tools:
        body = load_request_body(tool)
        for i in range(1, args.replicates + 1):
            run_id = f"replicate_{i:02d}"
            manifest = run_replicate(tool, run_id, dict(body), api_key, args.out_dir)
            manifests.append(manifest)
            if manifest["http_status"] != 200:
                failures += 1
            time.sleep(DELAY_BETWEEN_CALLS_SECONDS)

    print(f"\nDone: {len(manifests)} requests, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

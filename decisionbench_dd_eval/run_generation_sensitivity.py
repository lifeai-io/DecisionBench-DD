#!/usr/bin/env python3
"""Ad hoc MolMIM min_similarity sensitivity reruns (reviewer-requested, AI4DD round 2).

Not part of the frozen primary protocol (min_similarity=0.3, decisionbench_dd_configs_v1.0/
molmim_primary.json): this script takes the identical frozen request body and overrides only
min_similarity, writing to a separate out-dir so the frozen primary runs/ directory and its
results are untouched. Reuses run_generation.py's tested API-call/retry/manifest-writing logic
rather than duplicating it.

Usage:
    python -m decisionbench_dd_eval.run_generation_sensitivity --min-similarity 0.5 \\
        --out-dir runs_sensitivity/molmim_sim0.5 --replicates 3
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from decisionbench_dd_eval.io_runs import ManifestError
from decisionbench_dd_eval.run_generation import (
    DELAY_BETWEEN_CALLS_SECONDS,
    _PARSERS,
    ENDPOINTS,
    call_api,
    load_api_key,
    load_request_body,
)

TOOL = "molmim"


def run_replicate_sensitivity(run_id: str, body: dict, min_similarity: float, api_key: str, out_dir: Path) -> dict:
    print(f"[{TOOL}/{run_id}] min_similarity={min_similarity}: requesting {body.get('num_molecules')} molecules...")
    started_at = datetime.now(timezone.utc)
    status, raw_text, runtime_seconds = call_api(TOOL, api_key, body)
    finished_at = datetime.now(timezone.utc)

    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{TOOL}_{run_id}.json"
    raw_path.write_text(raw_text, encoding="utf-8")

    returned_records = None
    parse_note = ""
    if status == 200:
        try:
            import json

            raw_json = json.loads(raw_text)
            molecules = _PARSERS[TOOL](raw_json, manifest_path=raw_path)
            returned_records = len(molecules)
        except (ValueError, ManifestError, KeyError) as exc:
            parse_note = f"WARNING: raw response saved but did not parse cleanly: {exc}"
            print(f"  [{TOOL}/{run_id}] {parse_note}", file=sys.stderr)
    else:
        parse_note = f"HTTP {status} -- see raw response for error detail"
        print(f"  [{TOOL}/{run_id}] {parse_note}", file=sys.stderr)

    manifest = {
        "benchmark": "DecisionBench-DD v1.0",
        "tool": TOOL,
        "run_id": run_id,
        "request_config_file": f"molmim_primary.json (min_similarity overridden to {min_similarity}; sensitivity rerun, not frozen protocol)",
        "request_started_at_iso8601": started_at.isoformat(),
        "request_finished_at_iso8601": finished_at.isoformat(),
        "endpoint": ENDPOINTS[TOOL],
        "service_or_model_version": "hosted_api",
        "container_image_or_api_build": "hosted_api",
        "hardware": {"gpu_model": "hosted_api", "gpu_count": None, "peak_vram_gb": None},
        "runtime_seconds": round(runtime_seconds, 3),
        "http_status": status,
        "requested_molecules": body.get("num_molecules"),
        "returned_records": returned_records,
        "raw_response_file": f"raw/{raw_path.name}",
        "min_similarity": min_similarity,
        "notes": parse_note,
    }
    manifest_path = out_dir / f"{TOOL}_{run_id}.manifest.json"
    import json as _json

    manifest_path.write_text(_json.dumps(manifest, indent=2), encoding="utf-8")

    status_word = "OK" if status == 200 else "FAILED"
    print(f"  [{TOOL}/{run_id}] {status_word} (HTTP {status}, {runtime_seconds:.1f}s, {returned_records} molecules returned)")
    return manifest


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--min-similarity", type=float, required=True)
    p.add_argument("--replicates", type=int, default=3)
    p.add_argument("--out-dir", type=Path, required=True)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    api_key = load_api_key()
    body = load_request_body(TOOL)
    body["min_similarity"] = args.min_similarity

    args.out_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for i in range(1, args.replicates + 1):
        run_id = f"replicate_{i:02d}"
        manifest = run_replicate_sensitivity(run_id, dict(body), args.min_similarity, api_key, args.out_dir)
        if manifest["http_status"] != 200:
            failures += 1
        time.sleep(DELAY_BETWEEN_CALLS_SECONDS)

    print(f"\nDone: {args.replicates} requests, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

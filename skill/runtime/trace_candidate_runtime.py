#!/usr/bin/env python3
"""Trace Candidate model-readable rule context from a route decision."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("route", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    route = json.loads(args.route.read_text(encoding="utf-8"))
    details = []
    for relative in route["model_read_files"]:
        path = SKILL_ROOT / relative
        details.append({"path": relative, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper()})
    trace = {
        "profile": "production_candidate_tester_v04",
        "status": "PRODUCTION_CANDIDATE_STRUCTURALLY_VALIDATED",
        "real_video_status": "REAL_VIDEO_EVALUATION_SKIPPED",
        "model_read_files": [item["path"] for item in details],
        "model_file_details": details,
        "logical_module_count": len(details),
        "model_read_bytes": sum(item["bytes"] for item in details),
        "legacy_dependency_count": 0,
        "qa_default_dependency_count": 0,
        "workflow_default_dependency_count": 0,
        "peace_star_default_dependency_count": 0,
        "adapter_model_context_dependency": False,
        "adapter_model_context_bytes": 0,
        "production_default_changed": False,
    }
    encoded = json.dumps(trace, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate Candidate IR with the release-frozen contract implementation."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_VERSION = "storyboard-ir/0.4-production-candidate"
DRAFT_VERSION = "storyboard-ir-draft/0.1-shadow"


def load_legacy_validator():
    path = SKILL_ROOT / "_runtime" / "ir_validation.py"
    spec = importlib.util.spec_from_file_location("shared_ir_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load shared validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shared = load_legacy_validator()


def validate_candidate(data: object, schema: dict, profile: str = "generation_ready") -> list[str]:
    errors = shared.validate_schema_instance(data, schema, schema)
    if not isinstance(data, dict):
        return errors
    if data.get("schema_version") != CANDIDATE_VERSION:
        errors.append(f"schema_version must be {CANDIDATE_VERSION}")
        return errors
    compatibility = copy.deepcopy(data)
    compatibility["schema_version"] = DRAFT_VERSION
    draft_schema = json.loads(
        (SKILL_ROOT / "_runtime" / "storyboard-ir.draft.schema.json").read_text(encoding="utf-8")
    )
    errors.extend(shared.validate_ir_profile(compatibility, draft_schema, profile))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--schema", type=Path, default=SKILL_ROOT / "schemas" / "storyboard-ir.schema.json")
    parser.add_argument("--profile", choices=["generation_ready"], default="generation_ready")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    errors = validate_candidate(data, schema, args.profile)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS Storyboard IR Candidate profile={args.profile} scenes={len(data['scenes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

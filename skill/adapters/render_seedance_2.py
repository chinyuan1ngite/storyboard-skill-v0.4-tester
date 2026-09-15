#!/usr/bin/env python3
"""Deterministic Seedance 2.0 Production Candidate release renderer.

Prompt-expression logic is frozen inside this release package. Candidate
protocol metadata is validated separately
and translated in memory only for that implementation; Director semantics and
final prompts are unchanged.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_VERSION = "storyboard-ir/0.4-production-candidate"
DRAFT_VERSION = "storyboard-ir-draft/0.1-shadow"
ADAPTER_VERSION = "seedance-2-production-candidate/0.4"
ADAPTER_STATUS = "STRUCTURALLY_VALIDATED_REAL_VIDEO_UNVALIDATED"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


implementation = load_module(
    "release_seedance_renderer",
    SKILL_ROOT / "_runtime" / "seedance_renderer.py",
)
candidate_validator = load_module(
    "candidate_ir_validator",
    SKILL_ROOT / "scripts" / "validate_storyboard_ir.py",
)


def render_document(
    ir: dict[str, Any],
    source_path: Path,
    options: dict[str, Any] | None = None,
    options_sha256: str | None = None,
) -> dict[str, Any]:
    schema = json.loads((SKILL_ROOT / "schemas" / "storyboard-ir.schema.json").read_text(encoding="utf-8"))
    errors = candidate_validator.validate_candidate(ir, schema, "generation_ready")
    if errors:
        raise implementation.AdapterError("GENERATION_READY failed: " + " | ".join(errors))
    compatibility = copy.deepcopy(ir)
    compatibility["schema_version"] = DRAFT_VERSION
    sidecar = implementation.render_document(compatibility, source_path, options, options_sha256)
    sidecar["sidecar_version"] = "seedance-2-production-candidate-sidecar/0.4"
    sidecar["adapter_version"] = ADAPTER_VERSION
    sidecar["adapter_status"] = ADAPTER_STATUS
    sidecar["real_video_status"] = "REAL_VIDEO_EVALUATION_SKIPPED"
    sidecar["source_ir"]["schema_version"] = CANDIDATE_VERSION
    sidecar["generation_segment_policy"] = {
        "semantic_separation": "NARRATIVE_SCENE_NE_SHOT_NE_GENERATION_SEGMENT",
        "current_strategy": "ONE_SHOT_FALLBACK",
        "multi_shot_strategy": "OPEN_BLOCKED_BY_REAL_VIDEO",
    }
    for scene in sidecar["scenes"]:
        for segment in scene["segments"]:
            segment["segment_strategy"] = "ONE_SHOT_FALLBACK"
            segment["source_shot_ids"] = [segment["source_shot_id"]]
    return sidecar


def render_markdown(case_id: str, sidecar: dict[str, Any]) -> str:
    rendered = implementation.render_markdown(case_id, sidecar)
    rendered = rendered.replace(f"# {case_id} Seedance 2.0 Shadow Prompts", f"# {case_id} Seedance 2.0 Production Candidate Prompts", 1)
    rendered = rendered.replace("Status: `SHADOW_ADAPTER_DRAFT`", "Status: `STRUCTURALLY_VALIDATED` / `REAL_VIDEO_UNVALIDATED`", 1)
    return rendered


def render_case(source_path: Path, output_dir: Path, options: dict[str, Any] | None, options_sha256: str | None) -> dict[str, Any]:
    case_id = source_path.name.split(".", 1)[0]
    ir = json.loads(source_path.read_text(encoding="utf-8"))
    sidecar = render_document(ir, source_path, options, options_sha256)
    markdown = render_markdown(case_id, sidecar)
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = output_dir / f"{case_id}.seedance.prompts.md"
    sidecar_path = output_dir / f"{case_id}.seedance.sidecar.json"
    prompt_path.write_text(markdown, encoding="utf-8", newline="\n")
    sidecar_path.write_text(implementation.stable_json(sidecar), encoding="utf-8", newline="\n")
    segments = implementation.all_segments(sidecar)
    degradations = [item for segment in segments for item in segment["adapter_degradation"]["items"]]
    return {
        "case_id": case_id,
        "status": "PASS" if not degradations else "PASS_WITH_DEGRADATION",
        "source_ir": implementation.relative_path(source_path),
        "source_ir_sha256": sidecar["source_ir"]["sha256"],
        "prompt_output": implementation.relative_path(prompt_path),
        "prompt_output_sha256": implementation.sha256_bytes(prompt_path.read_bytes()),
        "sidecar": implementation.relative_path(sidecar_path),
        "sidecar_sha256": implementation.sha256_bytes(sidecar_path.read_bytes()),
        "prompt_count": len(segments),
        "prompt_bytes": sum(len(segment["final_seedance_prompt"].encode("utf-8")) for segment in segments),
        "degradation_count": len(degradations),
        "degradation_types": dict(Counter(item["type"] for item in degradations)),
        "legacy_field_dependency_count": 0,
        "adapter_model_context_dependency": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--options", type=Path)
    args = parser.parse_args()
    options, options_sha256 = implementation.load_options(args.options)
    sources = sorted(args.input_dir.glob("G*.candidate.ir.json"))
    if not sources:
        raise implementation.AdapterError("No Candidate IR inputs found")
    cases = [render_case(source, args.output_dir, options, options_sha256) for source in sources]
    manifest = {
        "manifest_version": "phase9-seedance-candidate-v1",
        "profile": "production_candidate_v04",
        "adapter_status": ADAPTER_STATUS,
        "real_video_status": "REAL_VIDEO_EVALUATION_SKIPPED",
        "case_count": len(cases),
        "prompt_count": sum(item["prompt_count"] for item in cases),
        "prompt_bytes": sum(item["prompt_bytes"] for item in cases),
        "degradation_count": sum(item["degradation_count"] for item in cases),
        "legacy_field_dependency_count": 0,
        "adapter_model_context_dependency": False,
        "production_default_changed": False,
        "segment_strategy": "ONE_SHOT_FALLBACK_CURRENT_IMPLEMENTATION",
        "cases": cases,
    }
    (args.output_dir / "adapter_manifest.json").write_text(implementation.stable_json(manifest), encoding="utf-8", newline="\n")
    print(f"PASS Candidate Adapter cases={len(cases)} prompts={manifest['prompt_count']} prompt_bytes={manifest['prompt_bytes']} degradations={manifest['degradation_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

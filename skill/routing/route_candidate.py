#!/usr/bin/env python3
"""Production-candidate route proposal using the release-frozen selector.

The selector reads script text only. This wrapper remaps the established Phase
7.5 routing decision to Candidate authorities without importing fixtures,
expected IR, QA, Workflow, Adapter, or Legacy content.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SHADOW_PATH = SKILL_ROOT / "_runtime" / "routing_selector.py"

spec = importlib.util.spec_from_file_location("release_routing_selector", SHADOW_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load routing implementation: {SHADOW_PATH}")
shadow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shadow)

BASE_FILES = [
    "SKILL.md",
    "core/storyboard-core.md",
    "core/generation-contract.md",
    "core/storyboard-ir.md",
]
CAPABILITY_PATHS = {
    "dialogue": "capabilities/dialogue.md",
    "group-dialogue": "capabilities/group-dialogue.md",
    "action-movement": "capabilities/action-movement.md",
    "emotion-performance": "capabilities/emotion-performance.md",
    "suspense-reveal": "capabilities/suspense-reveal.md",
    "establishing-transition": "capabilities/establishing-transition.md",
    "spatial-continuity": "capabilities/spatial-continuity.md",
    "audio-transition": "capabilities/audio-transition.md",
    "cinematic-high-risk": "capabilities/cinematic-high-risk.md",
}


def route_script(script: str) -> dict:
    proposed = shadow.route_script(script)
    selected = [proposed["dominant"]]
    if proposed.get("secondary"):
        selected.append(proposed["secondary"])
    selected.extend(proposed.get("modifiers", []))
    if len(selected) > 4:
        status = "ROUTE_ESCALATION_REQUIRED"
    else:
        status = "ROUTE_SELECTED"
    return {
        "schema_version": "phase9-production-candidate-route-v1",
        "status": status,
        "script_sha256": proposed["script_sha256"],
        "dominant": proposed["dominant"],
        "secondary": proposed.get("secondary"),
        "modifiers": proposed.get("modifiers", []),
        "route_confidence": proposed["route_confidence"],
        "uncertainty": proposed["uncertainty"],
        "cue_evidence": proposed["cue_evidence"],
        "model_read_files": BASE_FILES + [CAPABILITY_PATHS[item] for item in selected],
        "adapter_model_context_dependency": False,
        "production_default_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = route_script(args.script.read_text(encoding="utf-8"))
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

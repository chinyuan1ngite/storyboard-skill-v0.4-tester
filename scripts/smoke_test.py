#!/usr/bin/env python3
"""Run a minimal local toolchain smoke test; no LLM or video service is called."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PACKAGE_ROOT / "skill"


def stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def run(command: list[str], cwd: Path) -> str:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            + completed.stdout
            + completed.stderr
        )
    return completed.stdout


def minimal_ir() -> dict:
    return {
        "schema_version": "storyboard-ir/0.4-production-candidate",
        "document_id": "tester-smoke",
        "scenes": [
            {
                "scene_id": "SMOKE-SC01",
                "source_ref": {
                    "kind": "smoke_anchor",
                    "start": "门口",
                    "end": "刚到",
                },
                "required_beats": [
                    {
                        "beat_id": "B01",
                        "description": "林然进门，周宁询问她是否回来。",
                        "source_ref": "SMOKE:L1",
                    },
                    {
                        "beat_id": "B02",
                        "description": "林然回答刚到。",
                        "source_ref": "SMOKE:L2",
                    },
                ],
                "scene_objective": "清楚呈现两人的简短问答。",
                "subject_registry": [
                    {"subject_id": "LIN", "display_name": "林然"},
                    {"subject_id": "ZHOU", "display_name": "周宁"},
                ],
                "spatial_anchor": {"summary": "林然在门口，周宁在室内。"},
                "shots": [
                    {
                        "shot_id": "SMOKE-SH01",
                        "order": 1,
                        "source_beats": ["B01", "B02"],
                        "narrative_purpose": "呈现进门后的问答和人物关系。",
                        "duration": {
                            "start_seconds": 0,
                            "end_seconds": 5,
                            "duration_seconds": 5,
                        },
                        "subjects": ["LIN", "ZHOU"],
                        "framing": {"scale": "medium_two_shot"},
                        "camera": {
                            "viewpoint": "room_side_same_axis",
                            "angle": "eye_level",
                            "movement": "static",
                        },
                        "blocking_action": {
                            "summary": "林然停在门口看向周宁；周宁询问，林然回答。"
                        },
                        "spatial_relation": {
                            "summary": "两人保持门口与室内的既定相对位置。"
                        },
                    }
                ],
                "audio_plan": [
                    {
                        "event_id": "AUD01",
                        "kind": "dialogue",
                        "shot_refs": ["SMOKE-SH01"],
                        "description": "周宁询问林然。",
                        "speaker_ref": "ZHOU",
                        "text": "你回来了？",
                        "visibility": "on_screen",
                    },
                    {
                        "event_id": "AUD02",
                        "kind": "dialogue",
                        "shot_refs": ["SMOKE-SH01"],
                        "description": "林然回答周宁。",
                        "speaker_ref": "LIN",
                        "text": "刚到。",
                        "visibility": "on_screen",
                    },
                ],
            }
        ],
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="storyboard_tester_smoke_") as raw:
        work = Path(raw)
        script_path = work / "dialogue.txt"
        route_path = work / "route.json"
        ir_dir = work / "ir"
        output_dir = work / "prompt"
        trace_path = work / "runtime.json"
        ir_dir.mkdir()
        script_path.write_text(
            "门口，周宁：“你回来了？”林然：“刚到。”",
            encoding="utf-8",
        )
        ir_path = ir_dir / "GSMOKE.candidate.ir.json"
        ir_path.write_text(stable_json(minimal_ir()), encoding="utf-8")

        run(
            [
                sys.executable,
                str(SKILL_ROOT / "routing" / "route_candidate.py"),
                str(script_path),
                "--output",
                str(route_path),
            ],
            work,
        )
        route = json.loads(route_path.read_text(encoding="utf-8"))
        if route["dominant"] != "dialogue":
            raise RuntimeError(f"unexpected smoke route: {route['dominant']}")

        run(
            [
                sys.executable,
                str(SKILL_ROOT / "scripts" / "validate_storyboard_ir.py"),
                str(ir_path),
            ],
            work,
        )
        run(
            [
                sys.executable,
                str(SKILL_ROOT / "adapters" / "render_seedance_2.py"),
                "--input-dir",
                str(ir_dir),
                "--output-dir",
                str(output_dir),
            ],
            work,
        )
        run(
            [
                sys.executable,
                str(SKILL_ROOT / "runtime" / "trace_candidate_runtime.py"),
                str(route_path),
                "--output",
                str(trace_path),
            ],
            work,
        )

        sidecar = json.loads(
            (output_dir / "GSMOKE.seedance.sidecar.json").read_text(encoding="utf-8")
        )
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        prompt_count = sum(len(scene["segments"]) for scene in sidecar["scenes"])
        if prompt_count != 1:
            raise RuntimeError(f"expected one smoke prompt, got {prompt_count}")
        if trace["model_read_bytes"] != 14375:
            raise RuntimeError(
                f"dialogue rule context changed: {trace['model_read_bytes']}"
            )
        if trace["adapter_model_context_bytes"] != 0:
            raise RuntimeError("Adapter entered model context")

    print("A. Toolchain smoke test: PASS")
    print("   Router -> valid Candidate IR -> Validator -> Adapter -> Runtime trace")
    print("   dialogue rule context: 14375 bytes")
    print("B. LLM Skill test: NOT_RUN")
    print("   Follow QUICKSTART.md with a Skill-capable Agent; this script does not fake a Director.")
    print("C. Real video test: NOT_RUN")
    print("   Seedance service and credentials are external to this package.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

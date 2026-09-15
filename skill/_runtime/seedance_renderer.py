"""Deterministic Storyboard IR Draft -> Seedance 2.0 Shadow prompt renderer.

This Adapter expresses resolved director facts. It never chooses or revises them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
IR_VALIDATOR_DIR = Path(__file__).resolve().parent
if str(IR_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(IR_VALIDATOR_DIR))

from ir_validation import validate_ir_profile  # noqa: E402


ADAPTER_VERSION = "seedance-2-shadow-adapter/0.1"
SIDECAR_VERSION = "seedance-2-shadow-sidecar/0.1"
MANIFEST_VERSION = "phase8-seedance-shadow-results/0.1"
MODEL_ID = "Seedance 2.0"
TARGET_SEGMENT_SECONDS = 15.0
FIXED_FIDELITY_INSTRUCTION = (
    "只执行本镜头，不新增未声明的角色、事件、对白、动作结果或连续状态变化。"
)
DEGRADATION_TYPES = {
    "FORMAT_LIMITATION",
    "DURATION_LIMITATION",
    "REFERENCE_LIMITATION",
    "AUDIO_LIMITATION",
    "MOTION_LIMITATION",
    "SPATIAL_COMPLEXITY_LIMITATION",
    "UNSUPPORTED_IR_FACT",
}


class AdapterError(ValueError):
    """Raised when input is not safe for deterministic Adapter expression."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def format_number(value: float | int) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.3f}".rstrip("0").rstrip(".")


def sentence_clause(label: str, value: str) -> str:
    suffix = "" if value.endswith(("。", "！", "？", ".", "!", "?")) else "。"
    return f"{label}：{value}{suffix}"


def list_clause(label: str, values: list[str]) -> str:
    if len(values) == 1:
        return sentence_clause(label, values[0])
    return label + "：\n" + "\n".join(f"- {value}" for value in values)


def load_options(path: Path | None) -> tuple[dict[str, Any], str | None]:
    if path is None:
        return {}, None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AdapterError("Adapter options must be an object")
    allowed = {
        "profile_version",
        "render_style",
        "aspect_ratio",
        "reference_assets",
        "model_negative_constraints",
    }
    extra = set(data) - allowed
    if extra:
        raise AdapterError(f"Unsupported Adapter option keys: {sorted(extra)}")
    style = data.get("render_style")
    if style is not None:
        if not isinstance(style, dict):
            raise AdapterError("render_style must be an object")
        if style.get("classification") != "RENDER_ONLY":
            raise AdapterError("render_style must be classified RENDER_ONLY")
        if style.get("source") not in {"user_explicit", "platform_config"}:
            raise AdapterError("render_style source must be explicit")
        if not isinstance(style.get("text"), str) or not style["text"].strip():
            raise AdapterError("render_style.text must be non-empty")
    ratio = data.get("aspect_ratio")
    if ratio is not None and (not isinstance(ratio, str) or not ratio.strip()):
        raise AdapterError("aspect_ratio must be a non-empty string")
    negatives = data.get("model_negative_constraints", [])
    if not isinstance(negatives, list) or not all(
        isinstance(item, str) and item.strip() for item in negatives
    ):
        raise AdapterError("model_negative_constraints must contain non-empty strings")
    references = data.get("reference_assets", [])
    if not isinstance(references, list):
        raise AdapterError("reference_assets must be an array")
    for index, item in enumerate(references):
        if not isinstance(item, dict):
            raise AdapterError(f"reference_assets[{index}] must be an object")
        required = {"handle", "kind", "purpose", "source"}
        if not required.issubset(item):
            raise AdapterError(f"reference_assets[{index}] lacks required fields")
        if item["kind"] not in {"image", "video", "audio"}:
            raise AdapterError(f"reference_assets[{index}].kind is invalid")
        if item["source"] not in {"user_explicit", "platform_config"}:
            raise AdapterError(f"reference_assets[{index}].source must be explicit")
        if not all(
            isinstance(item[key], str) and item[key].strip()
            for key in ("handle", "purpose")
        ):
            raise AdapterError(f"reference_assets[{index}] contains an empty value")
    return data, sha256_bytes(path.read_bytes())


def subject_maps(scene: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    names: dict[str, str] = {}
    states: dict[str, str] = {}
    for subject in scene.get("subject_registry", []):
        names[subject["subject_id"]] = subject["display_name"]
        if "initial_state" in subject:
            states[subject["subject_id"]] = subject["initial_state"]
    return names, states


def collect_audio_events(
    scene: dict[str, Any],
    scene_index: int,
) -> tuple[dict[str, list[tuple[dict[str, Any], str]]], list[dict[str, Any]]]:
    shot_ids = [shot["shot_id"] for shot in scene["shots"]]
    by_shot: dict[str, list[tuple[dict[str, Any], str]]] = {
        shot_id: [] for shot_id in shot_ids
    }
    unattached: list[dict[str, Any]] = []
    origins: list[tuple[dict[str, Any], str]] = []
    for event_index, event in enumerate(scene.get("audio_plan", [])):
        origins.append((event, f"$.scenes[{scene_index}].audio_plan[{event_index}]"))
    for shot_index, shot in enumerate(scene["shots"]):
        for event_index, event in enumerate(shot.get("dialogue_audio", [])):
            origins.append(
                (
                    event,
                    f"$.scenes[{scene_index}].shots[{shot_index}].dialogue_audio[{event_index}]",
                )
            )
    for event, path in origins:
        refs = event.get("shot_refs", [])
        if not refs:
            unattached.append({"event": event, "path": path})
            continue
        for shot_id in refs:
            if shot_id not in by_shot:
                raise AdapterError(f"Audio event references unknown Shot {shot_id}")
            by_shot[shot_id].append((event, path))
    return by_shot, unattached


def add_fact(
    facts: list[dict[str, Any]],
    path: str,
    role: str,
    value: Any,
    rendered: str | None = None,
    authority: str = "IR",
) -> None:
    facts.append(
        {
            "path": path,
            "role": role,
            "value": value,
            "rendered": rendered if rendered is not None else str(value),
            "authority": authority,
        }
    )


def append_constraint_clauses(
    clauses: list[str],
    facts: list[dict[str, Any]],
    constraints: dict[str, Any] | None,
    base_path: str,
) -> None:
    if not constraints:
        return
    preserved = constraints.get("must_preserve", [])
    prohibited = constraints.get("prohibited", [])
    if preserved:
        clauses.append(list_clause("必须保持", preserved))
        for index, item in enumerate(preserved):
            add_fact(
                facts,
                f"{base_path}.must_preserve[{index}]",
                "story_director_constraint",
                item,
            )
    if prohibited:
        clauses.append(list_clause("禁止", prohibited))
        for index, item in enumerate(prohibited):
            add_fact(
                facts,
                f"{base_path}.prohibited[{index}]",
                "story_director_constraint",
                item,
            )


def render_audio_event(
    event: dict[str, Any],
    event_path: str,
    names: dict[str, str],
    facts: list[dict[str, Any]],
) -> str:
    kind = event["kind"]
    add_fact(facts, f"{event_path}.kind", "audio_kind", kind)
    pieces: list[str] = []
    if kind == "dialogue":
        speaker_ref = event["speaker_ref"]
        speaker = names[speaker_ref]
        text = event["text"]
        pieces.append(f"{speaker}说：“{text}”")
        add_fact(facts, f"{event_path}.speaker_ref", "dialogue_speaker", speaker_ref, speaker)
        add_fact(facts, f"{event_path}.text", "dialogue_text", text)
    else:
        pieces.append(event["description"])
    if event.get("delivery"):
        pieces.append("表达：" + event["delivery"])
        add_fact(facts, f"{event_path}.delivery", "audio_delivery", event["delivery"])
    if event.get("visibility"):
        pieces.append("声画关系：" + event["visibility"])
        add_fact(facts, f"{event_path}.visibility", "audio_visibility", event["visibility"])
    description = event["description"]
    if kind == "dialogue":
        pieces.append("说明：" + description)
    add_fact(facts, f"{event_path}.description", "audio_description", description)
    return "；".join(pieces)


def reference_limit_degradations(
    references: list[dict[str, Any]],
    shot_id: str,
) -> list[dict[str, Any]]:
    counts = Counter(item["kind"] for item in references)
    limits = {"image": 9, "video": 3, "audio": 3}
    items: list[dict[str, Any]] = []
    for kind, limit in limits.items():
        if counts[kind] > limit:
            items.append(
                {
                    "type": "REFERENCE_LIMITATION",
                    "affected_shot": shot_id,
                    "affected_ir_fact": "adapter_options.reference_assets",
                    "model_limitation": f"{kind} references {counts[kind]} exceed evidenced limit {limit}",
                    "possible_impact": "Some explicit references may not be accepted together.",
                    "manual_review_required": True,
                }
            )
    return items


def render_shot(
    scene: dict[str, Any],
    scene_index: int,
    shot: dict[str, Any],
    shot_index: int,
    audio_by_shot: dict[str, list[tuple[dict[str, Any], str]]],
    options: dict[str, Any],
) -> dict[str, Any]:
    names, subject_states = subject_maps(scene)
    shot_path = f"$.scenes[{scene_index}].shots[{shot_index}]"
    facts: list[dict[str, Any]] = []
    clauses: list[str] = []

    duration = shot["duration"]["duration_seconds"]
    duration_text = format_number(duration)
    clauses.append(f"时长：{duration_text} 秒。")
    add_fact(
        facts,
        f"{shot_path}.duration.duration_seconds",
        "duration",
        duration,
        duration_text,
    )

    clauses.append(sentence_clause("镜头任务", shot["narrative_purpose"]))
    add_fact(
        facts,
        f"{shot_path}.narrative_purpose",
        "narrative_purpose",
        shot["narrative_purpose"],
    )

    beats = {beat["beat_id"]: (index, beat) for index, beat in enumerate(scene["required_beats"])}
    beat_descriptions: list[str] = []
    for beat_id in shot["source_beats"]:
        beat_index, beat = beats[beat_id]
        beat_descriptions.append(beat["description"])
        add_fact(
            facts,
            f"$.scenes[{scene_index}].required_beats[{beat_index}].description",
            "required_beat",
            beat["description"],
        )
    clauses.append(list_clause("剧情事实", beat_descriptions))

    if shot["subjects"]:
        subject_names = [names[subject_id] for subject_id in shot["subjects"]]
        clauses.append("主体：" + "、".join(subject_names) + "。")
        registry_index = {
            item["subject_id"]: index
            for index, item in enumerate(scene.get("subject_registry", []))
        }
        for subject_id, display_name in zip(shot["subjects"], subject_names):
            index = registry_index[subject_id]
            add_fact(
                facts,
                f"$.scenes[{scene_index}].subject_registry[{index}].display_name",
                "subject_identity",
                display_name,
            )
            if subject_id in subject_states:
                add_fact(
                    facts,
                    f"$.scenes[{scene_index}].subject_registry[{index}].initial_state",
                    "subject_initial_state",
                    subject_states[subject_id],
                )
        state_phrases = [
            f"{names[subject_id]}：{subject_states[subject_id]}"
            for subject_id in shot["subjects"]
            if subject_id in subject_states
        ]
        if state_phrases:
            clauses.append("主体既定状态：" + "；".join(state_phrases) + "。")

    framing = shot["framing"]
    framing_parts = [framing["scale"]]
    add_fact(facts, f"{shot_path}.framing.scale", "framing", framing["scale"])
    if framing.get("description"):
        framing_parts.append(framing["description"])
        add_fact(
            facts,
            f"{shot_path}.framing.description",
            "framing",
            framing["description"],
        )
    clauses.append("景别：" + "；".join(framing_parts) + "。")

    camera = shot["camera"]
    camera_parts = [
        "机位 " + camera["viewpoint"],
        "角度 " + camera["angle"],
        "运镜 " + camera["movement"],
    ]
    for key in ("viewpoint", "angle", "movement"):
        add_fact(facts, f"{shot_path}.camera.{key}", "camera", camera[key])
    if camera.get("expanded"):
        expanded = camera["expanded"]
        camera_parts.append("风险依据 " + expanded["risk_reason"])
        add_fact(
            facts,
            f"{shot_path}.camera.expanded.risk_reason",
            "camera_high_risk",
            expanded["risk_reason"],
        )
        for index, item in enumerate(expanded["facts"]):
            camera_parts.append(item)
            add_fact(
                facts,
                f"{shot_path}.camera.expanded.facts[{index}]",
                "camera_high_risk",
                item,
            )
    clauses.append("摄影机：" + "；".join(camera_parts) + "。")

    action = shot["blocking_action"]["summary"]
    clauses.append(sentence_clause("动作与时序", action))
    add_fact(facts, f"{shot_path}.blocking_action.summary", "blocking_action", action)

    if shot_index == 0 and scene.get("initial_state"):
        initial = scene["initial_state"]["summary"]
        clauses.append(sentence_clause("起始连续状态", initial))
        add_fact(
            facts,
            f"$.scenes[{scene_index}].initial_state.summary",
            "continuity_initial",
            initial,
        )
    if scene.get("spatial_anchor"):
        anchor = scene["spatial_anchor"]["summary"]
        clauses.append(sentence_clause("场景空间锚点", anchor))
        add_fact(
            facts,
            f"$.scenes[{scene_index}].spatial_anchor.summary",
            "spatial_anchor",
            anchor,
        )
    if shot.get("spatial_relation"):
        relation = shot["spatial_relation"]["summary"]
        clauses.append(sentence_clause("本镜空间关系", relation))
        add_fact(
            facts,
            f"{shot_path}.spatial_relation.summary",
            "spatial_relation",
            relation,
        )
    if shot.get("composition"):
        composition = shot["composition"]["summary"]
        clauses.append(sentence_clause("构图", composition))
        add_fact(
            facts,
            f"{shot_path}.composition.summary",
            "composition",
            composition,
        )
    if shot.get("visual_emphasis"):
        emphasis = shot["visual_emphasis"]
        clauses.append(sentence_clause("视觉重点", emphasis))
        add_fact(facts, f"{shot_path}.visual_emphasis", "visual_emphasis", emphasis)

    events = audio_by_shot[shot["shot_id"]]
    if events:
        rendered_events = [
            render_audio_event(event, event_path, names, facts)
            for event, event_path in events
        ]
        clauses.append(list_clause("对白与声音", rendered_events))

    if shot.get("continuity_delta"):
        delta = shot["continuity_delta"]["summary"]
        clauses.append(sentence_clause("本镜连续状态变化", delta))
        add_fact(
            facts,
            f"{shot_path}.continuity_delta.summary",
            "continuity_delta",
            delta,
        )
    if shot_index == len(scene["shots"]) - 1 and scene.get("continuity_end_state"):
        end_state = scene["continuity_end_state"]["summary"]
        clauses.append(sentence_clause("镜末必须达到", end_state))
        add_fact(
            facts,
            f"$.scenes[{scene_index}].continuity_end_state.summary",
            "continuity_end",
            end_state,
        )

    append_constraint_clauses(
        clauses,
        facts,
        scene.get("generation_constraints"),
        f"$.scenes[{scene_index}].generation_constraints",
    )
    append_constraint_clauses(
        clauses,
        facts,
        shot.get("generation_constraints"),
        f"{shot_path}.generation_constraints",
    )

    style = options.get("render_style")
    if style:
        clauses.append(sentence_clause("渲染风格", style["text"]))
        add_fact(
            facts,
            "$adapter_options.render_style.text",
            "render_style",
            style["text"],
            authority="ADAPTER_OPTION",
        )
    references = options.get("reference_assets", [])
    if references:
        rendered_refs = []
        for index, item in enumerate(references):
            rendered_refs.append(f"{item['handle']}（{item['purpose']}）")
            add_fact(
                facts,
                f"$adapter_options.reference_assets[{index}].handle",
                "reference",
                item["handle"],
                authority="ADAPTER_OPTION",
            )
            add_fact(
                facts,
                f"$adapter_options.reference_assets[{index}].purpose",
                "reference",
                item["purpose"],
                authority="ADAPTER_OPTION",
            )
        clauses.append(list_clause("参考素材", rendered_refs))
    negatives = options.get("model_negative_constraints", [])
    if negatives:
        clauses.append(list_clause("模型负向限制", negatives))
        for index, item in enumerate(negatives):
            add_fact(
                facts,
                f"$adapter_options.model_negative_constraints[{index}]",
                "model_constraint",
                item,
                authority="ADAPTER_OPTION",
            )

    clauses.append(FIXED_FIDELITY_INSTRUCTION)
    prompt = "\n".join(clauses)

    degradations = reference_limit_degradations(references, shot["shot_id"])
    if float(duration) > TARGET_SEGMENT_SECONDS:
        degradations.append(
            {
                "type": "DURATION_LIMITATION",
                "affected_shot": shot["shot_id"],
                "affected_ir_fact": f"{shot_path}.duration.duration_seconds",
                "model_limitation": (
                    f"Shot duration {format_number(duration)}s exceeds the "
                    f"{format_number(TARGET_SEGMENT_SECONDS)}s evidenced target window"
                ),
                "possible_impact": "A single generation may not carry the complete Shot.",
                "manual_review_required": True,
            }
        )
    for item in degradations:
        if item["type"] not in DEGRADATION_TYPES:
            raise AdapterError(f"Unknown degradation type {item['type']}")

    return {
        "segment_id": shot["shot_id"] + "-SEG01",
        "source_scene_id": scene["scene_id"],
        "source_shot_id": shot["shot_id"],
        "shot_order": shot["order"],
        "segment_index": 1,
        "segment_count": 1,
        "duration_seconds": duration,
        "final_seedance_prompt": prompt,
        "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
        "fact_provenance": facts,
        "consumed_ir_paths": sorted(
            {item["path"] for item in facts if item["authority"] == "IR"}
        ),
        "reference_requirements": references,
        "adapter_warnings": [],
        "adapter_degradation": {
            "status": "NONE" if not degradations else "DEGRADED",
            "items": degradations,
        },
    }


def render_document(
    ir: dict[str, Any],
    source_path: Path,
    options: dict[str, Any] | None = None,
    options_sha256: str | None = None,
) -> dict[str, Any]:
    options = options or {}
    schema = json.loads(
        (Path(__file__).resolve().parent / "storyboard-ir.draft.schema.json").read_text(
            encoding="utf-8"
        )
    )
    errors = validate_ir_profile(ir, schema, "generation_ready")
    if errors:
        raise AdapterError("GENERATION_READY failed: " + " | ".join(errors))
    if "legacy_extensions" in ir:
        raise AdapterError("legacy_extensions is forbidden in the Shadow Adapter")

    scenes_out: list[dict[str, Any]] = []
    unattached_all: list[dict[str, Any]] = []
    for scene_index, scene in enumerate(ir["scenes"]):
        audio_by_shot, unattached = collect_audio_events(scene, scene_index)
        unattached_all.extend(unattached)
        segments = [
            render_shot(
                scene,
                scene_index,
                shot,
                shot_index,
                audio_by_shot,
                options,
            )
            for shot_index, shot in enumerate(scene["shots"])
        ]
        scenes_out.append({"source_scene_id": scene["scene_id"], "segments": segments})
    if unattached_all:
        details = ", ".join(item["path"] for item in unattached_all)
        raise AdapterError(
            "Audio events without shot_refs cannot be placed without directing: " + details
        )

    source_bytes = source_path.read_bytes()
    return {
        "sidecar_version": SIDECAR_VERSION,
        "adapter_version": ADAPTER_VERSION,
        "adapter_status": "SHADOW_ADAPTER_DRAFT",
        "model_id": MODEL_ID,
        "source_ir": {
            "path": relative_path(source_path),
            "sha256": sha256_bytes(source_bytes),
            "schema_version": ir["schema_version"],
            "document_id": ir["document_id"],
        },
        "adapter_options": {
            "present": bool(options),
            "sha256": options_sha256,
            "aspect_ratio": options.get("aspect_ratio"),
        },
        "target_segment_seconds": TARGET_SEGMENT_SECONDS,
        "fixed_policy": {
            "instruction": FIXED_FIDELITY_INSTRUCTION,
            "story_fact_authority": "IR_ONLY",
            "legacy_11_module_dependency": False,
        },
        "scenes": scenes_out,
    }


def all_segments(sidecar: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        segment
        for scene in sidecar["scenes"]
        for segment in scene["segments"]
    ]


def render_markdown(case_id: str, sidecar: dict[str, Any]) -> str:
    lines = [
        f"# {case_id} Seedance 2.0 Shadow Prompts",
        "",
        "Status: `SHADOW_ADAPTER_DRAFT`",
        "",
    ]
    for segment in all_segments(sidecar):
        lines.extend(
            [
                f"## Shot {segment['source_shot_id']}",
                "",
                f"Duration: {format_number(segment['duration_seconds'])} seconds",
                "",
                "Final Seedance Prompt:",
                "",
                "```text",
                segment["final_seedance_prompt"],
                "```",
                "",
            ]
        )
        if segment["reference_requirements"]:
            lines.extend(
                [
                    "Reference / Constraint:",
                    "",
                    "- " + "\n- ".join(
                        f"{item['handle']}: {item['purpose']}"
                        for item in segment["reference_requirements"]
                    ),
                    "",
                ]
            )
        if segment["adapter_warnings"]:
            lines.extend(
                [
                    "Adapter warning:",
                    "",
                    "- " + "\n- ".join(segment["adapter_warnings"]),
                    "",
                ]
            )
        degradation = segment["adapter_degradation"]
        if degradation["status"] != "NONE":
            lines.extend(
                [
                    "Adapter degradation:",
                    "",
                    "- " + "\n- ".join(
                        f"{item['type']}: {item['model_limitation']}"
                        for item in degradation["items"]
                    ),
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def render_case(
    source_path: Path,
    output_dir: Path,
    options: dict[str, Any] | None = None,
    options_sha256: str | None = None,
) -> dict[str, Any]:
    case_id = source_path.name.split(".", 1)[0]
    ir = json.loads(source_path.read_text(encoding="utf-8"))
    sidecar = render_document(ir, source_path, options, options_sha256)
    markdown = render_markdown(case_id, sidecar)
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = output_dir / f"{case_id}.seedance.prompts.md"
    sidecar_path = output_dir / f"{case_id}.seedance.sidecar.json"
    prompt_path.write_text(markdown, encoding="utf-8", newline="\n")
    sidecar_path.write_text(stable_json(sidecar), encoding="utf-8", newline="\n")

    segments = all_segments(sidecar)
    degradations = [
        item
        for segment in segments
        for item in segment["adapter_degradation"]["items"]
    ]
    prompt_bytes = sum(
        len(segment["final_seedance_prompt"].encode("utf-8"))
        for segment in segments
    )
    return {
        "case_id": case_id,
        "status": "PASS" if not degradations else "PASS_WITH_DEGRADATION",
        "source_ir": relative_path(source_path),
        "source_ir_sha256": sidecar["source_ir"]["sha256"],
        "prompt_output": relative_path(prompt_path),
        "prompt_output_bytes": len(prompt_path.read_bytes()),
        "prompt_output_sha256": sha256_bytes(prompt_path.read_bytes()),
        "sidecar": relative_path(sidecar_path),
        "sidecar_bytes": len(sidecar_path.read_bytes()),
        "sidecar_sha256": sha256_bytes(sidecar_path.read_bytes()),
        "prompt_count": len(segments),
        "prompt_bytes": prompt_bytes,
        "adapter_warning_count": sum(
            len(segment["adapter_warnings"]) for segment in segments
        ),
        "degradation_count": len(degradations),
        "degradation_types": dict(Counter(item["type"] for item in degradations)),
        "legacy_field_dependency_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--options", type=Path)
    args = parser.parse_args()

    options, options_sha256 = load_options(args.options)
    source_paths = sorted(args.input_dir.glob("G*.generated.ir.json"))
    if not source_paths:
        raise AdapterError("No generated IR inputs found")
    cases = [
        render_case(source_path, args.output_dir, options, options_sha256)
        for source_path in source_paths
    ]
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "profile": "shadow_v04_seedance",
        "adapter_status": "SHADOW_ADAPTER_DRAFT",
        "source_profile": "shadow_v04_director",
        "case_count": len(cases),
        "prompt_count": sum(item["prompt_count"] for item in cases),
        "prompt_bytes": sum(item["prompt_bytes"] for item in cases),
        "adapter_warning_count": sum(
            item["adapter_warning_count"] for item in cases
        ),
        "degradation_count": sum(item["degradation_count"] for item in cases),
        "missing_ir_fact_count": None,
        "added_unsupported_fact_count": None,
        "legacy_field_dependency_count": 0,
        "production_default_changed": False,
        "cases": cases,
    }
    manifest_path = args.output_dir / "adapter_manifest.json"
    manifest_path.write_text(stable_json(manifest), encoding="utf-8", newline="\n")
    print(
        "PASS Seedance Shadow Adapter "
        f"cases={manifest['case_count']} prompts={manifest['prompt_count']} "
        f"prompt_bytes={manifest['prompt_bytes']} "
        f"degradations={manifest['degradation_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

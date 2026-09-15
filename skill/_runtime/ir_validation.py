"""Deterministic structural/profile validator for the draft shadow IR."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


EXPECTED_VERSION = "storyboard-ir-draft/0.1-shadow"
PROFILE_ALIASES = {
    "legacy_import": "legacy_import",
    "shadow": "legacy_import",
    "generation_ready": "generation_ready",
}
UNRESOLVED_VALUES = {"unknown", "missing", "not_applicable"}
FORBIDDEN_CORE_KEYS = {
    "approval",
    "commit_hash",
    "release_seal",
    "qa_pass",
    "review_state",
    "segment_commit",
}


def validate_schema_instance(
    value: object,
    rule: dict,
    root_schema: dict,
    location: str = "$",
) -> list[str]:
    """Validate the JSON-Schema subset used by the Phase 6 draft.

    Keeping this local avoids adding a runtime dependency. It is deliberately
    structural: no storyboard-quality or directing judgment belongs here.
    """
    errors: list[str] = []
    if "$ref" in rule:
        prefix = "#/$defs/"
        reference = rule["$ref"]
        if not isinstance(reference, str) or not reference.startswith(prefix):
            return [f"schema: {location} contains unsupported reference {reference!r}"]
        name = reference[len(prefix):]
        target = root_schema.get("$defs", {}).get(name)
        if not isinstance(target, dict):
            return [f"schema: {location} references missing definition {name}"]
        return validate_schema_instance(value, target, root_schema, location)

    expected_type = rule.get("type")
    type_matches = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
    }
    if expected_type in type_matches and not type_matches[expected_type]:
        return [f"schema: {location} must be {expected_type}"]

    if "const" in rule and value != rule["const"]:
        errors.append(f"schema: {location} must equal {rule['const']!r}")
    if "enum" in rule and value not in rule["enum"]:
        errors.append(f"schema: {location} is not an allowed value")

    if isinstance(value, str):
        if "minLength" in rule and len(value) < rule["minLength"]:
            errors.append(f"schema: {location} is shorter than minLength")
        if "pattern" in rule and re.fullmatch(rule["pattern"], value) is None:
            errors.append(f"schema: {location} does not match required pattern")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in rule and value < rule["minimum"]:
            errors.append(f"schema: {location} is below minimum")
        if "exclusiveMinimum" in rule and value <= rule["exclusiveMinimum"]:
            errors.append(f"schema: {location} is not above exclusiveMinimum")

    if isinstance(value, list):
        if "minItems" in rule and len(value) < rule["minItems"]:
            errors.append(f"schema: {location} has fewer than minItems")
        item_rule = rule.get("items")
        if isinstance(item_rule, dict):
            for index, item in enumerate(value):
                errors.extend(validate_schema_instance(item, item_rule, root_schema, f"{location}[{index}]"))

    if isinstance(value, dict):
        required = rule.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"schema: {location}.{key} is required")
        if "minProperties" in rule and len(value) < rule["minProperties"]:
            errors.append(f"schema: {location} has fewer than minProperties")
        properties = rule.get("properties", {})
        if rule.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"schema: {location}.{key} is not an allowed property")
        for key, child_rule in properties.items():
            if key in value and isinstance(child_rule, dict):
                errors.extend(validate_schema_instance(value[key], child_rule, root_schema, f"{location}.{key}"))
    return errors


def is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_resolved_string(value: object) -> bool:
    return is_nonempty_string(value) and value.strip().lower() not in UNRESOLVED_VALUES


def add(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def string_list(errors: list[str], value: object, location: str, allow_empty: bool = True) -> list[str]:
    add(errors, isinstance(value, list), f"{location} must be an array")
    if not isinstance(value, list):
        return []
    if not allow_empty:
        add(errors, bool(value), f"{location} must not be empty")
    add(errors, all(is_nonempty_string(item) for item in value), f"{location} must contain non-empty strings")
    return [item for item in value if isinstance(item, str)]


def check_forbidden_keys(value: object, location: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_CORE_KEYS:
                errors.append(f"{location}.{key} is workflow/QA/project state, not Core IR")
            check_forbidden_keys(child, f"{location}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            check_forbidden_keys(child, f"{location}[{index}]", errors)


def validate_audio_event(
    event: object,
    location: str,
    shot_ids: set[str],
    subject_ids: set[str],
    event_ids: set[str],
    errors: list[str],
) -> None:
    add(errors, isinstance(event, dict), f"{location} must be an object")
    if not isinstance(event, dict):
        return
    event_id = event.get("event_id")
    add(errors, is_nonempty_string(event_id), f"{location}.event_id is required")
    if isinstance(event_id, str):
        add(errors, event_id not in event_ids, f"duplicate audio event id: {event_id}")
        event_ids.add(event_id)
    kind = event.get("kind")
    add(errors, kind in {"dialogue", "sound", "ambience", "music_constraint", "audio_constraint", "unknown"}, f"{location}.kind is invalid")
    refs = string_list(errors, event.get("shot_refs"), f"{location}.shot_refs")
    for ref in refs:
        add(errors, ref in shot_ids, f"{location}.shot_refs references unknown shot {ref}")
    add(errors, is_nonempty_string(event.get("description")), f"{location}.description is required")
    if kind == "dialogue":
        speaker = event.get("speaker_ref")
        add(errors, is_nonempty_string(speaker), f"{location}.speaker_ref is required for dialogue")
        if isinstance(speaker, str):
            add(errors, speaker in subject_ids, f"{location}.speaker_ref references unknown subject {speaker}")
        add(errors, isinstance(event.get("text"), str), f"{location}.text is required for dialogue")


def validate_constraints(value: object, location: str, errors: list[str]) -> None:
    add(errors, isinstance(value, dict), f"{location} must be an object")
    if not isinstance(value, dict):
        return
    add(errors, bool(value), f"{location} must not be empty")
    for key in ("must_preserve", "prohibited"):
        if key in value:
            string_list(errors, value[key], f"{location}.{key}", allow_empty=False)


def validate_ir(data: object, schema: dict | None = None) -> list[str]:
    errors: list[str] = []
    if schema is not None:
        errors.extend(validate_schema_instance(data, schema, schema))
    add(errors, isinstance(data, dict), "root must be an object")
    if not isinstance(data, dict):
        return errors
    add(errors, data.get("schema_version") == EXPECTED_VERSION, f"schema_version must be {EXPECTED_VERSION}")
    add(errors, is_nonempty_string(data.get("document_id")), "document_id is required")
    scenes = data.get("scenes")
    add(errors, isinstance(scenes, list) and bool(scenes), "scenes must be a non-empty array")
    if schema is not None:
        expected = schema.get("properties", {}).get("schema_version", {}).get("const")
        add(errors, expected == EXPECTED_VERSION, "schema file version does not match validator")
    if not isinstance(scenes, list):
        return errors

    scene_ids: set[str] = set()
    event_ids: set[str] = set()
    for scene_index, scene in enumerate(scenes):
        loc = f"scenes[{scene_index}]"
        add(errors, isinstance(scene, dict), f"{loc} must be an object")
        if not isinstance(scene, dict):
            continue
        scene_id = scene.get("scene_id")
        add(errors, is_nonempty_string(scene_id), f"{loc}.scene_id is required")
        if isinstance(scene_id, str):
            add(errors, scene_id not in scene_ids, f"duplicate scene_id: {scene_id}")
            scene_ids.add(scene_id)
        source_ref = scene.get("source_ref")
        add(errors, isinstance(source_ref, dict), f"{loc}.source_ref must be an object")
        if isinstance(source_ref, dict):
            for key in ("kind", "start", "end"):
                add(errors, is_nonempty_string(source_ref.get(key)), f"{loc}.source_ref.{key} is required")

        beats = scene.get("required_beats")
        add(errors, isinstance(beats, list) and bool(beats), f"{loc}.required_beats must be non-empty")
        beat_ids: set[str] = set()
        if isinstance(beats, list):
            for beat_index, beat in enumerate(beats):
                beat_loc = f"{loc}.required_beats[{beat_index}]"
                add(errors, isinstance(beat, dict), f"{beat_loc} must be an object")
                if not isinstance(beat, dict):
                    continue
                beat_id = beat.get("beat_id")
                add(errors, is_nonempty_string(beat_id), f"{beat_loc}.beat_id is required")
                if isinstance(beat_id, str):
                    add(errors, beat_id not in beat_ids, f"{loc} duplicate beat_id: {beat_id}")
                    beat_ids.add(beat_id)
                add(errors, is_nonempty_string(beat.get("description")), f"{beat_loc}.description is required")
                add(errors, is_nonempty_string(beat.get("source_ref")), f"{beat_loc}.source_ref is required")

        add(errors, is_nonempty_string(scene.get("scene_objective")), f"{loc}.scene_objective is required")
        registry = scene.get("subject_registry", [])
        add(errors, isinstance(registry, list), f"{loc}.subject_registry must be an array when present")
        subject_ids: set[str] = set()
        if isinstance(registry, list):
            for subject_index, subject in enumerate(registry):
                subject_loc = f"{loc}.subject_registry[{subject_index}]"
                add(errors, isinstance(subject, dict), f"{subject_loc} must be an object")
                if not isinstance(subject, dict):
                    continue
                subject_id = subject.get("subject_id")
                add(errors, is_nonempty_string(subject_id), f"{subject_loc}.subject_id is required")
                if isinstance(subject_id, str):
                    add(errors, subject_id not in subject_ids, f"{loc} duplicate subject_id: {subject_id}")
                    subject_ids.add(subject_id)
                add(errors, is_nonempty_string(subject.get("display_name")), f"{subject_loc}.display_name is required")

        shots = scene.get("shots")
        add(errors, isinstance(shots, list) and bool(shots), f"{loc}.shots must be non-empty")
        if not isinstance(shots, list):
            continue
        shot_ids = {shot.get("shot_id") for shot in shots if isinstance(shot, dict) and isinstance(shot.get("shot_id"), str)}
        add(errors, len(shot_ids) == len(shots), f"{loc}.shot_id values must be unique and present")
        orders: list[int] = []
        for shot_index, shot in enumerate(shots):
            shot_loc = f"{loc}.shots[{shot_index}]"
            add(errors, isinstance(shot, dict), f"{shot_loc} must be an object")
            if not isinstance(shot, dict):
                continue
            order = shot.get("order")
            add(errors, isinstance(order, int) and not isinstance(order, bool), f"{shot_loc}.order must be an integer")
            if isinstance(order, int):
                orders.append(order)
            refs = string_list(errors, shot.get("source_beats"), f"{shot_loc}.source_beats", allow_empty=False)
            for ref in refs:
                add(errors, ref in beat_ids, f"{shot_loc}.source_beats references unknown beat {ref}")
            add(errors, is_nonempty_string(shot.get("narrative_purpose")), f"{shot_loc}.narrative_purpose is required")
            duration = shot.get("duration")
            add(errors, isinstance(duration, dict), f"{shot_loc}.duration must be an object")
            if isinstance(duration, dict):
                start, end, length = duration.get("start_seconds"), duration.get("end_seconds"), duration.get("duration_seconds")
                numeric = all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in (start, end, length))
                add(errors, numeric, f"{shot_loc}.duration values must be numbers")
                if numeric:
                    add(errors, start >= 0 and end > start and length > 0, f"{shot_loc}.duration range is invalid")
                    add(errors, abs((end - start) - length) <= 1e-6, f"{shot_loc}.duration_seconds does not equal end-start")
            subject_refs = string_list(errors, shot.get("subjects"), f"{shot_loc}.subjects")
            for ref in subject_refs:
                add(errors, ref in subject_ids, f"{shot_loc}.subjects references unknown subject {ref}")
            framing = shot.get("framing")
            add(errors, isinstance(framing, dict) and is_nonempty_string(framing.get("scale")), f"{shot_loc}.framing.scale is required")
            camera = shot.get("camera")
            add(errors, isinstance(camera, dict), f"{shot_loc}.camera must be an object")
            if isinstance(camera, dict):
                for key in ("viewpoint", "angle", "movement"):
                    add(errors, is_nonempty_string(camera.get(key)), f"{shot_loc}.camera.{key} is required")
                if "expanded" in camera:
                    expanded = camera["expanded"]
                    add(errors, isinstance(expanded, dict), f"{shot_loc}.camera.expanded must be an object")
                    if isinstance(expanded, dict):
                        add(errors, is_nonempty_string(expanded.get("risk_reason")), f"{shot_loc}.camera.expanded.risk_reason is required")
                        string_list(errors, expanded.get("facts"), f"{shot_loc}.camera.expanded.facts", allow_empty=False)
            blocking = shot.get("blocking_action")
            add(errors, isinstance(blocking, dict) and is_nonempty_string(blocking.get("summary")), f"{shot_loc}.blocking_action.summary is required")
            if "dialogue_audio" in shot:
                add(errors, isinstance(shot["dialogue_audio"], list), f"{shot_loc}.dialogue_audio must be an array")
                if isinstance(shot["dialogue_audio"], list):
                    for event_index, event in enumerate(shot["dialogue_audio"]):
                        validate_audio_event(event, f"{shot_loc}.dialogue_audio[{event_index}]", shot_ids, subject_ids, event_ids, errors)
            if "continuity_delta" in shot:
                continuity = shot["continuity_delta"]
                add(errors, isinstance(continuity, dict) and is_nonempty_string(continuity.get("summary")), f"{shot_loc}.continuity_delta.summary is required")
                if isinstance(continuity, dict):
                    for ref in string_list(errors, continuity.get("subject_refs", []), f"{shot_loc}.continuity_delta.subject_refs"):
                        add(errors, ref in subject_ids, f"{shot_loc}.continuity_delta references unknown subject {ref}")
            if "generation_constraints" in shot:
                validate_constraints(shot["generation_constraints"], f"{shot_loc}.generation_constraints", errors)
        add(errors, orders == list(range(1, len(shots) + 1)), f"{loc}.shots order must be contiguous and match array order")

        if "audio_plan" in scene:
            add(errors, isinstance(scene["audio_plan"], list), f"{loc}.audio_plan must be an array")
            if isinstance(scene["audio_plan"], list):
                for event_index, event in enumerate(scene["audio_plan"]):
                    validate_audio_event(event, f"{loc}.audio_plan[{event_index}]", shot_ids, subject_ids, event_ids, errors)
        if "continuity_end_state" in scene:
            continuity = scene["continuity_end_state"]
            add(errors, isinstance(continuity, dict) and is_nonempty_string(continuity.get("summary")), f"{loc}.continuity_end_state.summary is required")
            if isinstance(continuity, dict):
                for ref in string_list(errors, continuity.get("subject_refs", []), f"{loc}.continuity_end_state.subject_refs"):
                    add(errors, ref in subject_ids, f"{loc}.continuity_end_state references unknown subject {ref}")
        if "generation_constraints" in scene:
            validate_constraints(scene["generation_constraints"], f"{loc}.generation_constraints", errors)

        core_scene = {key: value for key, value in scene.items()}
        check_forbidden_keys(core_scene, loc, errors)

    legacy = data.get("legacy_extensions")
    if legacy is not None:
        add(errors, isinstance(legacy, dict), "legacy_extensions must be an object")
        if isinstance(legacy, dict):
            add(errors, legacy.get("classification") == "LEGACY_ONLY", "legacy_extensions.classification must be LEGACY_ONLY")
            add(errors, legacy.get("migration_status") == "LEGACY_EXTENSION", "legacy_extensions.migration_status must be LEGACY_EXTENSION")
            original = legacy.get("original_document")
            expected_hash = legacy.get("original_document_sha256")
            add(errors, isinstance(original, str), "legacy_extensions.original_document must be a string")
            add(errors, is_nonempty_string(expected_hash), "legacy_extensions.original_document_sha256 is required")
            if isinstance(original, str) and isinstance(expected_hash, str):
                actual = hashlib.sha256(original.encode("utf-8")).hexdigest().upper()
                add(errors, actual == expected_hash, "legacy_extensions original document hash mismatch")
    return errors


def validate_generation_ready(data: dict) -> list[str]:
    """Reject unresolved or migration-only values without re-directing."""
    errors: list[str] = []
    if "legacy_extensions" in data:
        errors.append("generation_ready: legacy_extensions is migration-only")
    scenes = data.get("scenes")
    if not isinstance(scenes, list):
        return errors
    for scene_index, scene in enumerate(scenes):
        loc = f"scenes[{scene_index}]"
        if not isinstance(scene, dict):
            continue
        source_ref = scene.get("source_ref")
        if isinstance(source_ref, dict):
            for key in ("kind", "start", "end"):
                add(errors, is_resolved_string(source_ref.get(key)), f"generation_ready: {loc}.source_ref.{key} must be resolved")
            add(errors, source_ref.get("kind") != "legacy_declared_range", f"generation_ready: {loc}.source_ref.kind cannot be legacy_declared_range")
        add(errors, is_resolved_string(scene.get("scene_objective")), f"generation_ready: {loc}.scene_objective must be resolved")
        beats = scene.get("required_beats", [])
        if isinstance(beats, list):
            for beat_index, beat in enumerate(beats):
                if not isinstance(beat, dict):
                    continue
                beat_loc = f"{loc}.required_beats[{beat_index}]"
                add(errors, is_resolved_string(beat.get("description")), f"generation_ready: {beat_loc}.description must be resolved")
                source = beat.get("source_ref")
                add(errors, is_resolved_string(source), f"generation_ready: {beat_loc}.source_ref must be resolved")
                if isinstance(source, str):
                    add(errors, not source.startswith("legacy:"), f"generation_ready: {beat_loc}.source_ref cannot use legacy shadow anchors")

        shots = scene.get("shots", [])
        if isinstance(shots, list):
            for shot_index, shot in enumerate(shots):
                shot_loc = f"{loc}.shots[{shot_index}]"
                if not isinstance(shot, dict):
                    continue
                add(errors, is_resolved_string(shot.get("narrative_purpose")), f"generation_ready: {shot_loc}.narrative_purpose must be resolved")
                framing = shot.get("framing")
                if isinstance(framing, dict):
                    add(errors, is_resolved_string(framing.get("scale")), f"generation_ready: {shot_loc}.framing.scale must be resolved")
                camera = shot.get("camera")
                if isinstance(camera, dict):
                    for key in ("viewpoint", "angle", "movement"):
                        add(errors, is_resolved_string(camera.get(key)), f"generation_ready: {shot_loc}.camera.{key} must be resolved")
                    add(errors, "details" not in camera, f"generation_ready: {shot_loc}.camera.details is migration-only")
                    expanded = camera.get("expanded")
                    if isinstance(expanded, dict):
                        add(errors, is_resolved_string(expanded.get("risk_reason")), f"generation_ready: {shot_loc}.camera.expanded.risk_reason must be resolved")
                        facts = expanded.get("facts", [])
                        if isinstance(facts, list):
                            add(errors, all(is_resolved_string(item) for item in facts), f"generation_ready: {shot_loc}.camera.expanded.facts must be resolved")
                blocking = shot.get("blocking_action")
                if isinstance(blocking, dict):
                    add(errors, is_resolved_string(blocking.get("summary")), f"generation_ready: {shot_loc}.blocking_action.summary must be resolved")
                for key in ("composition", "spatial_relation", "continuity_delta"):
                    value = shot.get(key)
                    if isinstance(value, dict):
                        add(errors, is_resolved_string(value.get("summary")), f"generation_ready: {shot_loc}.{key}.summary must be resolved")
                if "visual_emphasis" in shot:
                    add(errors, is_resolved_string(shot.get("visual_emphasis")), f"generation_ready: {shot_loc}.visual_emphasis must be resolved")
                events = shot.get("dialogue_audio", [])
                if isinstance(events, list):
                    for event_index, event in enumerate(events):
                        if not isinstance(event, dict):
                            continue
                        event_loc = f"{shot_loc}.dialogue_audio[{event_index}]"
                        add(errors, event.get("kind") != "unknown", f"generation_ready: {event_loc}.kind must be resolved")
                        if event.get("kind") == "dialogue":
                            add(errors, is_resolved_string(event.get("speaker_ref")), f"generation_ready: {event_loc}.speaker_ref must be resolved")
                            add(errors, is_resolved_string(event.get("text")), f"generation_ready: {event_loc}.text must be resolved")
                            if "delivery" in event:
                                add(errors, is_resolved_string(event.get("delivery")), f"generation_ready: {event_loc}.delivery must be resolved when present")
                            add(errors, is_resolved_string(event.get("visibility")), f"generation_ready: {event_loc}.visibility must be resolved")

        for key in ("spatial_anchor", "initial_state", "continuity_end_state"):
            value = scene.get(key)
            if isinstance(value, dict):
                add(errors, is_resolved_string(value.get("summary")), f"generation_ready: {loc}.{key}.summary must be resolved")
        audio_plan = scene.get("audio_plan", [])
        if isinstance(audio_plan, list):
            for event_index, event in enumerate(audio_plan):
                if isinstance(event, dict):
                    event_loc = f"{loc}.audio_plan[{event_index}]"
                    add(errors, event.get("kind") != "unknown", f"generation_ready: {event_loc}.kind must be resolved")
                    if event.get("kind") == "dialogue":
                        add(errors, is_resolved_string(event.get("speaker_ref")), f"generation_ready: {event_loc}.speaker_ref must be resolved")
                        add(errors, is_resolved_string(event.get("text")), f"generation_ready: {event_loc}.text must be resolved")
                        if "delivery" in event:
                            add(errors, is_resolved_string(event.get("delivery")), f"generation_ready: {event_loc}.delivery must be resolved when present")
                        add(errors, is_resolved_string(event.get("visibility")), f"generation_ready: {event_loc}.visibility must be resolved")
        if scene_index < len(scenes) - 1 and isinstance(scenes[scene_index + 1], dict):
            following = scenes[scene_index + 1]
            boundary_declared = "continuity_end_state" in scene or "initial_state" in following
            if boundary_declared:
                add(errors, isinstance(scene.get("continuity_end_state"), dict), f"generation_ready: {loc}.continuity_end_state is required for the declared scene boundary")
                add(errors, isinstance(following.get("initial_state"), dict), f"generation_ready: scenes[{scene_index + 1}].initial_state is required for the declared scene boundary")
    return errors


def validate_ir_profile(
    data: object,
    schema: dict | None = None,
    profile: str = "legacy_import",
) -> list[str]:
    normalized = PROFILE_ALIASES.get(profile)
    if normalized is None:
        return [f"unknown validation profile: {profile}"]
    errors = validate_ir(data, schema)
    if normalized == "generation_ready" and isinstance(data, dict):
        errors.extend(validate_generation_ready(data))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "schemas" / "storyboard-ir.draft.schema.json",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_ALIASES),
        default="legacy_import",
        help="legacy_import/shadow allow reversible imports; generation_ready rejects unresolved director decisions",
    )
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    errors = validate_ir_profile(data, schema, profile=args.profile)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    scene_count = len(data["scenes"])
    shot_count = sum(len(scene["shots"]) for scene in data["scenes"])
    print(f"PASS IR Draft profile={args.profile} scenes={scene_count} shots={shot_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

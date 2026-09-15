#!/usr/bin/env python3
"""Verify Tester Package dependency and delivery checksums."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PACKAGE_ROOT / "skill"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def safe_relative(path_text: str) -> bool:
    path = Path(path_text)
    return not path.is_absolute() and ".." not in path.parts


def main() -> int:
    missing: list[str] = []
    mismatches: list[str] = []
    unrecorded: list[str] = []
    errors: list[str] = []

    dependency_path = SKILL_ROOT / "candidate_dependency_manifest.json"
    delivery_path = PACKAGE_ROOT / "manifests" / "delivery_manifest.json"
    checksum_path = PACKAGE_ROOT / "manifests" / "checksums.sha256"
    for path in (dependency_path, delivery_path, checksum_path):
        if not path.is_file():
            missing.append(path.relative_to(PACKAGE_ROOT).as_posix())
    if missing:
        print("Package integrity: FAIL")
        print("Missing:")
        for item in missing:
            print(f"- {item}")
        return 1

    try:
        dependency = json.loads(dependency_path.read_text(encoding="utf-8"))
        delivery = json.loads(delivery_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print("Package integrity: FAIL")
        print(f"Invalid JSON: {exc}")
        return 1

    recorded: set[str] = set()
    for item in dependency.get("dependencies", []):
        relative = item.get("path")
        if not isinstance(relative, str) or not safe_relative(relative):
            errors.append(f"Unsafe dependency path: {relative!r}")
            continue
        recorded.add(relative)
        path = SKILL_ROOT / relative
        if not path.is_file():
            missing.append("skill/" + relative)
            continue
        actual = sha256(path)
        if actual != item.get("sha256"):
            mismatches.append(
                f"skill/{relative}: expected {item.get('sha256')} actual {actual}"
            )

    actual_skill_files = {
        path.relative_to(SKILL_ROOT).as_posix()
        for path in SKILL_ROOT.rglob("*")
        if path.is_file() and path.name != "candidate_dependency_manifest.json"
    }
    unrecorded.extend("skill/" + item for item in sorted(actual_skill_files - recorded))
    missing.extend("skill/" + item for item in sorted(recorded - actual_skill_files))

    model_count = sum(
        1 for item in dependency.get("dependencies", []) if item.get("model_context") is True
    )
    if model_count != dependency.get("model_context_file_count"):
        errors.append(
            f"model_context count expected {dependency.get('model_context_file_count')} actual {model_count}"
        )

    dependency_hash = sha256(dependency_path)
    if delivery.get("skill_dependency_manifest_sha256") != dependency_hash:
        mismatches.append(
            "manifests/delivery_manifest.json skill_dependency_manifest_sha256"
        )

    for raw_line in checksum_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            expected, relative = line.split(None, 1)
        except ValueError:
            errors.append(f"Malformed checksum line: {raw_line}")
            continue
        relative = relative.strip().lstrip("*")
        if not safe_relative(relative):
            errors.append(f"Unsafe checksum path: {relative}")
            continue
        path = PACKAGE_ROOT / relative
        if not path.is_file():
            missing.append(relative)
        elif sha256(path) != expected.upper():
            mismatches.append(relative)

    if missing or mismatches or unrecorded or errors:
        print("Package integrity: FAIL")
        if missing:
            print("Missing:")
            for item in sorted(set(missing)):
                print(f"- {item}")
        if mismatches:
            print("Hash mismatch:")
            for item in mismatches:
                print(f"- {item}")
        if unrecorded:
            print("Unrecorded Skill files:")
            for item in unrecorded:
                print(f"- {item}")
        if errors:
            print("Manifest errors:")
            for item in errors:
                print(f"- {item}")
        return 1

    print("Package integrity: PASS")
    print(f"Skill dependencies: {len(recorded)}")
    print(f"Model-context files: {model_count}")
    print("External runtime dependencies: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check Tester Package prerequisites without running storyboard logic."""

from __future__ import annotations

import json
import platform
from pathlib import Path
import sys
import tempfile


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MINIMUM_PYTHON = (3, 10)


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []
    passes: list[str] = []

    version = sys.version_info[:3]
    if version < MINIMUM_PYTHON:
        failures.append(
            f"Python {version[0]}.{version[1]}.{version[2]} is below required 3.10"
        )
    else:
        passes.append(f"Python {version[0]}.{version[1]}.{version[2]}")

    try:
        probe = "中文 UTF-8 ✓"
        if probe.encode("utf-8").decode("utf-8") != probe:
            raise UnicodeError("UTF-8 round-trip changed text")
        passes.append(f"UTF-8 capability; stdout={sys.stdout.encoding or 'unknown'}")
    except UnicodeError as exc:
        failures.append(f"UTF-8 capability: {exc}")

    required = [
        "README.md",
        "QUICKSTART.md",
        "skill/SKILL.md",
        "skill/core/storyboard-core.md",
        "skill/routing/route_candidate.py",
        "skill/scripts/validate_storyboard_ir.py",
        "skill/adapters/render_seedance_2.py",
        "skill/runtime/trace_candidate_runtime.py",
        "skill/candidate_dependency_manifest.json",
        "manifests/delivery_manifest.json",
        "manifests/checksums.sha256",
    ]
    missing = [item for item in required if not (PACKAGE_ROOT / item).is_file()]
    if missing:
        failures.append("Required files missing: " + ", ".join(missing))
    else:
        passes.append(f"Required files present ({len(required)})")

    required_dirs = ["skill", "examples", "templates", "scripts", "config", "manifests"]
    missing_dirs = [item for item in required_dirs if not (PACKAGE_ROOT / item).is_dir()]
    if missing_dirs:
        failures.append("Required directories missing: " + ", ".join(missing_dirs))
    else:
        passes.append(f"Required directories present ({len(required_dirs)})")

    manifest_path = PACKAGE_ROOT / "skill" / "candidate_dependency_manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            passes.append(
                f"Dependency manifest readable ({len(manifest.get('dependencies', []))} entries)"
            )
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"Dependency manifest unreadable: {exc}")

    try:
        with tempfile.TemporaryDirectory(prefix="storyboard_tester_env_") as raw:
            probe_path = Path(raw) / "write-check.txt"
            probe_path.write_text("ok", encoding="utf-8")
            passes.append("Temporary output directory is writable")
    except OSError as exc:
        failures.append(f"No writable temporary directory: {exc}")

    system = platform.system()
    if system == "Windows":
        passes.append("Platform: Windows (validated platform family)")
    else:
        warnings.append(
            f"Platform: {system}; portable in design but not equivalently validated"
        )

    print("Environment check")
    for item in passes:
        print(f"PASS: {item}")
    for item in warnings:
        print(f"WARNING: {item}")
    for item in failures:
        print(f"FAIL: {item}")
    if failures:
        print("Environment status: FAIL")
        return 1
    print("Environment status: PASS" if not warnings else "Environment status: PASS WITH WARNING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

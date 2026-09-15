"""Release-frozen deterministic, genre-agnostic route proposal.

The router receives script text only. Fixture expectations are used by tests after
routing and are never imported here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


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

BASE_FILES = [
    "core/storyboard-core.md",
    "core/generation-contract.md",
    "core/storyboard-ir.md",
]


def hits(text: str, patterns: tuple[str, ...]) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text)]


def route_script(script: str) -> dict:
    if not script.strip():
        raise ValueError("script must not be empty")

    evidence: dict[str, list[str]] = {}
    evidence["cross_scene"] = hits(script, (r"紧接", r"仍有同一|仍在", r"Scene", r"离开。\s*\n?\s*[^。]{0,12}(?:间|厅|室|外)。"))
    evidence["group"] = hits(script, (r"三人|众人", r"围着.+争", r"打断两人", r"同时转向", r"三名|四人"))
    evidence["action"] = hits(script, (r"追赶|追上|追去", r"撞退|撞击|砸下|断裂", r"挣脱|缠住|跪地", r"跑下|进入车厢|跨过", r"沿.+通道", r"推开门进入", r"移动。"))
    evidence["emotion"] = hits(script, (r"愣住|眼泪|哭|笑", r"攥紧.+松开", r"呼吸停住", r"情绪|颤抖"))
    evidence["reveal"] = hits(script, (r"无署名|才拆开|背面写着", r"察觉异常|倒影", r"不得|隐藏", r"人影", r"脚步声|开门声.+躲避"))
    evidence["establishing"] = hits(script, (r"沿河而建|连接.+城门|位于.+内侧", r"离开.+进入相连", r"清晨，", r"从.+进入相连"))
    evidence["dialogue"] = hits(script, (r"[\u4e00-\u9fff]{1,8}[：:]“", r"的“[^”]+”先从画外", r"边.+边喊[：:]"))

    cross_scene_primary = "紧接" in script and bool(re.search(r"仍有同一|仍在|同一.+仍", script))
    if cross_scene_primary:
        dominant = "spatial-continuity"
    elif evidence["group"]:
        dominant = "group-dialogue"
    elif evidence["action"]:
        dominant = "action-movement"
    elif len(evidence["emotion"]) >= 2 and not evidence["reveal"]:
        dominant = "emotion-performance"
    elif evidence["reveal"]:
        dominant = "suspense-reveal"
    elif evidence["establishing"]:
        dominant = "establishing-transition"
    elif evidence["dialogue"]:
        dominant = "dialogue"
    else:
        dominant = "establishing-transition"

    secondary = None
    if dominant == "action-movement" and evidence["dialogue"]:
        secondary = "dialogue"
    elif dominant == "suspense-reveal" and len(evidence["emotion"]) >= 1:
        secondary = "emotion-performance"
    elif dominant == "group-dialogue" and evidence["establishing"]:
        secondary = "establishing-transition"
    elif dominant == "spatial-continuity" and evidence["reveal"]:
        secondary = "suspense-reveal"

    modifiers: list[str] = []
    true_audio_overlap = bool(re.search(r"画外|说到.+后画面切|声音先.+随后画面切", script))
    if true_audio_overlap and dominant != "audio-transition" and secondary != "audio-transition":
        modifiers.append("audio-transition")

    long_waypoint_path = all(term in script for term in ("入口", "闸机", "楼梯", "站台", "车厢"))
    spatial_risk = long_waypoint_path or bool(re.search(
        r"左侧|右侧|岔口|镜中|倒影|切到门内侧|中间通道|同一次撞击",
        script,
    ))
    if spatial_risk and dominant != "spatial-continuity" and secondary != "spatial-continuity":
        modifiers.append("spatial-continuity")

    modifiers = modifiers[:2]
    selected = [dominant] + ([secondary] if secondary else []) + modifiers
    model_read_files = BASE_FILES + [CAPABILITY_PATHS[item] for item in selected]
    return {
        "schema_version": "phase7.5-shadow-route-v1",
        "script_sha256": hashlib.sha256(script.encode("utf-8")).hexdigest().upper(),
        "dominant": dominant,
        "secondary": secondary,
        "modifiers": modifiers,
        "route_confidence": "high" if any(evidence.values()) else "low",
        "uncertainty": [] if any(evidence.values()) else ["no strong directing cue"],
        "cue_evidence": {key: value for key, value in evidence.items() if value},
        "model_read_files": model_read_files,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path, help="plain UTF-8 script text; no fixture metadata")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = route_script(args.script.read_text(encoding="utf-8"))
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

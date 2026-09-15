# Storyboard Routing Contract

Status: `FORMALIZED_PRODUCTION_CANDIDATE`; long-script and implicit-semantics coverage remains limited.

Routing selects guidance, not story permission. It is genre-agnostic.

## Route budget

- one dominant capability;
- zero or one secondary capability when it materially changes the Shot plan;
- zero to two narrow modifiers for explicit continuity, audio-transition, or camera risk.

This is a Runtime budget, not a hard business limit. A genuinely more complex Scene emits `ROUTE_ESCALATION_REQUIRED`; never omit required ability and never silently load all modules.

## Dominant decision

Choose the first description matching the Scene's principal result:

1. connected boundary/state inheritance → `spatial-continuity`;
2. three or more active participants/attention transfer → `group-dialogue`;
3. movement/contact/pursuit/impact/transformation → `action-movement`;
4. observable internal performance change → `emotion-performance`;
5. withholding/anomaly/recognition/reveal → `suspense-reveal`;
6. new time/place relation or connected-space transition → `establishing-transition`;
7. otherwise spoken exchange → `dialogue`.

Never route by genre label.

## Secondary and modifiers

Use a secondary only when the second problem changes the plan, for example action coordinated by dialogue or a reveal whose reception is required. Use:

- `spatial-continuity` for axis, direction, waypoint, mirror/POV, same action across cut, or boundary-state risk;
- `audio-transition` for true L/J cut or other sound crossing a Shot boundary;
- `cinematic-high-risk` only for concrete high-impact camera risk.

## Uncertainty

When readings tie, prefer the capability governing the final causal result. If still uncertain, select one dominant, record low confidence and alternatives, and request escalation when necessary. Do not all-load.

## Trace

Record script hash, cue evidence, selected roles, confidence, exact model-readable files/bytes, and exclusions. Expected IR, tests, QA, Workflow, Adapter, Legacy, Python, and Schema must not enter Director model context.

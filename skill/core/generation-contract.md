# Script to Storyboard IR Generation Contract

Status: `FORMALIZED_PRODUCTION_CANDIDATE`.

## Allowed inputs

The Director may use only the frozen script, explicit user constraints, the three Candidate Core contracts, the route decision, and selected capability files. Expected IR, golden output, Legacy 11-module output, QA verdicts, workflow state, project fixtures, and Adapter instructions are forbidden generation inputs.

## One-pass directing sequence

1. Identify narrative Scene boundaries from story time/place and connected state, not video-model length. Long-script Scene design remains under review.
2. Extract the minimum complete required beats: events, exact dialogue, reveals, reactions, results, and state changes, each with a source anchor.
3. State one Scene objective describing what the audience must understand or perceive by Scene end.
4. Apply selected capabilities once to choose a compact Shot plan. Never generate Legacy modules first.
5. For every Shot resolve source beats, narrative purpose, executable duration, subjects, framing, compact camera, and blocking/action with a visible result or end condition.
6. Add dialogue/audio, spatial, composition, emphasis, continuity, or constraints only when needed. Omit unused optional fields rather than writing empty or generic defaults.
7. Emit Candidate IR and pass `GENERATION_READY`. Validation reports definite gaps; it does not choose a better aesthetic solution.

## Required resolution

Scene objective, beat descriptions/anchors, Shot purpose, framing, camera viewpoint/angle/movement, blocking/action, exact dialogue speaker/text/visibility, and every declared spatial or continuity boundary must be resolved. `unknown`, `missing`, `not_applicable`, `legacy_declared_range`, `legacy_extensions`, `camera.details`, and meaningless defaults are forbidden.

## Camera scope

Ordinary Shots use `viewpoint`, `angle`, and `movement`. Use `camera.expanded` only after the routed high-risk modifier identifies a concrete occlusion, path-volume, vertical-geometry, POV/reflection, or terminal-composition risk. Do not add expanded facts for completeness.

## State authority

- Scene start/end states are boundary facts only when continuity matters.
- Shot delta names a change occurring in that Shot and inherited later.
- A declared cross-Scene boundary supplies both prior end and following initial state.
- Visual identity and VFX state stay attached to the same subject unless the script changes them.

## Output boundary

IR contains Director semantics plus protocol/validation identifiers. Runtime hashes, selected files, validator output, Adapter provenance, QA, workflow, and comparison results remain sidecar data.

Passing this contract proves structural completion for the input, not optimal directing or real-video realization.

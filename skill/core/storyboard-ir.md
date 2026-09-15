# Storyboard IR — V0.4 Production Candidate

Status: `FORMALIZED_PRODUCTION_CANDIDATE`. Schema ID: `storyboard-ir/0.4-production-candidate`.

The IR separates Director decisions from Seedance wording. Structural sufficiency is validated on 14 generalization cases and 42 Shots; real-video consumption quality remains unvalidated.

## Information classes

| Class | Fields | Meaning |
|---|---|---|
| `PROTOCOL_METADATA` | `schema_version`, `document_id` | Serialization/version/trace identity. Required by protocol, not a directing fact and never Adapter prose. |
| `DIRECTOR_SEMANTICS` | Scene objective/beats/subjects/space/state/audio/constraints and Shot purpose/duration/framing/camera/action/composition/emphasis/dialogue/spatial/delta | Decisions about what the audience sees/hears and how the Shot functions. |
| `VALIDATION_DATA` | Scene/Shot/beat/event IDs, order, source anchors, reference arrays | Coverage, ordering, identity, dependency, and trace checks. IDs do not themselves direct the image. |
| `ADAPTER_FACING_DATA` | Resolved display names and applicable Director semantics needed to generate the video | A projection of Director semantics, not a separate authority. Internal IDs appear only in wrappers/sidecars. |

Being Schema-required does not promote protocol metadata or validation identifiers into Director semantics.

## Required document shape

- `schema_version`: fixed Candidate protocol identifier.
- `document_id`: stable trace identifier.
- `scenes`: ordered narrative Scenes.

`legacy_extensions` is not part of Candidate IR. Reversible Legacy imports remain in the preserved Draft/Shadow schema and tools.

## Scene

Required:

- `scene_id` (`VALIDATION_DATA`)
- `source_ref` (`VALIDATION_DATA`)
- `required_beats`: ID/anchor validation plus beat description Director semantics
- `scene_objective`
- `shots`

Conditional Director semantics:

- `subject_registry`
- `spatial_anchor`
- `initial_state`
- `audio_plan`
- `continuity_end_state`
- `generation_constraints`

## Shot

Required:

- validation: `shot_id`, `order`, `source_beats`
- Director: `narrative_purpose`, `duration`, `subjects`, `framing`, `camera`, `blocking_action`

Conditional:

- `composition`
- `visual_emphasis`
- `dialogue_audio`
- `spatial_relation`
- `continuity_delta`
- `generation_constraints`

## Camera and composition

Ordinary camera uses only `viewpoint`, `angle`, and `movement`. `camera.expanded` is conditional high-risk evidence with a concrete `risk_reason`. `camera.details` is absent from Candidate Schema and remains Legacy-import-only.

Composition is an optional compact `summary`; a mandatory ten-field breakdown is not a Core requirement.

## Dialogue and audio

Dialogue/audio events bind an event, exact `shot_refs`, kind, description, and—when dialogue—speaker, text, delivery when needed, and visibility. Legacy D/G/S names are not required semantics. `unknown` audio kind and `legacy_event_id` are excluded from Candidate Schema.

## Continuity authority

- `scene.continuity_end_state` states a Scene boundary result.
- `shot.continuity_delta` states only a change explicitly assigned to that Shot.
- Never copy Scene end state to the last Shot by inference.
- If either side of a connected cross-Scene boundary is declared, Generation Ready requires both prior end and following initial state.

## Validation profiles

Candidate generation uses `GENERATION_READY` only. It rejects unresolved critical decisions, Legacy anchors/fields, migration fields, empty defaults, invalid references, noncontiguous Shot order, and duration arithmetic errors.

`LEGACY_IMPORT/SHADOW` remains a separate preserved Legacy protocol outside this Tester package. Candidate formalization does not delete, embed or reinterpret that rollback-only protocol.

## Adapter projection

The deterministic Adapter may consume required-beat descriptions, subject display names, duration, narrative purpose, framing, compact/expanded camera, action, applicable spatial/composition/emphasis/audio/continuity/constraints, and explicit model options. It never consumes protocol metadata as prompt prose, `camera.details`, Legacy extensions, QA, or Workflow.

## Scene, Shot, and Segment

`Narrative Scene != Director Shot != Generation Segment`. Candidate IR stops at Director Shot. Segment grouping is an Adapter execution strategy and may be 1:1 or N:1 without changing IR.

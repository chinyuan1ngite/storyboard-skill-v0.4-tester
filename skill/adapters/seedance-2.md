# Seedance 2.0 Deterministic Adapter Contract

Status: `STRUCTURALLY_VALIDATED` / `REAL_VIDEO_UNVALIDATED`.

## Boundary

```text
GENERATION_READY Candidate IR
  -> deterministic renderer tool
  -> Seedance prompt + provenance
```

The Adapter is not a second Director and requires no Adapter rule file in model context. It preserves Shot order/count, beat allocation, duration, subjects, framing, camera, action order/result, dialogue/speaker, reveal, spatial facts, continuity, and hard constraints.

It may reorder equivalent language, remove repetition, clarify subject references, and express explicit render-only/model options. It may not add facts, change the IR, call Legacy 11 modules, or consume QA/Workflow/project answers. Unsupported faithful expression produces degradation and manual review.

## Inputs

- one `storyboard-ir/0.4-production-candidate` document passing `GENERATION_READY`;
- optional explicit `render_style` classified `RENDER_ONLY`;
- model aspect ratio and reference handles with declared purpose;
- explicit model-negative constraints.

Director-style requests that alter Shot count, framing, viewpoint, movement, action, composition logic, reveal, or timing must return to the Director layer.

## Field projection

For each execution Segment, express only applicable Director semantics: duration, purpose, required story facts, display names, framing, camera, action, space/composition/emphasis, dialogue/audio relation, continuity, and constraints. Protocol metadata, source anchors, internal IDs, validation evidence, migration data, QA, and Workflow remain outside final prompt prose.

`camera.details` and `legacy_extensions` are impossible in Candidate Schema. Legacy Module 11 bug patches never load. Explicit model-negative options do not become Storyboard Core.

## Validation claim

The deterministic renderer has 14-case/42-Shot prompt-equivalence and provenance evidence against the Phase 8 structurally validated outputs. This proves expression stability, not Seedance instruction following, video quality, lip-sync, audio continuity, or optimal wording.

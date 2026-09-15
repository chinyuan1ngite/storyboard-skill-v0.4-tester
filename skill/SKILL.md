---
name: ai-series-storyboard-seedance-candidate
description: Production-candidate workflow for turning a general episodic script into model-independent Storyboard IR and deterministic Seedance 2.0 prompts. Use for structurally validated V0.4 candidate runs; real-video quality, lip-sync, L/J-cut realization, and optimal Generation Segment mapping remain unvalidated.
---

# General Episodic Storyboard Director — V0.4 Production Candidate

Status: `PRODUCTION_CANDIDATE_STRUCTURALLY_VALIDATED`. Real-video evaluation was skipped. This package is not the active production default and does not replace V0.3.31 rollback.

## Runtime path

1. Freeze the current script and explicit user constraints as the only story authority.
2. Run `routing/route_candidate.py` on the script. Read `core/storyboard-core.md`, `core/generation-contract.md`, `core/storyboard-ir.md`, and only the capability files named by the route.
3. Make the directing decision once and emit `storyboard-ir/0.4-production-candidate` IR.
4. Run `scripts/validate_storyboard_ir.py --profile generation_ready`. Fix only reported missing, contradictory, invalid, or untraceable director facts; do not re-direct for taste.
5. Run `adapters/render_seedance_2.py`. Prompt expression is deterministic and does not load Adapter rules into a second model context.
6. Return copy-ready prompts and any explicit degradation/manual-review notice. Keep IR, provenance, QA, and workflow state internal unless requested.

## Authority order

1. current script and explicit user revision;
2. Storyboard Core invariants;
3. selected scene capabilities;
4. Storyboard IR field meanings;
5. deterministic Adapter expression.

The Adapter cannot alter Shot count/order, beats, framing, camera, action, dialogue, reveal, identity, space, continuity, or story constraints.

## Progressive disclosure

Always load only the three Core contracts plus routed capabilities. `cinematic-high-risk` is a narrow optional modifier, never a genre or spectacle default. QA and Workflow are separate conditional layers. Never load by default:

- V0.3.31 or Legacy 11 modules;
- Peace Star or other tests/benchmarks;
- QA, semantic-audit samples, approval/commit/seal/release state;
- Python, JSON Schema, reports, generated outputs, or Adapter documentation;
- unused capabilities or genre packs.

If a route needs more than one dominant, one secondary, and two narrow modifiers, emit `ROUTE_ESCALATION_REQUIRED`; do not omit necessary ability and do not load everything.

## Generation Segment boundary

`Narrative Scene != Director Shot != Generation Segment`.

The current deterministic implementation uses one Shot per Segment as a safe fallback. It is not a universal rule. An execution strategy may later map N Shots to one Segment without changing Director IR. G11 audio-span and full multi-shot strategies remain open because real-video execution was skipped.

## Output

Default user-facing output is per Generation Segment:

- source Shot ID(s);
- duration;
- final Seedance prompt;
- necessary reference/model constraint;
- warning or degradation only when present.

Do not expose schema metadata, source anchors, internal beat IDs, validation evidence, migration data, QA verdicts, workflow state, Legacy modules, or long rule explanations by default.

## Evidence boundary

Structural evidence covers 14 generalization cases, 42 Shots, Generation Ready validation, deterministic prompt fidelity, routing isolation, and Legacy regression. It does not prove Seedance instruction following, video aesthetics, lip-sync, L/J-cut realization, or that one Shot per Segment is optimal. Never describe this candidate as `PRODUCTION_READY`.

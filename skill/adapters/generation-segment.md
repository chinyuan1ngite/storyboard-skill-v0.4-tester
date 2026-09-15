# Generation Segment Strategy Contract

Status: abstraction `FORMALIZED`; concrete multi-shot strategy `OPEN` / `BLOCKED_BY_REAL_VIDEO`.

## Separation

`Narrative Scene != Director Shot != Generation Segment`.

- Narrative Scene groups story time/place and connected state.
- Director Shot owns semantic framing, camera, action, audio, and continuity decisions.
- Generation Segment is a model execution window that references one or more ordered Director Shots.

Changing Segment grouping must not mutate Candidate IR or re-direct Shots.

## Strategy interface

Every Segment records:

- strategy ID;
- source Scene ID;
- ordered source Shot IDs;
- per-Shot duration allocation;
- cross-Shot audio event provenance;
- prompt hash;
- warning/degradation/manual-review state.

Allowed architecture:

- `1 Shot -> 1 Segment`;
- `N Shots -> 1 Segment` when a configured strategy can preserve every Shot meaning and timing.

`1 Shot -> N Segments` requires an explicit Director-authored internal timing allocation or manual review; the Adapter cannot invent one.

## Current fallback

The Candidate deterministic renderer implements `ONE_SHOT_FALLBACK`: one Shot per Segment when within the configured execution window. This is current implementation, not universal truth.

G11 `A_ONE_SHOT`, `B_AUDIO_SPAN`, and `C_FULL_MULTISHOT` prompts remain test-only experiment arms. Because real video was skipped, no strategy is selected as superior and no L/J-cut realization claim is allowed.

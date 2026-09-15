# Audio Transition Capability

Status: `FORMALIZED_PRODUCTION_CANDIDATE`; real-video audio realization is `BLOCKED_BY_REAL_VIDEO`.

Load only when speech or sound crosses a Shot boundary, starts before its source is shown, or remains after its source leaves frame.

- Bind each event to exact `shot_refs`, source/speaker, exact text when dialogue, and phase visibility.
- L-cut: picture leaves the source while the same sound continues; the receiver Shot must not show false synchronous mouth movement.
- J-cut: sound begins before the source appears; keep it off-screen until picture reveal.
- Preserve exact dialogue and intended cut point; do not paraphrase merely to fit Shots.
- Distinguish dialogue overlap from environmental bridges and off-screen effects.

This formalizes Director semantics only. It does not claim Seedance lip-sync, voice continuity, or actual L/J-cut execution.

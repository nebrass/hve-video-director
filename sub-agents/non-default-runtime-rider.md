# Non-default runtime — rider

> Ships **with the adapter excerpt** in frame-packet item 3, only when `runtime:` names a
> non-default runtime. Everything here is a **local narrowing constraint** on that excerpt
> (ADR-002 form 3) — the excerpt is written for a standalone composition, and you are building a
> sub-composition. Where the two differ, this wins; everything the excerpt says and this does not
> contradict still holds. Registered as `SUBCOMP_CLONE_SEMANTICS` in `compat/ecosystem.md`,
> because no upstream file owns the intersection these rules describe.

Your packet carries that runtime's **adapter excerpt** — follow it exactly, including its
registration and its seek contract, except where this rider narrows it.

**Never ship `<script type="module">`.** Your script is cloned out of its `<template>` and
re-executed in the host document, where a bare `import` throws and fails the `check` gate — and you
cannot see it, because it only appears once the film is assembled. The root imports the module and
publishes it; you consume it from a **classic** script:

    (window.__threeReady = window.__threeReady || []).push(function (THREE) { /* build here */ });

Split what defers from what does not: the paused GSAP timeline still registers **synchronously** at
the top level — the runtime's timeline gate depends on it — and only the runtime-specific build goes
inside the callback. If your packet names a non-default runtime and does not tell you which global
publishes it, stop and report that rather than importing one yourself.

**`hf-seek` carries the ROOT clock, not your local time**, and so does `window.__hfThreeTime`.
A scene mounted at 36s receives 36…44, not 0…8. Subtract your mount's `data-start` before using
it. Skip this and every root time past your duration clamps to your last frame: the scene renders
**frozen** for its whole beat — camera still, nothing travelling — while lint, runtime, motion and
contrast all pass, because a static WebGL plate is a perfectly valid frame. Read the offset from
the DOM rather than hard-coding it, so re-timing the scene in `index.html` needs no edit here, and
expect the **compiled** shape to differ from what you authored (the compiler rewrites the mount's
attributes and relabels your root) — walk ancestors for the mount carrying your composition id,
and fall back to 0 so the scene still works standalone.

Whatever the runtime, **GSAP stays the timeline owner**: every other runtime hangs off the one
paused timeline and renders from its seek, never from its own loop.

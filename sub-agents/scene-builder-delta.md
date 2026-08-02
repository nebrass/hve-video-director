# Scene builder — hve-video-director delta

> The shared frame-worker core contract is prepended above; read the two as one role. This file
> carries only what is specific to a scene in **this** pipeline, and where the two disagree **this
> file wins** — the overrides below are the complete list. A generic timeline, determinism, or
> font rule is not this file's business; it is already stated above.

## Overrides — four core conventions, re-pointed

| The core contract says | Here |
|---|---|
| write `compositions/frames/<frame_id>.html` | write the **exact scene path your packet names** (the frame's `src`, e.g. `scenes/03-feature.html`). One file. Nothing else. |
| composition id and timeline key are `frame_id` | the exact `data-composition-id` your packet names. The composition loader matches it byte for byte, and `window.__timelines["<that id>"]` uses the same string. |
| the design truth is `frame.md` | the **design spec inlined in your packet** (the project's `DESIGN.md`). Its don't-lift rule carries over unchanged: it is a style spec, never your on-screen copy. |
| caption keep-out — all content in the top ~83%, even when captions are off | **superseded in full** — see § Captions. This pipeline reserves no band, captions enabled or disabled. |

Root styling, the sub-composition wrapper, and the timeline registration you copy from the **scene
skeleton in your packet**, not from a convention you supply. Your packet is your whole world: it
already contains the design spec, so you open nothing outside it except the capture files it binds
by path.

`focal:` / `roles:` do not exist in this pipeline. The hero is whatever `goal:` says the viewer
must understand, carried by the bound capture when the packet binds one.

## The director keys are binding direction

Your frame block carries up to fourteen: `goal:` `abstraction:` `complexity:` `tone:` `energy:`
`density:` `camera:` `metaphor:` `blueprint:` `motion:` `capabilities:` `runtime:`
`runtime_rejected:` `user_directed:`. They are **direction, not suggestion** — each was derived
against the whole film's budgets and its emotional arc, so a frame that quietly ignores one
desynchronizes from neighbours you cannot see.

- `goal:` is the acceptance test. A viewer who misses it means the frame failed, however it looks.
- `tone:` + `energy:` set easing character and reveal rhythm — `calm` drifts, `build` tightens,
  `peak` punches, `resolve` settles.
- `density:` is a hard element count, not a mood. The packet states the count that applies to
  this frame; build to it exactly and reveal only in the disclosure order the frame gives.
- `camera:` and `metaphor:` are chosen vocabulary — implement the named move and the named concept,
  never a livelier substitute. `capabilities:` / `runtime:` were derived, not preferred, and
  `runtime_rejected:` records what was already ruled out; never revive it.
- `user_directed: true` means the user directed this frame explicitly, and outranks every default
  here.

Disagreeing with a key is legitimate; acting on the disagreement is not. Build as directed and
report the objection.

## Cited recipes arrive inlined — never name-guess a motion

`blueprint:` and every name in `motion:` reach you **with their bodies**: keep a blueprint's
signature move recognizable, reproduce each rule's mechanics. You resolve nothing — there is no
index and no recipes directory in your dispatch. A cited name whose body is missing from your
packet is a **build error you report**, never a motion you reconstruct from the spelling of its
name. Never invent a motion name, and never rename one.

## `runtime:` — the non-default runtimes

An absent `runtime:` means GSAP; build normally. When it names `three`, `html-in-canvas`, or any
other non-default runtime, your packet carries that runtime's **adapter excerpt** — follow it
exactly, including its registration and its seek contract. GSAP stays the timeline owner: every
other runtime hangs off the one paused timeline and renders from its seek, never from its own loop.

## Real captures are sacred

A bound capture — the `screenshot:` or `clip:` file your packet names by exact path — is the
**subject** of the frame, not texture.

- Frame it the way the design spec says: browser or device chrome, shadow, vignette, a grade toward
  the spec's tokens. Motion belongs to the non-timed wrapper around it, never to the `<img>` or
  `<video>` itself.
- **Never crop out product chrome** to tidy a composition. The window frame, the nav, the product's
  own header are what make the still identifiable as this product.
- **Never overlay text on a UI content region.** Put callouts in margins, gutters, or over inert
  surface — anywhere the product's own words are not.
- **Never replace a capture with an invented mock**, a redrawn UI, or a close-enough rebuild. A
  bound file that is missing or unreadable is a build error you report.

## Data honesty

Every number, metric, label, URL, command, and product string on screen comes **only** from values
your packet supplies. A number the packet does not give is a **build error you report** — never a
plausible figure, a rounded guess, a `10×`, or filler copy. The scene templates encode the same
rule in code: their stat constants start at `Number.NaN`, so shipping an invented number means
overwriting a guard that exists to stop exactly that. A wrong stat is a legal problem, not a design
problem.

## Captions — the overlay law

Captions are an overlay composited on top of the finished film, **not** a band reserved out of your
layout.

- Compose on the **true vertical centre**, `y = H / 2` (540 landscape, 960 portrait). A layout
  pushed high with an empty lower strip is the bug, not the fix.
- Content may run to the bottom edge — full-bleed captures, backgrounds, and rails are all welcome.
- One courtesy: keep *small critical readable text* (a URL line, a legal line) out of the bottom
  ~80px centre span where the caption line sits. Imagery and cards under it read fine.
- This holds identically whether your packet's captions flag is enabled or disabled.

## You do NOT decide

Narration text · this frame's `duration:` (fixed from real voice timing — build to land inside it)
· transitions between frames (the seam owns every exit; author one only if your packet says you are
the closing frame) · audio of any kind (no `<audio>` element, and a clip `<video>` stays `muted`) ·
design tokens · the storyboard (your packet is your copy of your block — never open or write the
shared file) · any frame but your own.

You run no CLI. Lint and check operate on the assembled project, which does not exist while you
build, so they would report on other files and come back falsely green. The orchestrator runs them
after assembly and re-dispatches you with a concrete finding if your frame fails; treat any finding
in your context as a hard constraint. Writing your one scene file is your terminal action.

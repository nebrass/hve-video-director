# Three.js Scene Taxonomy

Names the *scene categories, their capability tags, and their ingredients* for the moment a
frame's runtime selection lands on `three`. It teaches nothing about integration: `THREE_ADAPTER`
owns the entire contract (render from `hf-seek`, importmap version pinning, asset preload,
mandatory `data-duration`, mixer seeking, the determinism bans) and `HTML_IN_CANVAS` owns the
HTML-as-texture treatments and their environment caveats. Builders load those; this file only
decides *which kind of 3D scene this is, and whether it earns the runtime at all*.

Consumed by `reasoning/scene-analysis.md` (Q7, Q10) and by the selection procedure in
`reasoning/capability-catalog.md`, which owns and versions the capability-tag vocabulary.

## When Three.js is on the table at all

Never because someone asked for "3D". Only when the frame's derived capability set contains at
least one **Three-only tag**:

| Three-only tag | The need, stated as the viewer's experience |
|---|---|
| `perspective-camera` | the viewpoint itself travels through the space |
| `topology-3d` | the parts/structure relationship only reads in three dimensions |
| `volumetric-count` | the quantity *is* the message, past DOM instance budgets |
| `material-realism` | light, reflection, or surface finish carries meaning |
| `shader-surface` | the surface is computed per-pixel, not composed of elements |
| `cinematic-hero` | the beat's job is to feel monumental |

**And only when the user's ceiling permits it.** `visual_runtime: flat` in the Creative Brief
bars this runtime for the whole film. Test the tags anyway: a frame that derives a Three-only
tag under a flat ceiling takes the Tier-A move and records `runtime_rejected: three —
visual_runtime: flat`, exactly as the closing section requires. Barring the runtime is the
user's call; pretending the need never existed is nobody's, and it is what would leave them
unable to see what the setting cost them.

`spatial-depth` alone never justifies Three — the catalog serves 2.5D depth from GSAP, which is
cheaper, seek-native, and inside the house DON'T limits. The discriminator is **self-occlusion**:
content that must pass in front of *and* behind itself is Three; content that merely sits on
layers is DOM.

Three.js frames draw from the same hero budget as `HTML_IN_CANVAS` — doctrine origin there ("the
contrast between flat beats and canvas beats IS part of the visual storytelling"), enforced count
in the budget table of `reasoning/scene-analysis.md`. A video whose every scene is 3D has no hero.

## Scene categories

| Category | Capability tags | Ingredients & material register | Camera language | Grounding |
|---|---|---|---|---|
| **Objects** — product, device, logo as a real thing | `material-realism`, `spatial-depth` | GLTF or primitive-built mockup with authored clips, mixer-seeked; 3-point studio (hemisphere + key); roughness carries brand — matte = trust, gloss = consumer | Hero Orbit, Push In | `THREE_ADAPTER`; blueprint `device-surface-showcase`; block `vfx-iphone-device` via `REGISTRY_CATALOG` |
| **Fields** — scale, particles, data volume | `volumetric-count`, `spatial-depth` | instanced meshes whose positions are a pure function of (index, time) from a seeded PRNG; emissive points on dark, fog for depth cueing | static drift, Pull Out | `REGISTRY_VFX_TEMPLATE` (seeded PRNG for anything "random"; render on update, never rAF) |
| **Flows** — streams, throughput, token traffic | `perspective-camera`, `spatial-depth` | particles travelling authored curves, progress = f(time); additive blending, deliberately low count | Lock-On, Arc | **The most-rejected category.** If the path reads flat, it is `TECHNIQUES` #9 (GSAP MotionPathPlugin) in DOM and Three is a cost with no gain |
| **Spaces** — corridors, environments, establishing shots | `perspective-camera`, `cinematic-hero` | planes + exponential fog, sparse emissives, filmic tone mapping; the camera path *is* the content | 3D Flight (the signature shot), Multi-phase journey | `THREE_ADAPTER`; blueprint `camera-journey` is the Tier-A shape of the same idea |
| **Extrusion** — code/config becomes infrastructure | `topology-3d`, `material-realism` | 2D outlines extruded into solids with staged growth; flat-shaded, orthographic-feeling | Isometric, Crane | the code→matter entry in `grammar/metaphors.md` |
| **Assembly / Exploded** — parts ↔ whole | `topology-3d`, `spatial-depth` | grouped meshes, per-part transforms keyed to time; neutral studio, part colour = component identity | Exploded View → Assembly | `KEYFRAME_DISCIPLINE` — the subject must stay one legible identity across every pose |
| **Shader plates** — ambient hero backgrounds | `shader-surface` | one full-screen quad, time uniform; organic FBM / domain-warp noise — repeating geometric tiles read as cheap | static | `TECHNIQUES` #13 (WebGL Fragment Shader Art); shader hygiene per `TRANSITION_CATALOG` § Shader Transitions |
| **HTML-as-texture cinematics** — the real UI in 3D space | `cinematic-hero`, `material-realism` | live UI captured as a GPU texture, then bloom / portal / shatter / liquid | Hero Orbit, Reveal (masked) | `HTML_IN_CANVAS` owns this row entirely, fallback rule included; blocks `vfx-portal`, `vfx-shatter`, `vfx-liquid-background` via `REGISTRY_CATALOG` |

Camera-move names resolve in `grammar/camera.md`.

## Ingredient defaults (director-level; mechanism stays upstream)

- **Camera.** One perspective camera, 35–50° FOV — wider reads as an action cam, narrower
  flattens the depth you just paid for. One camera driver per scene; the single-writer rule is
  `grammar/camera.md` § Hard rules, the time→pose mechanism is `THREE_ADAPTER`, and
  `KEYFRAME_PATTERNS` carries the proxy pattern for driving a non-DOM camera off the timeline.
- **Lighting.** Start at hemisphere + one directional key. Add shadows only when contact
  grounding is the message. Keep brand colours in linear space so tone mapping does not shift them.
- **Materials.** Standard PBR by default; emissive reserved for UI-glow accents. Anything needing
  frame history (motion-blur trails, feedback buffers) is decided by `DETERMINISM_RULES` and
  `THREE_ADAPTER` § Avoid, not here — if the idea needs it, redesign the idea.
- **Surface reading.** `material-realism` says light carries meaning; it does not say *what the
  light does*, and that is a communication choice, not an implementation detail. Name one:

  | Reading | The viewer concludes | Use when |
  |---|---|---|
  | `travelling-band` | a manufactured object with real extent — the eye follows the light across it | a product hero, a device, anything whose *thingness* is the point |
  | `fixed-glint` | a screen or a pane — lit, but flat | the surface is a display showing something, and the content matters more than the object |
  | `matte-diffuse` | a material sample, not a product | texture or colour is the subject and a highlight would distract |

  State it on a `runtime: three` frame alongside the camera move; the packet carries it. The
  *mechanism* stays the builder's — the reading follows from surface curvature and lobe tightness
  together, and `THREE_ADAPTER` owns both. Naming it matters because the levers that look like
  highlight controls are not: intensity, roughness and cone angle change how *bright* and how
  *broad* a highlight is, while whether it reads as a band or a spot is decided by the geometry
  underneath. A frame that asked for `travelling-band` and got an ellipse is a miss the director
  can see and name; without the word, it is nobody's defect.
- **Transitions.** A Three scene enters and exits through the same 2D seam system as every other
  scene (opacity/transform on its clip wrapper). Never transition *inside* WebGL across a scene
  boundary — seams are `SEAM_LAW` and `seam-craft` territory.
- **Overlays.** HTML text and captions layer *above* the canvas on the same timeline. The canvas
  is one layer, not the composition.
- **Reuse before authoring.** Check `REGISTRY_CATALOG` first — a shipped VFX block spends less of
  the hero budget than a bespoke scene, and arrives already deterministic.

## The sub-composition tax — count it before selecting `three`

`THREE_ADAPTER` documents an ES-module import, and that is correct for a **standalone**
composition. Every scene here is a **sub-composition**: its `<script>` is cloned out of its
`<template>` and re-executed in the host document, where module semantics do not survive. A bare
`import` there throws `Cannot use import statement outside a module` and fails the `check` gate —
and none of it is visible while the scene is viewed alone. It appears only once Phase 4 assembles
the film, which is the worst place to find it.

So a `runtime: three` frame is never self-contained. It obliges the root composition to import the
module once and publish it on a global, and obliges the scene to consume that global from a classic
script. Phase 4 carries the root half; `sub-agents/scene-builder-delta.md` carries the scene half.
Count this when a frame competes for a hero beat: the capability is real, and so is the assembly it
drags in behind it.

## Rejecting Three.js — and recording it

Reject for a frame when any of these hold:

- the subject is flat UI that a screenshot or clip already carries honestly;
- the depth need is mockup-tilt subtle → `orbit-3d-entry`, `split-tilt-cards`;
- parts, paths, or layers read fine in 2.5D → `depth-scatter-assemble`, `3d-camera-flight`,
  `TECHNIQUES` #9 (GSAP MotionPathPlugin);
- the instance count fits DOM budgets — see the `density:` row and the budget table in
  `reasoning/scene-analysis.md`;
- the hero budget is better spent on a higher-story-leverage frame;
- the render-environment risk is not repaid by communication gain (confirm with `DOCTOR`).

Write the verdict into the frame as `runtime_rejected: three — <reason>` and name the Tier-A move
that took its place. A rejection with no recorded reason is indistinguishable from never having
considered 3D at all — which is the failure this taxonomy exists to prevent.

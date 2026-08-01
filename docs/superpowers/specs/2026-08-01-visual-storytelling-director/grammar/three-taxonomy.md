# Three.js Primitive Taxonomy

> **Proposed skill module** — target location after approval: `grammar/three-taxonomy.md`.
> Consumed by Phase 3 when a scene's capability analysis selects the `three` runtime.
> This taxonomy names *scene categories and their ingredients*; the integration contract
> (hf-seek, importmap, data-duration, preloading, determinism) belongs entirely to
> `../hyperframes-animation/adapters/three.md` and is never restated here. The heavier
> HTML-as-texture treatments belong to `../hyperframes-animation/adapters/html-in-canvas-patterns.md`.

## When Three.js is on the table at all

Never because the user asked for "3D". Only when scene analysis scores a hard need for one of:
**true depth** (content occludes itself), **perspective camera motion** (the viewpoint travels),
**volumetric quantity** (instance counts beyond DOM budgets), **material realism** (light/reflection
carries meaning), or **shader-driven surfaces**. Subtle dimensionality (tilts, parallax, translateZ
stacks) stays DOM/GSAP — cheaper, seek-native, and inside the house DON'T limits.

Budget: Three.js scenes draw from the same **1–3 hero beats per video** budget as html-in-canvas.
A video whose every scene is 3D has no hero.

## Scene categories

| Category | Ingredients | Camera language | Lighting/material register | Official grounding |
|---|---|---|---|---|
| **Objects** — product/device/logo as a real thing | GLTF model or primitive-built mockup; `AnimationMixer.setTime` for authored clips | Hero Orbit, Push In | 3-point studio: hemisphere + key; `MeshStandardMaterial`, roughness carries brand (matte=trust, gloss=consumer) | `adapters/three.md` AnimationMixer pattern; `blueprints/device-surface-showcase.md` (flagged heavy) |
| **Fields** — scale, particles, data volume | `InstancedMesh`; positions = pure function of (index, time) with seeded PRNG | static drift, Pull Out | emissive points on dark; fog for depth cueing | `adapters/three.md` "seeded data"; registry VFX rules (mulberry32, no rAF) |
| **Flows** — streams, throughput, token traffic | particles along `CatmullRomCurve3` paths; progress = f(time) | Lock-On, gentle Arc | additive blending, low count | curve travel = deterministic path seek |
| **Spaces** — corridors, environments, establishing shots | walls/planes + fog; camera path is the content | 3D Flight (THE hero shot) | `FogExp2` + sparse emissives; ACES tone mapping | camera as pure function of time (`adapters/three.md`) |
| **Extrusion** — code/config becomes infrastructure | `ExtrudeGeometry`/`Shape` from 2D outlines; staged growth | Isometric, Crane | flat-shaded, orthographic-feeling | code→matter metaphor (`grammar/metaphors.md`) |
| **Assembly/Exploded** — parts ↔ whole | grouped meshes, per-part transforms keyed to time | Exploded View → Assembly | neutral studio; part-color = component identity | mixer or keyframed groups; `../hyperframes-keyframes/` pose contracts |
| **Shader plates** — ambient hero backgrounds | full-screen quad + fragment shader, time uniform | static | FBM/domain-warp organic noise — repeating geometric tiles read as cheap | `techniques.md` #13; transitions doctrine bans tile grids |
| **HTML-as-texture cinematics** — the real UI in 3D space | `<canvas layoutsubtree>` → `drawElementImage` → texture; bloom/portal/shatter/liquid | Hero Orbit, Portal reveal | UnrealBloom sparingly; effects catalog | `adapters/html-in-canvas-patterns.md` (owns this entirely, incl. env caveats) |

## Ingredient defaults (director-level, still deferring implementation)

- **Camera:** one `PerspectiveCamera`, 35–50° FOV; position/target keyframed as pure functions of
  seek time (or via the GSAP-proxy pattern in `../hyperframes-keyframes/references/keyframe-patterns.md`).
  One camera driver per scene — the single-writer rule.
- **Lighting:** start hemisphere + one directional key. Shadows only when contact grounding is the
  message. sRGB output + ACES for filmic scenes (session-verified: linear-space emissive values
  for accurate brand colors under tone mapping).
- **Materials:** `MeshStandardMaterial` default; emissive for UI-glow accents; avoid
  history-dependent effects (motion-blur trails, feedback buffers) — banned by the adapter's
  determinism rules.
- **Transitions:** a Three scene enters/exits through the same 2D seam system as every scene
  (opacity/transform on its clip wrapper). Never transition *inside* WebGL across scene
  boundaries — seams are `motion-doctrine`/`seam-craft` territory.
- **Overlays:** HTML text/captions layer *above* the canvas, animated by GSAP on the same
  timeline; the canvas is one layer, not the composition.
- **Version/SRI:** pin one `three` version in importmap + bare imports alike (silent breakage
  otherwise — `adapters/three.md`); vendor or SRI-pin per repo supply-chain policy.

## Rejection checklist (record in the storyboard when Three.js is declined)

Reject Three.js for a scene when any of: the subject is flat UI (screenshot/clip carries it),
the depth need is ≤ mockup-tilt subtlety (DOM), the count fits DOM budgets (≤40 animated
elements), the hero budget is spent, or the render environment risk (WebGPU/GPU paths) is not
justified by communication gain. Record as `runtime_rejected: three — <reason>` in the frame's
storyboard bullets so reviewers see the reasoning.

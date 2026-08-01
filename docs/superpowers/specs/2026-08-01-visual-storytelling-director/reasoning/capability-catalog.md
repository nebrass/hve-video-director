# Runtime Capability Catalog & Selection Framework

> **Proposed skill module** — target location after approval: `reasoning/capability-catalog.md`.
> Consumed by Phase 1 (scene planning, stage 13–14 of the reasoning pipeline) and Phase 3
> (scene direction). The director reasons in **communication capabilities**, then maps to
> runtimes via this catalog. The official selection guidance in
> `../hyperframes-animation/SKILL.md` § "Picking a runtime" is the base truth; this file adds
> the capability→runtime mapping and the tie-breaking heuristics. Adapters own all integration
> contracts.

## Capability vocabulary (what a scene may need)

`timeline-choreography` · `text-choreography` · `ui-micro-motion` · `chart-animation` ·
`svg-line-work` · `spatial-depth` · `perspective-camera` · `topology-3d` · `volumetric-count` ·
`material-realism` · `shader-surface` · `gpu-compute` · `prebaked-asset` · `decorative-loop` ·
`identity-morph` · `physical-metaphor` · `cinematic-hero`

## The catalog

| Runtime | Capabilities served | Choose when (official guidance, condensed) | Costs / constraints | Adapter (owner) |
|---|---|---|---|---|
| **GSAP** | timeline-choreography, text-choreography, ui-micro-motion, chart-animation, svg-line-work, identity-morph (FLIP), 2.5D spatial-depth | **Default for 95% of motion work** — all rules/blueprints/transitions are GSAP-based | property allowlist; layout-tween ban; the master clock every other runtime hangs off | `adapters/gsap.md` + 3 sub-files |
| **Three.js** | spatial-depth (true), perspective-camera, topology-3d, volumetric-count, material-realism, shader-surface, cinematic-hero | "3D scenes, camera motion, shader-driven visuals" | `data-duration` mandatory (no inference); importmap version pinning; asset preload; hero budget 1–3 beats | `adapters/three.md` |
| **html-in-canvas** (+Three/WebGL) | cinematic-hero on REAL UI (bloom, shatter, portal, liquid, device-mapping) | "Most powerful visual capability" — hero product beats only | same hero budget; feature-detect + fallback; env caveats | `adapters/html-in-canvas-patterns.md` |
| **Lottie** | prebaked-asset (AE exports), vector mascots, logo/icon accents | "When an asset has its own pre-baked timeline" | local assets only; absolute-time seek (no runtime loop/speed) | `adapters/lottie.md` |
| **Anime.js** | ui-micro-motion (compact), imported-example ports | "Lightweight tweening when GSAP is overkill"; explicitly secondary to GSAP | registry discipline (`__hfAnime`) | `adapters/animejs.md` |
| **CSS keyframes** | decorative-loop (shimmer/glow/pulse/grain), zero-JS motifs | "Simple repeated motifs, decoration — no JS cost" | finite iterations or duration uninferable; **banned as idle/glitch inside GSAP-choreographed scenes** (wall-clock desync) | `adapters/css-animations.md` |
| **WAAPI** | data-generated keyframes without GSAP | "Native browser keyframes without a GSAP dependency" | document-time seek (clip offsets via delay); weakest diagnostics | `adapters/waapi.md` |
| **TypeGPU/WebGPU** | gpu-compute, shader-surface at scale (liquid glass, frosted, particle sims) | "GPU-rendered canvases (particles, liquid glass, custom shaders)" | env-gated (headless-shell can't do WebGPU+drawElementImage; Brave/Canary override); sync-registration rules | `adapters/typegpu.md` |
| **animate-text** (catalog) | text-choreography by NAME (24 effects) | Named-effect consistency across beats; layout-aware effects | external skill; GSAP fallback recipe | `adapters/animate-text.md` |
| **hyperframes-keyframes** (discipline) | identity-morph proof, pose contracts, motion verification | When a single subject's motion must be *proven* (`--shot`/`--ghost` diagnostics) | not a runtime — a verification layer over all of them | `../hyperframes-keyframes/SKILL.md` |
| **Mixed** | any combination | Officially first-class: every runtime registers on its global; HyperFrames seeks all in one pass | duration interplay: Three never infers — mixed comps need `data-duration` or a GSAP timeline | `SKILL.md` § coexistence |

## Selection procedure (per scene)

```
1. Take the frame's DERIVED capability set from scene analysis (ADR-005: the union of
   tags declared by its cited grammar entries + asset/subject realities + reasoned
   additions). This catalog owns and versions the tag vocabulary; grammar entries
   declare their tags as part of M1 (annotation task).
2. Candidate set = every runtime serving all derived capabilities.
3. Apply priors, in order:
   a. GSAP-first: if GSAP alone serves all REQUIRED → GSAP. Stop. (95% rule.)
   b. Real-product rule: a bound capture on screen biases against replacing it
      with invented visuals; html-in-canvas may ELEVATE it (hero budget permitting).
   c. Hero budget: three / html-in-canvas / typegpu candidates compete for the
      video's 1–3 hero beats. Highest story-leverage scene wins; others degrade
      to the DOM expression of the same idea (grammar/camera.md Tier A).
   d. Asset reality: prebaked vector asset exists → Lottie; no asset → never Lottie.
   e. Environment: typegpu only if the render environment supports it
      (npx hyperframes doctor); otherwise Three.js fallback or DOM.
   f. Determinism risk: if the effect needs frame-history (trails, feedback,
      stateful sims) → redesign; no runtime may violate seek determinism.
4. Record in the storyboard frame:
     runtime: <choice>            (omit when GSAP — it is the default)
     runtime_rejected: <name — reason>   (only when a non-default was considered)
5. Multi-runtime scenes: GSAP remains the timeline owner; other runtimes hang off
   it per the adapter's registration contract.
```

## Scoring heuristic (when candidates tie)

Score = (communication gain: 0–3) − (integration cost: 0–2) − (budget pressure: 0–2), where
communication gain asks "does the capability change what the viewer *understands*, or only how
it *looks*?" A looks-only gain caps at 1. Ties resolve to the cheaper runtime. This keeps the
framework future-proof: a new HyperFrames adapter enters the catalog as one table row + its
capability tags — the procedure never changes.

## Worked examples

- *"Show our API gateway routing requests to three services"* → REQUIRED: timeline-choreography,
  svg-line-work; topology is 2D → **GSAP + SVG** (`spatial-pan-stations`, `svg-path-draw`).
  Three.js rejected: no occlusion/perspective need — record it.
- *"Make the dashboard feel monumental for the finale"* → cinematic-hero on real UI →
  **html-in-canvas** 3D-rotation+bloom, spending hero beat #1; camera: Hero Orbit.
- *"Explain vector embeddings"* → volumetric-count + spatial-depth (clusters in space) →
  **Three.js** Fields category (seeded InstancedMesh), hero beat; degrade path: 2.5D
  `depth-scatter-assemble` if budget is spent.
- *"Animate our mascot waving"* → prebaked-asset → **Lottie** (AE export exists) else redesign
  to poses via `hyperframes-keyframes`.
- *"Subtle grain + shimmer on the title card"* → decorative-loop → **CSS keyframes** (finite),
  because no choreography relationship to the timeline exists.

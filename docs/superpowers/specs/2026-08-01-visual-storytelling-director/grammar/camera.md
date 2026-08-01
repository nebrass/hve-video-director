# Camera Grammar

> **Proposed skill module** — target location after approval: `grammar/camera.md` in the skill root.
> Consumed by Phase 1 (scene planning) and Phase 3 (scene direction). This file teaches
> *when and why* to use a camera move. It never teaches *how* — every move cites the official
> HyperFrames implementation owner, and scene builders load that owner, not this file.

## Doctrine

Camera is communication, not decoration. A camera move answers exactly one viewer question
(*where am I? what matters now? how do these relate? how big is this?*). If you cannot name
the question, the scene gets a static camera and earns its motion from content animation.

The user never asks for a camera move. The director infers camera language from each scene's
communication goal (see `reasoning/scene-analysis.md`) and records it in the storyboard frame's
`camera:` key. Builders receive it via their frame packet.

**Two implementation tiers — chosen by capability need, never by spectacle:**

| Tier | Mechanism | Cost | Budget | Implementation owner |
|---|---|---|---|---|
| **A — DOM camera** | GSAP transforms on a world wrapper (scale/x/y, ≤8° rotateY, ≤4° rotateZ) | near zero | default for all scenes | `../hyperframes-animation/rules/` (named per move below) |
| **B — true 3D camera** | Three.js `PerspectiveCamera` driven from seek time via `hf-seek` | high (importmap, preload, `data-duration` mandatory) | **1–3 hero beats per video** | `../hyperframes-animation/adapters/three.md` + `grammar/three-taxonomy.md` |

The 1–3 hero-beat budget is official doctrine, not taste: "1–3 hero beats per video, not every
beat — the contrast between flat GSAP beats and canvas beats IS part of the storytelling"
(`../hyperframes-animation/adapters/html-in-canvas-patterns.md`).

## The grammar

| Move | What it tells the viewer | Use when | Pacing effect | Tier | Official implementation |
|---|---|---|---|---|---|
| **Push In** | "This detail is the point." | Narrowing from context to a feature; rising intensity toward a claim | builds tension; pair with VO emphasis word | A | `rules/coordinate-target-zoom.md` |
| **Pull Out** | "Now see the whole system." | Payoff reveals; after a detail beat, show scale/context | release; breathes after density | A | `blueprints/zoom-out-workspace-reveal.md` |
| **Pan / Truck** | "These things sit side-by-side." | Sequential features sharing one space; comparison without a cut | steady, procedural; keeps one mental map | A | `blueprints/spatial-pan-stations.md` |
| **Tilt / Crane / Boom** | "There is a hierarchy here." | Vertical structure: stack diagrams, layered architectures, leaderboard | ceremonial when slow | A | y-translate on world wrapper + `rules/multi-phase-camera.md` |
| **Multi-phase journey** | "Follow this path through the product." | Guided tours; tutorial chapter transitions inside one space | sustained motion between rest points | A | `rules/multi-phase-camera.md`, `blueprints/camera-journey.md` |
| **Orbit / Hero Orbit** | "This object is real and has dimension." | Product hero moment, device mockup, logo lockup | slow = premium; never loop a full 360° | B (subtle A via `rules/orbit-3d-entry.md`) | `adapters/three.md` (camera position as pure function of time) |
| **Arc** | Softened lateral move — relation *plus* dimension | When a straight truck feels mechanical past ~2s | organic, calm | A | truck + slight rotateY within DON'T limits |
| **Rack Focus** | "Shift your attention — same space, new subject." | Two coexisting planes (UI + annotation; foreground/background) | instant redirection without spatial motion | A | `rules/depth-of-field-blur.md` |
| **Follow / Lock-On** | "Watch this element — it is the actor." | Cursor-driven demos, tutorial steps, tracked UI elements | procedural, intimate | A | `rules/camera-cursor-tracking.md`, `rules/ai-tracking-box.md` |
| **Reveal (masked)** | "Something was hidden; now it isn't." | Before/after, feature unveil, brand reveal | anticipation → payoff | A | technique #12 (clip-path static window) in `techniques.md`; never animate the clipPath itself between scenes |
| **Isometric** | "This is a system; here is its map." | Architecture diagrams, infra topologies, workflow overviews | neutral, explanatory | A (CSS 3D grid) or B (orthographic) | CSS `preserve-3d` stage per `rules/3d-camera-flight.md` hygiene notes; `three-taxonomy.md` § Diagram scenes |
| **Parallax** | "This space has depth." | Ambient depth under text beats; opening establishing shots | atmospheric, subconscious | A | `rules/depth-scatter-assemble.md`, `rules/3d-page-scroll.md` |
| **Macro** | "Look this close — the craft is real." | Type detail, micro-interaction, code character-level | intimate; short beats only | A | capture at 2× (retina screenshot), then scale ≤1.5; legibility math in `patterns/visual-patterns.md` budgets |
| **Exploded View** | "This whole is made of these parts." | Component decomposition: plugin systems, request lifecycles, stacks | analytic pause; hold ≥1s at full separation | A (translateZ layers) or B (GLTF) | `rules/depth-scatter-assemble.md` (reverse = explode); `three-taxonomy.md` § Assembly |
| **Assembly** | "These parts become this product." | Closing synthesis, logo lockups, feature recap | convergent, conclusive | A | `rules/depth-scatter-assemble.md`, `blueprints/logo-assemble-lockup.md` |
| **3D Flight** | "Travel through the space itself." | ONE signature establishing or closing shot | maximal; spends the hero budget | A+ (the only DOM rule that travels in Z) or B | `rules/3d-camera-flight.md`; true flight → `adapters/three.md` |

`rules/…`, `blueprints/…`, `techniques.md` = `../hyperframes-animation/…`.

## Hard rules (all inherited — cited, not restated)

1. **One camera, one writer.** All camera state lives in a single `cam` object applied by one
   `applyCamera()` — never parallel tweens on the same wrapper
   (`../hyperframes-animation/rules/3d-camera-flight.md`, `multi-phase-camera.md`).
2. **Seed at t=0.** Run the applier once at build time so frame 0 renders the authored pose
   (`rules/3d-camera-flight.md`).
3. **Perspective hygiene.** `perspective` on a static stage; `preserve-3d` on world + intermediate
   wrappers; any `filter`/`opacity<1`/`overflow` on a 3D wrapper collapses `translateZ`
   (`rules/3d-camera-flight.md`).
4. **No camera push under fixed overlays** (`../motion-graphics/categories/asset-fusion/module.md`).
5. **Seams own the handoff.** A camera move must end *still in motion* if the cut is a
   velocity-matched seam — exit vector, direction, and speed are ledger entries verified by
   `seam-gate.mjs` (`../motion-doctrine/SKILL.md`). Camera direction contributes to the film's
   Current: one dominant direction, reserved vectors carry meaning.
6. **Tier B contract is the three adapter's, verbatim:** render from `hf-seek`, preload assets,
   `data-duration` on the root, pinned renderer size/DPR (`adapters/three.md`). Never re-derive it.
7. **DON'T limits still bind Tier A:** no full 360° scene spins; mockup tilt ≤8° rotateY / ≤4°
   rotateZ; no 3D transforms inside inter-scene transitions.

## Pacing coupling

Camera speed is an emotional-pacing instrument (consumed from the storyboard's `energy:` key):

| Scene energy | Camera behavior | Typical duration |
|---|---|---|
| calm / trust | static or drift ≤4% scale change | whole scene |
| build / explain | one deliberate move, `power2.inOut` | 60–80% of scene |
| peak / reveal | fast push or flight, `power4`, then **stillness-before-climax hold 0.3–0.75s** | 0.3–0.8s move |
| resolve / CTA | settle to static; assembly convergence | ends ≥1s before scene end |

Stillness-before-climax and the ≥1s climax dwell are `../motion-doctrine/SKILL.md` law.

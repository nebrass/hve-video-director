# Runtime Capability Catalog

Stage 14 of the reasoning pipeline. Consumed by Phase 1 (scene planning) and re-checked in Phase 3,
whose frame packets carry the resolved keys to builders (M5). The director reasons in **communication capabilities**, never in
technology; this file is the only place capabilities become a runtime.

`RUNTIME_PICKER` (the `hyperframes-animation` skill) is the **base truth** for which runtime does
what. This catalog adds the capability→runtime mapping, the budgets, and the tie-break. It may
never contradict `RUNTIME_PICKER`; if the two disagree, upstream wins and this file is the bug.
Adapters own every integration contract — nothing here restates one.

## Vocabulary ownership (ADR-005)

**This file owns and versions the capability tag vocabulary.** Every `grammar/` entry declares
its tags from the list below and from nowhere else; `reasoning/scene-analysis.md` unions declared
tags and never invents one. That is what makes capability derivation mechanical rather than a
judgment call.

**Baseline capability.** Every scene implies `timeline-choreography` — a frame is a timeline and
its elements arrive on one clock. Grammar rows declare only what they add *beyond* it, so an empty
tag cell adds nothing rather than meaning "no capability". Stated here and nowhere else: no
grammar file's local convention is load-bearing, Q11's union starts from it, and no set is empty.

- **Vocabulary version: 1** (2026-08-01). Bump on any add, rename, or removal.
- **Adding a tag** requires three things: a communication need no existing tag covers; a
  **derivation path** — one of Q11's three sources: a grammar entry that declares it, a named
  asset/subject reality, or an explicit addition whose triggering condition is stated in its row
  below; and at least one runtime row that serves it. A tag no runtime serves is a design error,
  not a capability; a tag no source reaches is dead vocabulary.
- **Audited exceptions.** Two tags are declared by no grammar entry and are not orphans:
  `prebaked-asset` enters as an asset reality (Q11 source 2 names it verbatim), `decorative-loop`
  as an explicit addition (source 3) under the condition its row states. Both are served.
- **Renaming a tag** is a breaking change — every grammar entry declaring it changes in the same
  commit.

### The tags

| Tag | The frame needs it when… |
|---|---|
| `timeline-choreography` | **baseline — every scene has it**: elements arrive and act in a stated order on one clock |
| `text-choreography` | the words themselves are the motion — per-word or per-glyph treatment |
| `ui-micro-motion` | small interface reactions carry the beat: press, hover, toggle, cursor contact |
| `chart-animation` | a number or series must be *seen changing* — counters, bars, rings, scrub |
| `svg-line-work` | a vector stroke must draw itself, or a path must be traced |
| `spatial-depth` | content must read as layered in Z — occlusion, parallax, stacked planes |
| `perspective-camera` | the *viewpoint* travels and perspective changes as it moves |
| `topology-3d` | the arrangement of parts only reads correctly in three dimensions |
| `volumetric-count` | quantity itself is the message; instance counts exceed a DOM budget |
| `material-realism` | light, reflection, or surface finish carries meaning |
| `shader-surface` | a per-pixel treatment is the subject — noise field, warp, plasma, liquid |
| `gpu-compute` | a simulation is computed per frame at scale — particles, fluid, flocking |
| `prebaked-asset` | an exported timeline already exists and *is* the motion |
| `decorative-loop` | an ambient motif with no relationship to the timeline — shimmer, grain, pulse |
| `identity-morph` | one subject must stay the *same object* across a change of form or place |
| `physical-metaphor` | simulated physical behavior carries the idea — collision, weight, magnetism |
| `cinematic-hero` | this single beat must feel dimensionally different from the rest of the film |

## The catalog

| Runtime | Serves | Choose when | Costs / gates | Contract |
|---|---|---|---|---|
| **GSAP** *(default)* | `timeline-choreography`, `text-choreography`, `ui-micro-motion`, `chart-animation`, `svg-line-work`, `identity-morph` (FLIP), 2.5D `spatial-depth` | **95% of motion work.** Every rule, blueprint, and transition is GSAP-based | property allowlist; layout-tween ban; it is the master clock every other runtime hangs off | `GSAP_ADAPTER`, `EASING_AND_STAGGER` |
| **Three.js** | true `spatial-depth`, `perspective-camera`, `topology-3d`, `volumetric-count`, `material-realism`, `shader-surface`, `cinematic-hero` | 3D scenes, travelling camera, shader-driven visuals | spends a hero beat; `data-duration` mandatory (nothing is inferred); importmap pinning; asset preload | `THREE_ADAPTER`, `grammar/three-taxonomy.md` |
| **html-in-canvas** | `cinematic-hero` on the **real** UI — bloom, shatter, portal, liquid, device mapping | the most powerful visual capability; hero product beats only | spends a hero beat; environment-gated, needs a declared fallback | `HTML_IN_CANVAS` |
| **Lottie** | `prebaked-asset` — vector mascots, logo and icon accents | an asset already carries its own baked timeline | local assets only; absolute-time seek, no runtime loop or speed | `LOTTIE_ADAPTER` |
| **Anime.js** | compact `ui-micro-motion`, ported examples | lightweight tweening where GSAP is overkill — explicitly secondary to GSAP | its own instance-registry discipline | `ANIMEJS_ADAPTER` |
| **CSS keyframes** | `decorative-loop` | zero-JS repeated motifs with no choreographic relationship to the timeline | finite iterations only; **banned as idle motion inside a GSAP-choreographed scene** (wall-clock desync) | `CSS_ANIMATIONS_ADAPTER` |
| **WAAPI** | data-generated keyframes without GSAP | native browser keyframes when a GSAP dependency is unwanted | document-time seek; weakest diagnostics of any runtime — last resort | `WAAPI_ADAPTER` |
| **TypeGPU / WebGPU** | `gpu-compute`, `shader-surface` at scale | particle sims, liquid glass, custom WGSL | spends a hero beat; environment-gated — confirm with `DOCTOR` first, else fall back | `TYPEGPU_ADAPTER` |
| **animate-text** | `text-choreography` by named effect | named-effect consistency across beats | an **external skill that is not installed here** — named effect IDs resolve to nothing; direct the effect in plain motion vocabulary instead | `ANIMATE_TEXT` |
| **hyperframes-keyframes** | `identity-morph` *proof* | a single subject's motion must be **proven**, not asserted | not a runtime — a verification layer over whichever runtime is chosen | `KEYFRAME_DISCIPLINE`, `KEYFRAME_PATTERNS` |
| **Mixed** | any combination | first-class: every runtime registers on its own global and HyperFrames seeks all in one pass | GSAP stays the timeline owner; a mixed composition needs an explicit duration — Three infers none | `RUNTIME_PICKER` |

**Before hand-authoring anything on this table, check `REGISTRY_CATALOG` for a shipped block that
already does it.** A tested block beats a hand-built hero beat.

## Selection procedure (per frame)

```
1. Take the frame's DERIVED capability set from reasoning/scene-analysis.md Q11 — the baseline,
   plus tags declared by each grammar entry the frame cites, plus asset/subject realities, plus
   reasoned additions. Do not re-derive it here; do not add tags here.
2. Candidate set = every runtime serving ALL derived capabilities.
2b. Apply the user's `visual_runtime` ceiling from the Creative Brief. On `flat`, drop
   three, html-in-canvas and typegpu from the CANDIDATE SET — never from step 1. The tags
   stay derived; only the runtime is barred, so a frame that reached for one still records
   it (step 4) instead of looking like 3D was never warranted. `derived` removes nothing
   and permits nothing: it is the absence of a ceiling, not a request for a runtime.
3. Apply the priors, in order — the first that decides, decides:
   a. GSAP-first. If GSAP alone serves every derived capability → GSAP. Stop.
   b. Real product. A bound capture on screen biases against replacing it with invented
      visuals; html-in-canvas may ELEVATE the real capture instead of displacing it.
   c. Hero budget. three / html-in-canvas / typegpu candidates compete for the film's hero
      beats (see the budget table in reasoning/scene-analysis.md). Highest story leverage
      wins; the rest degrade to the Tier-A DOM expression of the same idea (grammar/camera.md).
   d. Asset reality. A prebaked vector timeline exists → Lottie. No asset → never Lottie.
   e. Environment. typegpu only if the render environment supports it — confirm with DOCTOR;
      otherwise Three.js, otherwise DOM.
   f. Determinism. An effect needing frame history (trails, feedback, stateful sims) is
      redesigned, never approved. No runtime may violate seek determinism.
4. Record on the frame:  runtime:            (omit entirely when GSAP — it is the default)
                         runtime_rejected:   (whenever a non-default was considered and lost)
                         When 2b did the barring, the reason is the ceiling and the frame
                         also carries user_directed: true — e.g.
                         runtime_rejected: three — visual_runtime: flat (topology-3d derived)
5. Multi-runtime frames: GSAP remains the timeline owner; every other runtime hangs off it per
   its adapter's registration contract.
```

Step 3e's environment probe is `DOCTOR`; step 3f is enforced by `DETERMINISM_RULES`; step 3c's
limit is the hero-beat row of the budget table in `reasoning/scene-analysis.md`.

## Tie-break — one rubric, at one decision

When two candidates survive step 3, and only then:

> **Score = communication gain (0–3) − integration cost (0–2) − budget pressure (0–2).**
> Communication gain asks *does this change what the viewer **understands**, or only how it
> **looks**?* A looks-only gain caps at **1** (ADR-008: comprehension outranks engagement).
> A tie resolves to the cheaper runtime. Record the loser in `runtime_rejected:`.

**A multi-score cascade is explicitly rejected** (ADR-005) and must not be reintroduced. Numeric
Communication/Visual/Capability/Runtime scores invented by an LLM are the same class of fabricated
metric the anti-slop law bans from the screen, and they *reduce* auditability: a number hides its
rationale, while a recorded rejection exposes it. Measured scores from a real evaluator enter
through the gate ladder, never here.

A new adapter enters as **one table row plus its capability tags**. The procedure never changes.

## Worked examples

| Ask | Derived | Verdict |
|---|---|---|
| "Show our API gateway routing to three services" | `timeline-choreography`, `svg-line-work` | **GSAP + SVG** — `spatial-pan-stations` with `svg-path-draw`. Topology is 2D: `runtime_rejected: three — no occlusion or perspective need` |
| "Make the dashboard feel monumental for the finale" | `cinematic-hero` on real UI | **html-in-canvas** (`HTML_IN_CANVAS`), camera Hero Orbit, spending hero beat #1 |
| "Explain vector embeddings" | `volumetric-count`, `spatial-depth` | **Three.js**, Fields category (`grammar/three-taxonomy.md`), one hero beat. Degrade path when the budget is spent: 2.5D `depth-scatter-assemble` |
| "Animate our mascot waving" | `prebaked-asset` | **Lottie** if the export exists; if not, redesign to authored poses and prove them with `hyperframes-keyframes` |
| "Grain and shimmer on the title card" | `decorative-loop` | **CSS keyframes**, finite iterations — the motif has no choreographic relationship to the timeline |

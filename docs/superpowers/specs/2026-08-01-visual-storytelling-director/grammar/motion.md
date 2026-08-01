# Motion Grammar

> **Proposed skill module** — target location after approval: `grammar/motion.md`.
> Consumed by Phase 1 (beat direction) and Phase 3 (scene direction). Like the camera grammar,
> this file maps motion *principles* to communication purposes and cites the official owner of
> every mechanism. Motion names are cited from official indexes, **never invented** — the rule
> `/general-video` states for plans applies here: "motion names come from those indexes."

## Doctrine

Every element gets a motion verb; "if you can't name the verb, the element is not yet designed"
(`../hyperframes-creative/references/beat-direction.md`). The director's job is choosing verbs
that serve the beat's communication goal; the builder's job is executing them from the official
recipe. The split is absolute: this grammar plans, `../hyperframes-animation/` implements.

## Principles → when to apply → official owner

| Principle | Communicates | Apply when | Official owner (implementation) |
|---|---|---|---|
| **Anticipation** | "Something is about to matter" | Before a reveal or stat punch; small counter-motion or hold | `rules/kinetic-beat-slam.md`, `rules/press-release-spring.md` |
| **Follow-through** | Physical credibility | After fast arrivals; settle, never dead-stop | baked spring ease ζ=1 (`adapters/gsap-easing-and-stagger.md`) — interactive spring libs are banned |
| **Easing discipline** | Brand register | Always. House default `power3.out`; "smooth beats bouncy"; ≤3 easing characters per film; overshoot is a *playful register*, never a default; no `bounce.out`/`elastic.out` | `adapters/gsap-easing-and-stagger.md`, `../motion-doctrine/SKILL.md` timing intents |
| **Emphasis** | "This word/number is the claim" | Per the budget table in `reasoning/scene-analysis.md` (single source) | `rules/css-marker-patterns.md`, `rules/asr-keyword-glow.md` |
| **Hierarchy (stagger)** | Reading order | Lists, grids, card sets; total stagger ≤0.5s (`items × stagger`) | `adapters/gsap-easing-and-stagger.md`; contract in `rules-index.md` |
| **Reveal** | New information | Entrances only — always `fromTo`, never `from` (0→0 no-op trap); reveal paced across the frame's *full duration* to VO — front-loading is the "PowerPoint slide" failure | `frame-worker-core.md` (hyperframes-core), `rules-index.md` contract |
| **Transformation / morph** | "A becomes B"; identity persists | Before/after, refactor stories, state changes; crossfade only when the intent IS replacement | `../hyperframes-keyframes/` (FLIP, MorphSVG, pose contracts) — load it whenever a single subject's motion must be *proven* |
| **Synchronization** | Trust; craft | **Audio is the clock**: word-timed kinetic type from transcript timestamps; beat-timed cuts from `audiomap`; VO regen re-opens every seam | `techniques.md` #4; `../motion-doctrine/SKILL.md`; timestamps from `../media-use/references/audio.md` |
| **Continuity** | One film, not a slideshow | Every seam: vector law (axis/direction/speed/phase), the Current (one dominant direction), a named carrier — "never a crossfade — it has no carrier at all" | `../motion-doctrine/SKILL.md` + `ledger.json` + `seam-stamp.mjs`/`seam-gate.mjs`; mechanics `../seam-craft/SKILL.md` |
| **Staging** | Focus | One focal per beat; density varies by scene role (`../hyperframes-creative/references/video-composition.md`) | `beat-direction.md` |
| **Progressive disclosure** | Comprehension pacing | Tutorials and dense diagrams; reveal follows the viewer's question order, not the DOM order | `frame-worker-core.md` pacing law; blueprint slot ordering |
| **Causal motion** | Agency; "the product did that" | UI demos: the click *ignites* the next beat, same frame | `../oversized-cursor/SKILL.md`; `rules/cursor-click-ripple.md`, `rules/control-target-sync.md` (single-driver rule) |
| **Sustained motion (anti-wobble)** | Aliveness without noise | Any beat >3s: pick one of the 5 official sustained-motion routes; idle jitter is banned | `../motion-doctrine/SKILL.md` routes; `rules/sine-wave-loop.md` constraints |
| **Stillness** | Weight | 0.3–0.75s before a climax; ≥1s dwell after a payoff | `../motion-doctrine/SKILL.md` |
| **Exit discipline** | Seam ownership | **Exits are banned except on the final scene — "The transition IS the exit"** | `transitions/overview.md` (hyperframes-animation) |

`rules/…`, `techniques.md`, `transitions/…`, `blueprints/…` = `../hyperframes-animation/…`.

## Vocabulary sources (cite by name in storyboards)

- **47 atomic rules** — `../hyperframes-animation/rules-index.md` (one-liners; text, data, camera,
  layout, SVG, ambient, transition families).
- **22 time-coded blueprints** — `../hyperframes-animation/blueprints-index.md` (role menu maps
  1:1 to storyboard frame types Hook/Problem/Product_Intro/Key_Feature/Benefits/Social_Proof/CTA/
  Brand_Outro). Posture: Reproduce / Adapt / Compose — a soft menu, story truth decides beats.
- **13 techniques** — `../hyperframes-animation/techniques.md` ("every composition should use at
  least 2–3").
- **24 named text effects** — `../hyperframes-animation/adapters/animate-text.md` (IDs usable in
  storyboards; GSAP fallback recipe if the external skill is absent).
- **Transition registry** — Tier-B machine-stampable set (crossfade, blur-crossfade, push-slide,
  zoom-through, squeeze) + ~40 CSS transitions + shader transitions. Budget: ONE primary
  (60–70% of cuts) + 1–2 accents; 2–3 types per film (`transitions/overview.md`,
  `TRANSITION-REGISTRY.md`).

## Determinism boundary (inherited, never restated in scene prompts)

The full seek-safety contract (paused registered timeline, `fromTo` law, property allowlist,
no wall-clock/randomness, layout-tween ban, finite repeats) is owned by
`../hyperframes-core/references/determinism-rules.md` and `../hyperframes-animation/rules-index.md`.
Scene builders load those; the director's storyboards must simply avoid *requesting* motion that
violates them (e.g. "continuous ambient shimmer" → name a sustained-motion route instead).

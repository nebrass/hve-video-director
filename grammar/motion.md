# Motion Grammar

Consumed by Phase 1 today (beat direction); Phase 3 becomes a reader in M5, when frame packets
carry the director keys to scene builders. This file maps motion
*principles* to communication purposes and names the official owner of every mechanism. It plans
**when and why**; the owning upstream recipe implements **how** (ADR-002 — never restate mechanism
text here). Motion names are cited, never invented: bare backticked names resolve through
`BLUEPRINT_INDEX` first, then `RULES_INDEX`; everything else upstream is cited by the capability
SYMBOL registered in `compat/ecosystem.md` (ADR-007).

## Doctrine

Every element gets a motion verb — if you cannot name the verb, the element is not yet designed
(`BEAT_DIRECTION`). Film-wide motion philosophy (easing is emotion, speed is weight,
build/breathe/resolve) is read once per project from `MOTION_PRINCIPLES`. The director chooses
verbs that serve the beat's communication goal; the builder executes them from the official
recipe. Comprehension outranks retention outranks engagement (ADR-008): a verb that looks better
but reads slower loses.

## Capability tags

The tag vocabulary is owned and versioned by `reasoning/capability-catalog.md`. A frame's
capability set is the **union** of the tags declared by every grammar entry it cites (ADR-005) —
mechanical, not a judgment call. `—` declares the empty set deliberately: the principle changes
what the frame *communicates* but not which runtime can serve it. A frame whose union is empty
resolves to the default runtime (GSAP) per the catalog's GSAP-first prior and `RUNTIME_PICKER`.

## Principles → when to apply → owner

| Principle | Communicates | Apply when (director's call) | Tags | Owner (mechanism) |
|---|---|---|---|---|
| **Anticipation** | "Something is about to matter" | Before a reveal or stat punch — small counter-motion, or a held beat | `timeline-choreography` | `kinetic-beat-slam`, `press-release-spring` |
| **Follow-through** | Physical credibility | After a fast arrival; settle, never dead-stop. Baked ease only — a physics solver is not seekable | `timeline-choreography` | `EASING_AND_STAGGER`; `DETERMINISM_RULES` for the ban |
| **Easing discipline** | Brand register | Always. Pick one register and hold it across the film; overshoot is a *playful* register, not a default | `timeline-choreography` | `EASING_AND_STAGGER`; `SEAM_LAW` § timing intents (house register + forbidden eases — read, never restate) |
| **Emphasis** | "This word/number is the claim" | On the one phrase the beat exists to land. Budget: `reasoning/scene-analysis.md` | `text-choreography` | `MARKER_PATTERNS`, `asr-keyword-glow` |
| **Hierarchy (stagger)** | Reading order | Lists, grids, card sets — the order *is* the argument. The group must still arrive as one beat | `timeline-choreography` | `EASING_AND_STAGGER`; stagger cap in the `RULES_INDEX` contract |
| **Reveal** | New information | Entrances. Pace the reveal across the frame's **full** duration against the VO — front-loading is the "PowerPoint slide" failure | `timeline-choreography` | `FRAME_WORKER_CORE`; `spring-pop-entrance`, `waterfall-entry` |
| **Transformation / morph** | "A becomes B", identity persists | Before/after, refactors, state changes. Crossfade only when the intent genuinely *is* replacement | `identity-morph`, `timeline-choreography` | `KEYFRAME_DISCIPLINE` (load it whenever a subject's motion must be *proven*), `KEYFRAME_PATTERNS`; `card-morph-anchor`, `scale-swap-transition`, `theme-crossfade-morph` |
| **Synchronization** | Trust; craft | **Audio is the clock.** Word-timed type from real transcript timestamps — never eyeballed. Regenerating the VO re-opens every seam | `text-choreography`, `timeline-choreography` | `TECHNIQUES` #4 Per-Word Kinetic Typography; timestamps from `TRANSCRIBE`; optional beat-matched motion via `AUDIO_REACTIVE` |
| **Continuity** | One film, not a slideshow | Every seam: the vector law (axis/direction/speed/phase), one dominant current, and a **named carrier** — a crossfade carries nothing | `timeline-choreography` | `SEAM_LAW` (governs); `CUT_CATALOG` (the five velocity-matched seams + parameters); `SEAM_STAMP` → `SEAM_VERIFIER`; render side `SEAM_RENDER_MECHANICS` |
| **Staging** | Focus | One focal point per beat; information density follows the scene's role, not the design system's | `—` | `BEAT_DIRECTION`; `VIDEO_COMPOSITION`; `density:` values in `reasoning/scene-analysis.md` |
| **Progressive disclosure** | Comprehension pacing | Tutorials and dense diagrams — reveal in the viewer's question order, not DOM order | `timeline-choreography` | `FRAME_WORKER_CORE` pacing law; slot ordering per `BLUEPRINT_INDEX` |
| **Causal motion** | Agency — "the product did that" | UI demos: the click *ignites* the next beat in the same frame; one driver per coupled pair | `ui-micro-motion`, `timeline-choreography` | `CURSOR_TECHNIQUE`; `cursor-click-ripple`, `control-target-sync`; `SEAM_LAW` § causal motion |
| **Sustained motion** | Aliveness without noise | Any beat still running after its entry lands. Name one route in the plan: `staged reveals` · `camera with intent` · `sequenced UI life` · `animated sequences` · `cursor-led action`. Idle wobble is banned — a scene with nothing left to do is a planning bug, not a shimmer opportunity | `timeline-choreography` | `SEAM_LAW` § sustained-motion routes; `sine-wave-loop` constraints. `decorative-loop` is **not** a legal way to satisfy this inside a choreographed scene |
| **Stillness** | Weight | A held pause between the action and its result; a dwell after the payoff. Duration owned upstream | `—` | `SEAM_LAW` § stillness before climax |
| **Exit discipline** | Seam ownership | **No exits except on the closing scene — the transition IS the exit** | `—` | `TRANSITION_OVERVIEW` (states the ban and its final-scene exception); `SEAM_LAW` |

## Vocabulary sources

Storyboards name motion from these registries and nowhere else. Counts are deliberately not
quoted here — read them from the index, which is the thing upstream maintains.

| Source | What you get | How to cite it |
|---|---|---|
| `RULES_INDEX` | Atomic motion recipes — text, data, camera, layout, SVG, ambient, transition families. Compose 2–4 per scene | bare backticked name, no directory, no `.md` |
| `BLUEPRINT_INDEX` | Time-coded whole-frame shapes; its role menu maps 1:1 to the storyboard frame types. Posture: Reproduce / Adapt / Compose — a soft menu, story truth decides the beats | bare backticked id |
| `TECHNIQUES` | Numbered visual techniques; upstream expects 2–3 per composition | number **+** title, e.g. `TECHNIQUES` #4 Per-Word Kinetic Typography |
| `ANIMATE_TEXT` | A **pointer**, not a catalog — the named text-effect IDs live in an external skill that is *not installed here*. Treat every named ID as unavailable until `npx skills add pixel-point/animate-text` runs; until then direct the effect in plain motion vocabulary | symbol only |
| `TRANSITION_OVERVIEW` | Selection guidance — energy/mood, narrative position, presets — **and** the numbered hard rules that carry the exit ban | symbol only |
| `TRANSITION_REGISTRY` | The machine-stampable Tier-B subset (**not** the full catalog) | symbol only |
| `TRANSITION_CATALOG` | The normative page — hard rules, scene template, shader rules | symbol only |

Transition budget (one primary + accents, types per film) is a budget number: it lives only in
`reasoning/scene-analysis.md`. `SEAM_LAW` supersedes transition guidance wherever they disagree.

**Namespace guardrail.** `MG_MOTION_VOCABULARY` is the `motion-graphics` skill's *own*
primitive→GSAP vocabulary for its Director/Builder pair. It is deliberately excluded, not awaiting
adoption. Our motion names come from `RULES_INDEX` / `BLUEPRINT_INDEX` / `TECHNIQUES`; never mix
the two namespaces.

## Determinism boundary

The seek-safety contract is owned by `DETERMINISM_RULES` and the `RULES_INDEX` contract. It is
inherited, never restated in a scene prompt. The director's duty is narrower: do not *request*
motion that cannot be deterministic. Two recurring rewrites —

- "continuous ambient shimmer / it should feel alive" → name a sustained-motion route instead.
- "random sparkles / organic drift" → ask for index-seeded, finite motion, or drop it.

If a beat genuinely needs frame-history (trails, feedback, stateful sims), redesign the beat. No
runtime is allowed to buy it back.

## Budgets

Density, emphasis, marker, hero-beat and transition budgets are single-sourced in
`reasoning/scene-analysis.md` (ADR-008). No number from that table is repeated here or in any
scene prompt — cite the table.

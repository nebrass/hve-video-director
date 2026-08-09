# Camera Grammar

Consumed by Phase 1 (frame planning, the `camera:` key) and by Phase 3, which carries the
director keys to scene builders inside each frame packet (M5). The keys are build input, not
just planning record. This file
teaches **when and why** the camera moves. It never teaches how — every move names the upstream
owner of its mechanism and the builder loads that owner, not this file (ADR-002). Bare names are
rules/blueprints and SYMBOLS are capabilities; both resolve through `compat/ecosystem.md`.

## Doctrine

Camera is communication, not decoration. A move answers exactly one viewer question — *where am
I? what matters now? how do these relate? how big is this?* If you cannot name the question, the
frame gets `camera: static` and earns its motion from content animation instead.

The user never asks for a camera move. The director infers it from the frame's communication goal
(`reasoning/scene-analysis.md`, Q8) and records it as the frame's `camera:` key; builders receive
it in their frame packet.

### Two tiers — chosen by capability need, never by spectacle

| Tier | Mechanism | Cost | Budget |
|---|---|---|---|
| **A — DOM camera** | GSAP transforms on one world wrapper (scale / x / y; ≤8° `rotateY`, ≤4° `rotateX`, ≤4° `rotateZ`) | ~zero | the default for every frame |
| **B — true 3D camera** | Three.js perspective camera posed from seek time | high — importmap pinning, asset preload, mandatory `data-duration` | spends a hero beat; see the budget table in `reasoning/scene-analysis.md` |

Tier B's integration contract belongs entirely to THREE_ADAPTER, and `grammar/three-taxonomy.md`
names the scene categories; neither is restated here. The hero budget is ecosystem doctrine — the
contrast between flat beats and canvas beats *is* the storytelling (HTML_IN_CANVAS) — and its
number lives only in the budget table in `reasoning/scene-analysis.md`.

## Capability tagging (ADR-005)

Stage 13 unions the `capabilities` cell of every grammar entry a frame cites. A move's cell
declares only what that move **adds** beyond the baseline capability every scene implies, and `—`
means it adds nothing; that baseline rule is owned and stated once by
`reasoning/capability-catalog.md`, and this line only cites it. Three further rules keep the union
mechanical rather than a judgment call:

1. **Tag what the viewer must understand, not what the code does.** A `rotateY` that merely
   softens a lateral move is not `spatial-depth`; a layered stack whose *meaning* is the layering
   is.
2. **A Tier-A row never declares a Three-only tag** — `perspective-camera`, `topology-3d`,
   `volumetric-count`, `material-realism`, `shader-surface`, `cinematic-hero`. One such tag on a
   DOM row would force Three.js onto every frame that cites the cheap expression of the idea.
3. **Conditional tags key off an authoring fact, never taste.** "If parts travel in Z" is
   checkable; "if it feels dimensional" is not.

The tag vocabulary is owned and versioned by `reasoning/capability-catalog.md`. Never invent a tag.

## The vocabulary is closed by the Key column

**The Key column of the table below gives the exact literal a storyboard writes.** Copy it
verbatim; never derive it from the Move name, which is a display name and does not match. `static`
is the one legal value with no row — the frame that answers no viewer question earns its motion
from content instead (see Doctrine).

**A `-3d` suffix in the `camera:` value requests the Tier-B branch.** Four moves span both tiers
and spell both literals: `orbit` / `orbit-3d`, `isometric` / `isometric-3d`, `exploded` /
`exploded-3d`, `flight` / `flight-3d`. An unsuffixed value always derives the Tier-A branch; the
suffixed form is a *request* for a hero beat, which stage 14 may deny — a denied frame re-derives
as its A branch. Without the suffix, `camera:` would not tell stage 13 which branch to union, and
the derivation would stop being mechanical.

## The grammar

| Move | Key | Tells the viewer | Use when | Pacing effect | Tier | Adds (`capabilities`) | Mechanism owner |
|---|---|---|---|---|---|---|---|
| **Push In** | push-in | "This detail is the point." | narrowing from context to a feature; intensity rising into a claim | builds tension; land it on the VO emphasis word | A | — | `coordinate-target-zoom` (off-centre target), `viewport-change` (whole world) |
| **Pull Out** | pull-out | "Now see the whole system." | payoff reveal; scale or context after a detail beat | release; breathes after density | A | — | `zoom-out-workspace-reveal`, `viewport-change` |
| **Pan / Truck** | pan | "These things sit side by side." | sequential features sharing one space; comparison without a cut | steady, procedural; keeps one mental map | A | — | `spatial-pan-stations`, `viewport-change` |
| **Tilt / Crane** | tilt | "There is a hierarchy here." | vertical structure — stacks, layered architecture, leaderboards | ceremonial when slow | A | — | `viewport-change` (y leg), `multi-phase-camera` |
| **Multi-phase journey** | multi-phase | "Follow this path through the product." | guided tours; chapter changes inside one continuous space | sustained motion between rest points | A | — | `multi-phase-camera`, `camera-journey` |
| **Orbit / Hero Orbit** | orbit · orbit-3d | "This object is real and has dimension." | product hero moment, device mockup, logo lockup, icon ring | slow reads premium; never loop a full 360° | A subtle · B hero | A: `spatial-depth` · B adds `perspective-camera`, `material-realism` | A: `orbit-3d-entry` · B: THREE_ADAPTER (pose as a pure function of time), `grammar/three-taxonomy.md` |
| **Arc** | arc | relation *plus* a hint of dimension | a straight truck reads mechanical past ~2s | organic, calm | A | — | `viewport-change` with `rotateY` inside the DON'T limits |
| **Rack Focus** | rack-focus | "Same space — now look at the other plane." | two coexisting planes (UI + annotation, foreground/background) | instant redirection with no spatial travel | A | `spatial-depth` | `depth-of-field-blur` |
| **Follow / Lock-On** | follow | "Watch this element — it is the actor." | cursor-led demos, tutorial steps, tracked UI elements | procedural, intimate | A | `ui-micro-motion` | `camera-cursor-tracking`, `ai-tracking-box`, CURSOR_TECHNIQUE |
| **Reveal (masked)** | reveal | "Something was hidden; now it isn't." | before/after, feature unveil, brand reveal | anticipation → payoff | A | — | TECHNIQUES #12 *Clip-Path Reveal Masks* — a static window only; never tween a clipPath across a seam |
| **Isometric** | isometric · isometric-3d | "This is a system; here is its map." | architecture diagrams, infra topology, workflow overviews | neutral, explanatory | A · B for true occlusion | A: `spatial-depth` · B adds `topology-3d`, `perspective-camera` | A: TECHNIQUES #3 *CSS 3D Transforms*, stage hygiene per `3d-camera-flight` · B: `grammar/three-taxonomy.md` |
| **Parallax** | parallax | "This space has depth." | ambient depth under a text beat; establishing shots | atmospheric, subconscious | A | `spatial-depth` | `depth-scatter-assemble`, `3d-page-scroll` |
| **Macro** | macro | "Look this close — the craft is real." | type detail, micro-interaction, character-level code | intimate; short beats only | A | — | capture at 2× then scale ≤1.5 via `viewport-change`; legibility floor in `patterns/visual-patterns.md` |
| **Exploded View** | exploded · exploded-3d | "This whole is made of these parts." | component decomposition — plugin systems, request lifecycles, stacks | analytic; hold at full separation | A · B for real parts | A: `spatial-depth` · B adds `material-realism` | `depth-scatter-assemble` (reversed = explode), `center-outward-expansion` · B: `grammar/three-taxonomy.md` |
| **Assembly** | assembly | "These parts become this product." | closing synthesis, logo lockups, feature recap | convergent, conclusive | A | **`spatial-depth` only if parts arrive from Z** | `depth-scatter-assemble`, `logo-assemble-lockup` |
| **3D Flight** | flight · flight-3d | "Travel through the space itself." | ONE signature establishing or closing shot | maximal; Tier B spends a hero beat | A+ · B | A: `spatial-depth` · B adds `perspective-camera`, `cinematic-hero` | A: `3d-camera-flight` (the only DOM rule that travels in Z), `motion-blur-streak` · B: THREE_ADAPTER, `camera-journey` sub-shape B |

## Hard rules — all inherited, cited not restated

1. **One camera, one writer.** All camera state lives in a single state object applied by one
   applier; never run parallel tweens against the same wrapper (`3d-camera-flight`,
   `multi-phase-camera`, `viewport-change`).
2. **Seed at t=0.** Run the applier once at build time so frame 0 renders the authored pose
   (`3d-camera-flight`; the seek contract is DETERMINISM_RULES).
3. **Perspective hygiene.** `perspective` on a static stage, `preserve-3d` on the world and every
   intermediate wrapper; any `filter`, `opacity < 1`, or `overflow` on a 3D wrapper collapses
   `translateZ` (`3d-camera-flight`).
4. **Never push the camera under a fixed overlay** (MG_ASSET_FUSION).
5. **Seams own the handoff.** If the cut is a velocity-matched seam, the move must still be in
   motion at the boundary — exit vector, direction and speed are ledger entries (SEAM_LAW; the
   named carriers and their parameters are CUT_CATALOG; SEAM_VERIFIER checks them). Camera
   direction feeds the film's Current: one dominant direction, reserved vectors carry meaning.
6. **Tier B's integration contract belongs entirely to THREE_ADAPTER** — load it and follow it
   there. This file deliberately does not enumerate its terms: a local copy is a second author of
   record (ADR-002), and a copy that drifts is worse than a pointer.
7. **The repo DON'Ts still bind Tier A** (`SKILL.md` § DON'Ts): no 360° scene spins; mockup tilt
   ≤8° `rotateY` / ≤4° `rotateX` / ≤4° `rotateZ`; no 3D transforms inside an inter-scene
   transition; no camera tween that animates a layout property.

   **All three axes are capped, and the asymmetry is deliberate.** `rotateY` yaws a card the way a
   product is turned toward you, so it takes the widest angle. `rotateX` pitches it away, which
   foreshortens type *vertically* and costs legibility exactly where a screenshot's own words are —
   comprehension outranks looks (ADR-008), so it is capped with `rotateZ`, not with `rotateY`.
   `rotateZ` rolls the horizon, which reads as a mistake before it reads as style. A brand may
   narrow any of them further; nothing may widen them. **State the axis whenever you state a
   limit** — an unqualified "tilt ≤3°" leaves a builder to pick which rotation it governs.

## Pacing coupling

Camera speed is an emotional-pacing instrument, read from the frame's `energy:` key:

| `energy:` | Camera behavior | Share of the frame |
|---|---|---|
| calm / trust | static, or a drift small enough to read as stillness | whole frame |
| build / explain | ONE deliberate move with a clear start pose and rest pose | most of it — pace the move across the full duration; front-loading is the PowerPoint failure (FRAME_WORKER_CORE) |
| peak / reveal | one fast push or flight, preceded by the stillness-before-climax pause (SEAM_LAW owns its duration) | a short burst |
| resolve / CTA | settle to static; assembly converges and the frame holds | ends before the frame does |

Ease families are not chosen here. Take the register from the tone table in
`reasoning/scene-analysis.md`, resolved through EASING_AND_STAGGER.

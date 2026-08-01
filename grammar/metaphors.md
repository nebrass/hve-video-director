# Visual Metaphor Library

Maps a *concept* to the *picture that explains it*. Read in Phase 1 (visual semantics) and Phase 3
(scene direction). Goal is comprehension, not novelty. When a concept has a literal product
surface — a real screenshot or clip — **the real product beats any metaphor**; metaphors serve the
invisible: architecture, flow, scale, time, risk.

Every row names WHEN and WHY. The named upstream recipe owns HOW — never re-derive its mechanism
here.

**Columns.** **Concept** · **Metaphor** (what to draw) · **Requires** (capability tags, ADR-005) ·
**Camera** (a move from `grammar/camera.md`) · **Motion** (the upstream recipe that is the DOM
floor) · **Why**.

**Requires** lists only what a row adds *beyond* `timeline-choreography`, which every row implies;
`—` means it adds nothing. Tags are the vocabulary owned and versioned by
`reasoning/capability-catalog.md` — use those spellings, never invent one. A frame's capability set
is the **union** of the tags of every grammar entry it cites; that union is the input to runtime
selection, which happens in the catalog, not here.

**Motion cells name the Tier-A (DOM) expression only.** Elevating a row to true 3D, GPU, or
html-in-canvas is a separate decision that spends a hero beat — the tags say what elevation would
buy, `grammar/camera.md` owns the tier ladder, `reasoning/capability-catalog.md` makes the call.

## AI / LLMs / agents

| Concept | Metaphor | Requires | Camera | Motion | Why |
|---|---|---|---|---|---|
| LLM inference | prompt → typing → generative cascade | text-choreography, ui-micro-motion | Follow | `prompt-type-submit-generate` | mirrors the interaction users know |
| Agent working | progress theater — steps light up, artifacts land | ui-micro-motion | Multi-phase journey | `agent-progress-theater` | invisible work becomes observable |
| Multi-agent orchestration | constellation hub; spokes ignite around a center | svg-line-work | Pull Out | `constellation-hub` | hub-and-spoke = delegation topology |
| Context window / memory | vessel fills; transcript condenses as it scrolls | chart-animation | Push In | `transcript-scroll-artifact-reveal`, `stat-bars-and-fills` | capacity is spatial |
| Token stream | discrete particles travelling between surfaces | spatial-depth, volumetric-count | Follow / Lock-On | `TECHNIQUES` #9 GSAP MotionPathPlugin, `particle-burst` | things-moving reads as throughput |
| Model quality / eval | count-up + bars, real numbers only | chart-animation | static | `dataviz-countup`, `counting-dynamic-scale` | the number *is* the claim |
| MCP / tool use | ports dock into a hub; plug meets socket | identity-morph | Exploded View → Assembly | `card-morph-anchor`, `logo-assemble-lockup` | a protocol is a connection standard |

## Software architecture / APIs / distributed systems

| Concept | Metaphor | Requires | Camera | Motion | Why |
|---|---|---|---|---|---|
| Layered architecture | exploded stack of planes | spatial-depth | Exploded View → Tilt | `depth-scatter-assemble` | layers are literally layers |
| Request lifecycle | a pulse travels a path through stations | svg-line-work | Pan / Truck | `TECHNIQUES` #9 GSAP MotionPathPlugin, `spatial-pan-stations` | journey = sequence + latency |
| API contract | two panels; typed shapes cross the gap | ui-micro-motion | Rack Focus | `control-target-sync` (one driver) | request/response is a handshake |
| Microservices | city-block grid; one cell lights per call | ui-micro-motion | Isometric | `grid-card-assemble` | independent-but-cooperating units |
| Scale / load | instances multiply; density grows | spatial-depth, volumetric-count | Pull Out | `depth-scatter-assemble`, `grid-card-assemble`; DOM count cap per `particle-burst` | quantity is the message |
| Failure / resilience | one cell dims; traffic reroutes around it | svg-line-work | Lock-On on the failure | `svg-path-draw` (path re-draw) | the rerouting is the story |
| Networking / topology | node-edge graph; edges draw on | svg-line-work | Isometric / Pull Out | `avatar-cloud-network`, `svg-path-draw` | graphs are the native notation |
| Kubernetes / orchestration | pods as scheduler cells; reconcile loop pulses | chart-animation | Isometric + Push In on one pod | `grid-card-assemble`, `stat-bars-and-fills` | a control loop is a visible pulse |

## Data / databases / pipelines

| Concept | Metaphor | Requires | Camera | Motion | Why |
|---|---|---|---|---|---|
| Query | rows crystallize out of a structured field | ui-micro-motion | Push In | `grid-card-assemble` (live-populating board), `waterfall-entry` | selection out of bulk |
| Pipeline / ETL | material transforms across stations | — | Pan / Truck | `spatial-pan-stations` | the assembly line is canonical |
| Streaming | continuous ribbon beside discrete batches | — | static split | `comparison-split` | contrast carries the concept |
| Metrics / observability | dashboard assembles; needles settle on real values | chart-animation | Assembly | `dataviz-countup`, `chart-scrub-readout`; numerals per `TYPOGRAPHY` | the dashboard is the product surface |

## Security / DevOps / cloud

| Concept | Metaphor | Requires | Camera | Motion | Why |
|---|---|---|---|---|---|
| Threat / vulnerability | a probe traces edges until one gap glows | svg-line-work | Lock-On | `svg-path-draw`, `ai-tracking-box` | attack paths are paths |
| Encryption / secrets | content scrambles into cipherglyphs (seeded) | text-choreography | Macro | `hacker-flip-3d`; harsher alt `chromatic-glitch` | legible→illegible needs no narration |
| CI/CD | conveyor of commits through gates; a red gate halts it | ui-micro-motion | Pan / Truck | `spatial-pan-stations` | gates are quality checkpoints |
| Infra as code | a text file extrudes into isometric infrastructure | spatial-depth, physical-metaphor | Isometric, Crane | `depth-scatter-assemble` | code→matter is the whole pitch |
| Cloud regions | glowing points on a dark map; arcs between them | svg-line-work | Orbit (partial) | maps-category block via `MG_CATALOG_MAP` | geography is literal |

## Product / business / education

| Concept | Metaphor | Requires | Camera | Motion | Why |
|---|---|---|---|---|---|
| Product hero | the REAL product, framed, with subtle dimension | cinematic-hero, spatial-depth | Hero Orbit / Push In | `device-surface-showcase` (heavy — budget it) | authenticity is the moat |
| Before / after | split screen; the divider sweeps | — | static | `comparison-split` | direct contrast |
| Pain / overwhelm | notifications crowd inward around the center | — | Push In (claustrophobic) | `overwhelm-surround` | felt, not narrated |
| Growth / traction | count-up + rising bars from real data | chart-animation | static → small Pull Out | `dataviz-countup`, `counting-dynamic-scale` | the readout is the data |
| Timeline / roadmap | horizontal path of stations; the camera travels | — | Pan / Truck, Multi-phase journey | `spatial-pan-stations`, `camera-journey` | time reads as distance |
| Comparison / pricing | cards assemble; the winner scales forward | spatial-depth | Rack Focus | `grid-card-assemble`, `split-tilt-cards` | spatial prominence = recommendation |
| Workflow / how-to | numbered stations complete in order; artifacts persist | ui-micro-motion | Multi-phase journey | `fixed-anchor-cycle`, `spatial-pan-stations` | persistence shows accumulation |
| CTA | one anchor morphs into the action; the press ignites | identity-morph | settle to static | `cta-morph-press` | one action, zero competition |
| Brand close | parts assemble into the lockup | identity-morph | Assembly | `logo-assemble-lockup` | synthesis reads as closure |

## Scientific / quantitative

| Concept | Metaphor | Requires | Camera | Motion | Why |
|---|---|---|---|---|---|
| 3D structure (molecule, mesh, model) | a real object, slowly orbited | topology-3d, perspective-camera, material-realism | Orbit | `orbit-3d-entry` | genuinely spatial content earns depth |
| Field / simulation | a dense seeded particle or shader field | volumetric-count, shader-surface, gpu-compute | static / drift | `particle-burst` (count-capped) | only elevation affords the count |
| Distribution / uncertainty | an area chart morphs as a parameter moves | chart-animation | static | `chart-scrub-readout` | scrubbing the parameter *is* the explanation |

## Selection rules

1. **Real product first.** If the beat has a bound capture, the metaphor budget is zero — frame
   the real thing. Metaphors are for beats about invisible structure.
2. **One metaphor per concept per video.** Re-use it when the concept returns; consistency
   compounds comprehension.
3. **Screenshot test.** Pause any frame — would a stranger name the concept? If not, simplify
   (`patterns/anti-slop.md`).
4. **Tags are inputs, not verdicts.** Citing a row contributes its tags to the frame's capability
   set. Runtime selection consumes that set in `reasoning/capability-catalog.md`; never name a
   runtime in a storyboard on the strength of this table alone.
5. **The Motion cell is the floor, not the ceiling.** Every row is shippable in Tier A. Elevation
   competes for the video's hero beats — decided once, per video, not per row.
6. **Never decorate invented numbers.** A data metaphor without real data is cut, not filled
   (`patterns/anti-slop.md` P0).
7. **Reuse before authoring.** Check `REGISTRY_CATALOG` for a shipped block (including the VFX
   blocks) and `MG_CATALOG_MAP` for a category block before hand-authoring a metaphor scene.
8. **Word emphasis inside a metaphor is `MARKER_PATTERNS`** — never a bare marker rule name.
9. **Budgets live elsewhere.** Density, emphasis, marker, hero-beat and transition numbers are
   single-sourced in `reasoning/scene-analysis.md`. Cite that table; never restate a number here.

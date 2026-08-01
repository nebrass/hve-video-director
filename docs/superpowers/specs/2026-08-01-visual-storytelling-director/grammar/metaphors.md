# Visual Metaphor Library

> **Proposed skill module** — target location after approval: `grammar/metaphors.md`.
> Consumed by Phase 1 (visual semantics stage). Maps *concepts* to *visual metaphors* with a
> preferred runtime, camera language, and motion language — each grounded in an official
> HyperFrames vocabulary item so the builder implements from the owning recipe, never from
> this table. Goal: maximize understanding, not novelty. When a concept has a literal product
> surface (a real screenshot/clip), **the real product beats any metaphor** — metaphors are for
> the invisible (architecture, flows, scale, time, risk).

Columns: **Metaphor** (what to draw) · **Runtime** (from `reasoning/capability-catalog.md`) ·
**Camera** (from `grammar/camera.md`) · **Motion** (official vocabulary item) · **Why it works**.

## AI / LLMs / agents

| Concept | Metaphor | Runtime | Camera | Motion | Why |
|---|---|---|---|---|---|
| LLM inference | prompt → typing → generative cascade | GSAP | Follow | `blueprints/prompt-type-submit-generate.md` | mirrors the interaction users know |
| Agent working | progress theater: steps lighting up with artifacts | GSAP | Multi-phase journey | `blueprints/agent-progress-theater.md` | renders invisible work as observable steps |
| Multi-agent orchestration | constellation hub: spokes ignite around a center | GSAP/SVG | Pull Out | `blueprints/constellation-hub.md` | hub-and-spoke = delegation topology |
| Context window / memory | filling vessel; scrolling transcript that condenses | GSAP | Push In | `blueprints/transcript-scroll-artifact-reveal.md` | capacity is spatial |
| Token stream | particle stream between surfaces | Three.js (seeded particles) or GSAP | Lock-On | seeded particle field, `three-taxonomy.md` § Flows | discrete-things-moving reads as throughput |
| Model quality/eval | count-up + bar race with real numbers only | GSAP | static | `blueprints/dataviz-countup.md`; anti-slop: no invented metrics | numbers are the claim — never decorate fake ones |
| MCP / tool use | ports docking into a hub; plug gains a socket | GSAP/SVG | Exploded → Assembly | `rules/card-morph-anchor.md`, `logo-assemble-lockup.md` | protocol = physical connection standard |

## Software architecture / APIs / distributed systems

| Concept | Metaphor | Runtime | Camera | Motion | Why |
|---|---|---|---|---|---|
| Layered architecture | exploded stack of planes | GSAP (translateZ) or Three.js if a hero beat | Exploded View → Tilt | `rules/depth-scatter-assemble.md` | layers are literally layers |
| Request lifecycle | pulse traveling a path through stations | GSAP + SVG | Pan (stations) | `techniques.md` #9 MotionPath; `blueprints/spatial-pan-stations.md` | journey = sequence + latency |
| API contract | two panels; typed shapes crossing the gap | GSAP | static, Rack Focus | `rules/control-target-sync.md` (single driver) | request/response is a handshake |
| Microservices | city-block grid of cells, one lights per call | GSAP | Isometric | `blueprints/grid-card-assemble.md` | independent-but-cooperating units |
| Scale / load | multiplying instances; density growth | Three.js InstancedMesh (hero) or GSAP grid | Pull Out | `three-taxonomy.md` § Fields; ≤40 particles rule in DOM | quantity is the message — GPU when count is |
| Failure / resilience | one cell dims, traffic reroutes around it | GSAP + SVG paths | Lock-On on the failure | path re-draw, `rules/svg-path-draw.md` | rerouting is the story |
| Networking / topology | node-edge graph, edges draw on | SVG + GSAP | Isometric / Pull Out | `rules/avatar-cloud-network.md`, `svg-path-draw.md` | graphs are the native notation |
| Kubernetes / orchestration | pods as cells in a scheduler grid; reconcile loop as heartbeat | GSAP | Isometric + Push In on one pod | `grid-card-assemble.md` + `rules/stat-bars-and-fills.md` | control loop = periodic visible pulse |

## Data / databases / pipelines

| Concept | Metaphor | Runtime | Camera | Motion | Why |
|---|---|---|---|---|---|
| Query | beam scanning a structured field, rows crystallize | GSAP | Push In | `rules/dynamic-content-sequencing.md` | selection from bulk |
| Pipeline / ETL | material transforming across stations | GSAP | Truck | `spatial-pan-stations.md` | assembly line is the canonical metaphor |
| Streaming | continuous ribbon vs discrete batches side-by-side | GSAP | static split | `blueprints/comparison-split.md` | contrast carries the concept |
| Metrics / observability | live dashboard assembling; needles settle on real values | GSAP | Assembly | `dataviz-countup.md`, `chart-scrub-readout.md`; tabular-nums law | dashboards are the product surface |

## Security / DevOps / cloud

| Concept | Metaphor | Runtime | Camera | Motion | Why |
|---|---|---|---|---|---|
| Threat / vulnerability | red probe tracing edges until one gap glows | SVG + GSAP | Lock-On | `svg-path-draw.md` + `rules/ai-tracking-box.md` | attack paths are paths |
| Encryption / secrets | content scrambles to cipherglyphs (seeded) | GSAP | Macro | `rules/chromatic-glitch.md` constraints (quantized-time hash) | legible→illegible is instant comprehension |
| CI/CD | conveyor of commits passing gates; red gate halts line | GSAP | Truck | `spatial-pan-stations.md` + causal ignition | gates = quality checkpoints |
| Infra as code | text file extrudes into isometric infrastructure | Three.js (one hero beat) or CSS 3D | Isometric, Crane | `three-taxonomy.md` § Extrusion | code→matter is the whole pitch |
| Cloud regions | glowing points on a dark globe/map, arcs between | Three.js (hero) or `motion-graphics` maps category | Orbit (partial) | maps category (`../motion-graphics/catalog-map.md`) | geography is literal |

## Product / business / education

| Concept | Metaphor | Runtime | Camera | Motion | Why |
|---|---|---|---|---|---|
| Product hero | the REAL product, framed, subtle dimension | capture + GSAP; Three.js/html-in-canvas for ONE hero beat | Hero Orbit / Push In | `blueprints/device-surface-showcase.md` (flagged heavy — budget it) | authenticity is the moat; spine doctrine |
| Before/after | split screen; divider sweeps | GSAP | static | `comparison-split.md` | direct contrast |
| Pain / overwhelm | crowding notifications surround center | GSAP | Push In (claustrophobic) | `blueprints/overwhelm-surround.md` | felt, not narrated (anti-slop: don't narrate pain) |
| Growth / traction | count-up + rising bars from real data | GSAP | static → small Pull Out | `dataviz-countup.md`; no overshoot on counters | "the readout is data" |
| Timeline / roadmap | horizontal path with stations; camera travels | GSAP | Truck / journey | `camera-journey.md` | time = distance |
| Comparison / pricing | cards assemble, winner scales forward | GSAP | Rack Focus | `grid-card-assemble.md`, `split-tilt-cards.md` | spatial prominence = recommendation |
| Workflow / how-to | numbered stations completed in sequence, artifacts persist | GSAP | Multi-phase journey | `fixed-anchor-cycle.md` or stations | persistent artifacts show accumulation |
| CTA | single anchor morphs to action; press ignites | GSAP | settle to static | `blueprints/cta-morph-press.md` | one action, zero competition |
| Brand close | parts assemble into lockup | GSAP | Assembly | `logo-assemble-lockup.md` | synthesis = closure |

## Scientific / quantitative

| Concept | Metaphor | Runtime | Camera | Motion | Why |
|---|---|---|---|---|---|
| 3D structure (molecule, model, mesh) | true 3D object, slow orbit | Three.js (GLTF + `AnimationMixer.setTime`) | Orbit | `three-taxonomy.md` § Objects | genuinely spatial content earns Tier B |
| Field / simulation | GPU particle or shader field, seeded | TypeGPU (env-gated) or Three.js | static / drift | `adapters/typegpu.md` contract | only runtime that can afford the count |
| Distribution / uncertainty | area chart morphs as parameters change | SVG + GSAP | static | `chart-scrub-readout.md` | scrubbing a parameter is the explanation |

## Selection rules

1. **Real product first.** If the beat has a bound capture, the metaphor budget is zero — frame
   the real thing (capture-coverage gate). Metaphors serve beats *about invisible structure*.
2. **One metaphor per video for the same concept.** Re-use it when the concept returns —
   consistency compounds comprehension (design-system thinking applied to semantics).
3. **The metaphor must survive the screenshot test** (`patterns/anti-slop.md`): pause any frame —
   would a stranger name the concept? If not, simplify.
4. **Runtime column is a prior, not a verdict** — final runtime selection runs through
   `reasoning/capability-catalog.md` scoring, which weighs the whole video's hero-beat budget.
5. **Never decorate invented numbers.** Data metaphors require real data or the beat is cut
   (anti-slop P0; enforced by NaN guards in stat templates).

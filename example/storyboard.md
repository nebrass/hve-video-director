---
format: 1920x1080
duration: 60s
message: It does not render what you describe — it decides how the idea should be shown, then picks the tool that serves it.
arc: Hook → Pain → Turn → Mechanism → Delegation → Proof → Capabilities → CTA
audience: General developer audience — devs who have never written an agent skill
content_mode: promo
theme: dark
renderer: HyperFrames
product_surface: none
emotional_journey: frustration → relief → confidence
capture_plan: none — skip Phase 2
---

## Frame 1 — Every AI video looks like AI made it

- status: outline
- src: scenes/00-hook.html
- duration: 5s
- scene: The accusation, in type. No product yet.
- voiceover: "You can always tell when a video was made by an AI."
- goal: viewer recognises the problem as one they have seen, before any product appears
- abstraction: symbolic
- complexity: atomic
- tone: frustration
- energy: build
- density: focal
- camera: static
- metaphor: none — connective tissue
- blueprint: kinetic-type-beats
- motion: kinetic-beat-slam
- capabilities: text-choreography
- screenshot: none — connective tissue

The line lands one clause at a time. Nothing moves but the words: a frame that answers no viewer
question earns its motion from content, not from the camera.

## Frame 2 — The reason why

- status: outline
- src: scenes/01-pain.html
- duration: 8s
- transition_in: crossfade
- transition_speed: medium
- scene: Scattered fragments — a timeline, a renderer, an easing curve, a codec flag — closing in.
- voiceover: "Because making one by hand means learning a renderer, a timeline model, and an animation library before you get a single frame."
- goal: viewer feels the cost of doing this manually, rather than being told it
- abstraction: metaphor
- complexity: compound
- tone: tension
- energy: build
- density: dense
- camera: push-in
- metaphor: Pain / overwhelm
- blueprint: overwhelm-surround
- motion: center-outward-expansion
- capabilities: —
- screenshot: none — connective tissue

Fragments crowd inward as the push-in tightens. Felt, never narrated: the VO names the work, the
frame supplies the pressure.

## Frame 3 — It does not render. It directs.

- status: outline
- src: scenes/02-turn.html
- duration: 6s
- transition_in: zoom-through
- transition_speed: medium
- scene: The pivot line, alone on the canvas.
- voiceover: "This one is different. It decides how the idea should be shown."
- goal: viewer understands the category claim — a director, not a renderer
- abstraction: symbolic
- complexity: atomic
- tone: curiosity
- energy: peak
- density: focal
- camera: static
- metaphor: none — connective tissue
- motion: gradient-text-sweep
- capabilities: text-choreography
- screenshot: none — connective tissue

The pressure of Frame 2 releases into stillness. Held 0.4s before the sweep — the pause is the
turn.

## Frame 4 — Twelve questions per scene

- status: outline
- src: scenes/03-reasoning.html
- duration: 9s
- transition_in: crossfade
- transition_speed: medium
- scene: Questions resolve one by one into a plan — goal, tone, camera, metaphor, runtime.
- voiceover: "For every scene it asks what you must understand, how it should feel, and what it would take to show it."
- goal: viewer sees that the decision is explicit and auditable, not a black box
- abstraction: analog
- complexity: systemic
- tone: curiosity
- energy: build
- density: composed
- camera: multi-phase
- metaphor: Agent working
- blueprint: agent-progress-theater
- motion: card-morph-anchor
- capabilities: ui-micro-motion
- screenshot: none — connective tissue

Progressive disclosure: each answer settles before the next asks. Systemic idea, so the reveal is
paced across the full duration rather than front-loaded.

## Frame 5 — Then it delegates

- status: outline
- src: scenes/04-stack.html
- duration: 8s
- transition_in: zoom-through
- transition_speed: medium
- scene: The director on top; the rendering ecosystem separating out beneath it.
- voiceover: "It owns the thinking. Everything that draws a pixel belongs to HyperFrames."
- goal: viewer understands the division of labour — reasoning here, rendering there
- abstraction: metaphor
- complexity: compound
- tone: relief
- energy: build
- density: composed
- camera: exploded
- metaphor: Layered architecture
- blueprint: grid-card-assemble
- motion: depth-scatter-assemble
- capabilities: spatial-depth
- runtime_rejected: three — `spatial-depth` alone is served by GSAP's 2.5D layering. Real occlusion would cost a hero beat and add nothing the viewer must understand here.
- screenshot: none — connective tissue

Layers separate along Z far enough to read as distinct planes, then hold at full separation. The
depth is the argument; it does not need real 3D to make it.

## Frame 6 — The proof

- status: outline
- src: scenes/05-hero.html
- duration: 8s
- transition_in: zoom-through
- transition_speed: medium
- scene: The finished film as a real object in space, turning slowly under a key light.
- voiceover: "This video was planned, built and rendered by the skill it is describing."
- goal: viewer believes the claim because the artifact is in front of them with weight and dimension
- abstraction: metaphor
- complexity: atomic
- tone: relief
- energy: peak
- density: focal
- camera: orbit-3d
- metaphor: Product hero
- motion: —
- capabilities: spatial-depth, cinematic-hero, perspective-camera, material-realism
- runtime: three
- runtime_rejected: html-in-canvas — it elevates a real captured surface, and `product_surface: none` means there is none to elevate.
- screenshot: none — connective tissue

The film's one hero beat. Slow orbit, never a full revolution; the surface catches the key light so
the object reads as manufactured rather than drawn. Stillness of 0.5s before the light lands.

## Frame 7 — What it delegates to

- status: outline
- src: scenes/06-capabilities.html
- duration: 9s
- transition_in: crossfade
- transition_speed: medium
- scene: Three stations passing the frame — motion, seams, audio — each already owned upstream.
- voiceover: "Motion, transitions, narration and music are all the ecosystem's. It inherits every improvement without changing a line."
- goal: viewer understands the skill gets better without being updated
- abstraction: analog
- complexity: compound
- tone: confidence
- energy: calm
- density: composed
- camera: pan
- metaphor: Pipeline / ETL
- blueprint: spatial-pan-stations
- motion: card-morph-anchor
- capabilities: —
- screenshot: none — connective tissue

A steady truck past three stations keeps one mental map. Calm after the peak — the film breathes
before the ask.

## Frame 8 — Run it on yours

- status: outline
- src: scenes/07-cta.html
- duration: 7s
- transition_in: zoom-through
- transition_speed: medium
- scene: The install command resolving into a single anchor. Nothing else on screen.
- voiceover: "Install it, and point it at something you built."
- goal: viewer knows the exact command and has no competing action
- abstraction: symbolic
- complexity: atomic
- tone: confidence
- energy: resolve
- density: focal
- camera: static
- metaphor: CTA
- blueprint: cta-morph-press
- motion: card-morph-anchor
- capabilities: identity-morph
- screenshot: none — connective tissue

The closing frame — the only frame permitted an exit. The full command stays legible on screen for
its whole duration; one action, no competing links.

---

## Video-level budget check (Phase 1 Step 1.4c)

| Budget | Verdict |
|---|---|
| Hero beats (three / html-in-canvas / typegpu) | **1 of the allowed maximum** — Frame 6 only. Frame 5 considered and degraded to Tier A. |
| Transition types | 2 — `crossfade` primary (4 of 7 seams), `zoom-through` accent (2). Within one-primary-plus-accents. |
| Emphasis devices | 1 per scene; no marker-highlight used anywhere in the film. |
| Duration variance | 5 / 8 / 6 / 9 / 8 / 8 / 9 / 7 — varied; no flat profile. |
| Emotional arc closure | frustration → tension → curiosity → curiosity → relief → relief → confidence → confidence. Traces the Phase-0 journey. |
| Metaphor consistency | Each concept appears once; no concept re-drawn a second way. |

## Creative Brief levers still unconfirmed

`theme`, `aspect_ratio`, `identity_strategy` / `identity_choice`, `voice`, `transition_style`,
`transition_speed`, `music_strategy` — Phase 1 Steps 1.1–1.3 and 1.5 ask these. They are user-owned
and were not inferred (ADR-001). None of them changes the capability derivation above.

# Product Context — hve-video-director

## Product
- **Name:** hve-video-director
- **URL:** https://github.com/nebrass/hve-video-director
- **One-liner:** An agent skill that directs a video — it reasons about how to communicate an idea, then orchestrates the HyperFrames ecosystem to render it.
- **Tech stack:** Agent Skill (markdown prompt content) + pure-stdlib Python helpers; renders through HyperFrames (HTML + GSAP + headless Chromium), with Three.js / Lottie / WAAPI / TypeGPU reachable as runtimes.

## Audience
- **Who:** General developer audience — devs who have never written an agent skill.
- **Pain points:**
  - AI-generated video looks AI-generated: flat cards, uniform durations, stock easing.
  - Building one by hand means learning a renderer, a timeline model and an animation library before the first frame.
  - Existing tools render what you describe; none of them *decide* how the idea should be shown.
- **Desired action:** Install it and run `/hve-video-director` on their own project.
- **Emotional journey:** frustration → relief → confidence

## Brand
- **Colors:** Stripe design system, dark theme — deep navy canvas, blue-tinted elevation shadows, restrained accent.
- **Typography:** Stripe's light-weight display type; generous tracking at display sizes.
- **Tone:** Plain, technical, unhyped. Show the machinery; never claim a number.
- **Visual style:** Premium fintech restraint — depth via shadow and surface, not ornament.

## Video Concept
- **Type:** promo
- **Angle:** *"It thinks before it renders."* The differentiator is not that it makes videos — it is that it decides how an idea should be communicated, then picks the tool that serves it.
- **Duration:** 60s
- **Theme:** dark
- **Voice:** Daniel (ElevenLabs) — authoritative male, broadcast register

## Features to Highlight
1. **The reasoning layer** — a question set per scene produces an auditable plan: goal, tone, camera, metaphor, capabilities, runtime. It is the part no other tool has.
2. **Capability-driven runtime selection** — a scene declares what it must *communicate*; the runtime follows. The viewer never asks for 3D, and the film never spends 3D it did not need.
3. **HyperFrames-first delegation** — rendering, motion, seams and audio belong to the ecosystem, so the skill inherits every upstream improvement for free.
4. **Governance** — per-phase approval; the user owns every creative lever; nothing is inferred. It is why the output is *yours*.

## Constraints
- **Product surface:** `none` — the subject is a skill, not a UI. Abstract film; waives the Phase-3 capture-coverage gate.
- No invented metrics, no claimed adoption numbers (`patterns/anti-slop.md` P0).
- Dark canvas is authoritative: `stripe` supports light or dark, so nothing is adapted away.

---

*Phase 0 output. Every Creative Brief lever in `project-plan.md` was chosen by the user and
confirmed at story revision 1; none was inferred from this document (ADR-001).*

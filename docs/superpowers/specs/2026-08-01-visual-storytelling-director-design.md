# hve-video-director → Visual Storytelling Director — Design Review & Redesign Spec

**Date:** 2026-08-01 · **Status:** IMPLEMENTED — M0 → M6 landed on `refactor/hyperframes-first-m0-m1`
(PR #34), then validated by a real end-to-end Phase 0–5 production run on 2026-08-02.
**Scope:** full review of the skill (SKILL.md 492 ln, workflows 3,122 ln, patterns ~1,400 ln,
templates ~750 ln, design-systems 928 ln, scripts ~4,780 ln, tests 2,699 ln) against the
complete official HyperFrames ecosystem freshly locked in `.agents/skills/` (25 skills).
**Companion artifacts** (implementation-ready, same directory `2026-08-01-visual-storytelling-director/`):
`grammar/camera.md`, `grammar/motion.md`, `grammar/metaphors.md`, `grammar/three-taxonomy.md`,
`reasoning/capability-catalog.md`, `reasoning/scene-analysis.md`, `prompts/skill-rewrite.md`,
`adr.md` (ADR-001…008; 002/005 replaced, 001/007 amended per review), and
`review-principal.md` (final pre-implementation architecture review — APPROVED WITH CHANGES,
all mandatory changes applied).

---

## 1. Executive summary

hve-video-director is a well-engineered pipeline whose **governance layer is world-class and
whose knowledge layer is obsolete**. Its consent model, fingerprint/stamp gate chain, capture
determinism machinery, and docs-as-contract tests have no equivalent anywhere in the HyperFrames
ecosystem. But 70–85% of its phase-workflow content is a hand-maintained shadow copy of the
HyperFrames manual — and the ecosystem has since shipped official owners for nearly all of it:
`BRIEF.md`/`STORYBOARD.md`/`SCRIPT.md` formats, a production loop, a review loop, parallel
frame-worker dispatch, a unified `check` gate (deprecating the `lint|inspect|validate` chain
this skill still requires), a numeric seam gate, a media OS (TTS/BGM/SFX/captions/grading), a
97-block registry, and runtime adapters for Three.js/GSAP/Anime.js/WAAPI/Lottie/CSS/TypeGPU.
Several local pointers already dead-end into the pre-split skill layout.

**The redesign is therefore a re-basing, not a feature addition.** The mission's "add Three.js"
is a one-row consequence of the real change:

1. **Delegate every mechanical capability** to its official owner (the delegation map in §14).
2. **Adopt the official artifact formats and loops** where they exist, keeping this skill's
   governance as a *delta* on them, not a parallel universe.
3. **Add the missing director brain** — the layer neither this repo nor the ecosystem has:
   per-scene communication analysis, capability-driven runtime selection, camera/motion
   grammars, a metaphor library, and emotional pacing that is mechanically consequential.
4. **Keep the moats**: authenticated/native/terminal capture, tutorial mode, vendored brand
   design systems, the consent-first brief, reviewed-caption delivery.

Result: workflow prose shrinks ~45% while the reasoning share rises from ~25% to ~70%; every
future HyperFrames improvement (new adapter, new blocks, better gates) flows in with **zero
changes** to this skill; and Three.js/WebGPU/Lottie scenes appear automatically whenever a
scene's communication needs score for them — never because a user asked for "3D".

---

## 2. Current architecture review

**Shape.** `SKILL.md` orchestrates six phase workflows with file-presence prerequisites,
revision-bound fingerprints (`validate_brief.py`), and per-phase user approval. Entry modes
`new`/`continue`/`jump` with staleness routing. Strong data-level decoupling.

**Verdict per layer** (full evidence: agent reports; disposition table §27):

| Layer | Assessment |
|---|---|
| Orchestration & gates (SKILL.md + validate_brief/caption_gen/capture state machines) | **Excellent — the product.** `require`/`confirm-*`/`stamp` chain, consent doctrine, pending-marker capture protocol, transactional caption publishing. Keep. |
| Phase prose (workflows/) | **Overgrown.** Phases 2–5 average ~594 ln, ≥70% embedded implementation; three explicit "keep in sync" duties; the clip `<video>` contract stated 3×; `SKILL_DIR` resolver ×4 byte-identical; Phase 5 conflates five sub-domains in 866 ln. |
| Patterns/templates | **Split personality.** ~40% of patterns/ duplicated upstream; `patterns/INDEX.md` and `transition-catalog.md` point at a skill layout that no longer exists (pre-split monolith paths) — **broken today**. Templates are valuable *enforcement vehicles* (NaN guards) but carry a 7-copy SRI-pinned GSAP tag. |
| Scripts | Governance scripts unique and tested; `search_music.py`/`generate_voiceover.py` superseded by `media-use`. |
| Tests | Inverse to risk: 2,699 ln on governance, zero on the HTML/GSAP surface where silent breakage historically shipped. `test_question_contract.py` (docs-as-contract) is rare, genuine IP. |
| Runtime coupling | Fragile: `node_modules/hyperframes/dist/...` internal path, "v0.4.2"/"Chromium 147+" lore, deprecated gate names. |

Observed working-tree note: `example/` is currently deleted (unstaged). The redesign treats the
canonical example as a **rebuild deliverable** of the new pipeline (M6), not something to patch.

## 3. Current prompt review

Reasoning-to-implementation ratios measured per phase: P0 40/60 (cleanest), P1 35/65, P2 20/80,
P3 30/70, P4 25/75, P5 15/85. The implementation majority is exactly the content the ecosystem
now owns. Prompt-engineering defects: uppercase substitution tokens relying on agent diligence
(only `D` has a throw-guard); runtime constraints leaking into portable content (Claude's
4-option cap shaping menu architecture against the repo's own "name actions, not tools" rule);
version-pinned troubleshooting lore that rots fastest; soft "orchestrator-enforced" gates
honestly flagged but unverified. Strong prompt engineering worth keeping: neutral
`{"questions":[...]}` schema with single-point runtime binding; recommend-don't-select
labeling; the fingerprint vocabulary (`earliest_stale_phase`) giving resume semantics.

## 4. Storytelling review

The engineering spine is thicker than the storytelling spine — for a skill named "director",
direction is the least-developed layer:

- **Collected but dropped:** Phase 0's emotional-journey answer has no downstream consumer.
- **No pacing model:** mode structures are fixed slot templates; "vary scene durations" is
  asserted, not operationalized.
- **No motion/camera selection reasoning:** the storyboard `Animation` field has zero guidance
  connecting motion to narrative purpose; camera exists only as pattern references.
- **VO guidance purely mechanical** (commas, buffers, acronyms) despite Phase 0 capturing
  audience technicality and tone.
- **What's genuinely good:** product-spine doctrine, anti-slideshow rule, tutorial cold-open
  rationale, anti-slop editorial law, rich-state capture planning.

The ecosystem also now ships storytelling assets the skill ignores: `story-spine.md` (hook
language, value-before-evidence, storyboard-as-proposal), `beat-direction.md` (motion-verb
vocabulary: "if you can't name the verb, the element is not yet designed"), `narration.md`,
and 22 blueprints with a role menu mapping 1:1 to storyboard frame types.

## 5. HyperFrames integration review

Integration predates the ecosystem split and the workflow-engine era:

- Gates: requires `lint|inspect|validate` — now deprecated aliases of `check` (runtime/layout/
  motion/contrast, `sweep_static`, motion sidecars, `--caption-zone`, `--frame-check`).
- Formats: bespoke `project-plan.md` brief table, bespoke `storyboard.md` — parallel to official
  `BRIEF.md`/`STORYBOARD.md` (with parser, statuses, feedback sidecar) and `SCRIPT.md`.
- Loops: hand-rolled phase choreography parallel to `production-loop.md`/`review-loop.md`/
  `frame-worker-core.md`/`subagent-dispatch.md`.
- Audio: ElevenLabs/Freesound scripts parallel to `media-use`'s engine (which itself includes
  ElevenLabs in its TTS cascade) — and no access to its word-timestamp captions, SFX library,
  grading/LUTs, preference memory.
- Transitions: verbal DON'Ts parallel to `motion-doctrine`'s *numeric* seam gate — which
  explicitly declares its rules supersede guidance like this repo's, leaving two authorities
  with no arbitration note.
- Stale pointers: `patterns/INDEX.md:17-57`, `transition-catalog.md:52` reference the dead
  monolith layout.
- Missed capabilities: `hyperframes capture <url>`, registry blocks (97), Studio
  preview/selection bridge, `doctor`, cloud/lambda rendering, `feedback`.

## 6. Strengths (preserve verbatim)

1. The `validate_brief.py` gate chain + revision fingerprints — makes continue/jump safe.
2. The consent doctrine end-to-end (brief ownership, exact-track music, per-action attached-
   session consent, caption approval, consent-gated fixes).
3. Capture determinism machinery (`capture_screen.py` lock/pending/sidecar, terminal quarantine,
   `stitch_clip.py` CFR30 contract).
4. The hero-frame content check — the only defense against "all gates green, output wrong",
   the changelog's dominant failure archetype.
5. Verified-by-failure annotations (incoming-only crossfade, no-dynamic-loudnorm, `aformat`
   sidechain fix, screencast PTS, `tl.from()` trap) — content must survive even as location moves.
6. `patterns/anti-slop.md` editorial law + NaN-guard templates enforcing it in code.
7. design-systems/ brand-specific Motion+Avoid DNA with its legal posture (TRADEMARKS.md).
8. `test_question_contract.py` docs-as-contract testing; cross-runtime portability discipline.

## 7. Weaknesses

Ranked (evidence in §2–§5): (1) shadow-copy duplication with keep-in-sync duties; (2) script-
worthy programs living in prose (95-ln clip-audio bash, 66-ln asciinema recorder); (3) Phase-5
conflation; (4) triple-stated clip contract; (5) resolver ×4; (6) hard-coded catalog menus;
(7) version/layout-pinned couplings incl. a `node_modules` internal path; (8) thin storytelling
spine (§4); (9) runtime constraints leaked into portable prose; (10) unverified soft gates;
plus broken INDEX pointers and zero test coverage on the HTML surface.

## 8. Gap analysis

**Duplicated (delegate):** composition contract, GSAP rules/traps, transitions & seams, scene
skeletons, captions mechanics, TTS/music search, storyboard/brief formats, phase loops, gate
scripts, style catalogs, toolchain doctoring (render env), animation-map tooling.

**Missing (adopt from ecosystem):** `check` gate + motion sidecars + `--caption-zone`/
`--frame-check`; seam ledger + numeric gate; registry blocks; word-timestamp captions; SFX;
color grading/LUTs; preference memory + recipes; Studio review surfaces; audio-first "audio is
the clock" scheduling; dispatch economics; `hyperframes capture` for plain-URL sources; cloud
rendering; visual-grounding protocol for annotating screenshots.

**Missing (build — true white space, confirmed by ecosystem sweep):** per-scene communication
analysis; capability-driven runtime selection; camera/motion/metaphor grammars; consequential
emotional pacing; deep product discovery; authenticated/native/terminal capture (already the
moat); reviewed-caption governance; cross-runtime portability layer.

**Unnecessary complexity (retire/slim):** metallic-swoosh, INDEX.md as-is, transition mechanics
restatements, identity JSON menus, inline programs, `search_music.py`, `generate_voiceover.py`.

## 9. Proposed architecture — decision record

**Approaches considered:**

- **A. Meta-router:** hve becomes a thin router delegating whole videos to official workflows.
  *Rejected:* `/hyperframes` already IS the router; this would discard the consent model,
  capture moat, tutorial mode — the parts users chose this skill for.
- **B. Bolt-on Three.js:** keep v1, add a 3D phase step. *Rejected:* deepens the shadow-copy
  problem; every HyperFrames release widens drift; violates the HyperFrames-first mandate.
- **C. Director-over-delegates (CHOSEN):** re-base as a first-class HyperFrames *workflow
  skill* — thin orchestrator + reasoning modules + delegation, official formats, moats kept.

**Why C:** it is the only option where the skill's value concentrates in what nothing else
provides (direction + governance + capture), where ecosystem improvements are inherited free,
and where the mission's automatic-runtime-selection requirement has a natural home.

**The five layers of C:**

1. **Governance (kept, evolved):** entry modes, consent doctrine, fingerprints, per-phase
   approval — `validate_brief.py` v2 re-pointed at official artifacts (M4).
2. **Reasoning (new):** `reasoning/` + `grammar/` modules — the 16-stage pipeline (§11).
3. **Delegation (new posture):** the map in §14; load-on-demand like `/general-video`'s
   conditional mandatory-reads table.
4. **Capture (moat, kept):** Phase 2 unchanged in substance; adds `hyperframes capture` and
   `/figma` as source adapters.
5. **Build (re-based):** registry-first scene authoring, frame packets with a ~40-line
   builder delta, seam ledger, `check` + seam-gate + hero-frame verification ladder.

## 10. Architecture diagram

```
                       ┌────────────────────────────────────────────┐
                       │  SKILL.md — thin orchestrator (~250 ln)    │
                       │  entry modes · consent · gates · routing   │
                       └───────┬──────────────────┬─────────────────┘
             reasoning modules │                  │ governance scripts
      ┌────────────────────────┴───┐        ┌─────┴──────────────────────┐
      │ reasoning/ scene-analysis  │        │ validate_brief v2 · caption │
      │ capability-catalog         │        │ _gen · capture_screen ·     │
      │ grammar/ camera·motion·    │        │ stitch_clip · check_reqs    │
      │ metaphors·three-taxonomy   │        └────────────────────────────┘
      └────────────┬───────────────┘
   Phase 0 → 1 ────┴─→ STORYBOARD.md (+ director keys) ── Phase 2 CAPTURE (moat)
                          │                                 auth'd Chrome · native ·
                          ▼                                 terminal · hf capture · figma
   Phase 3 DESIGN ─ frame.md spec ─ registry blocks ─ frame packets + builder delta
                          │
   Phase 4 PRODUCTION ─ duration-sync ─ assembly ─ seam ledger/stamp
                          │
   Phase 5 AUDIO ─ media-use engine ─ caption governance ─ mix ─ render approval
                          │
        gates ladder: lint → check → seam-gate → hero-frame check → user approval
────────────────────────── DELEGATED (loaded on demand, never restated) ─────────────────────
 /hyperframes-core /hyperframes-animation /hyperframes-keyframes /hyperframes-creative
 /motion-doctrine /seam-craft /cut-the-curve /oversized-cursor /media-use
 /hyperframes-registry /hyperframes-cli /figma      · routing-out: /product-launch-video
 /pr-to-video /faceless-explainer /music-to-video /slideshow /website-to-video
```

## 11. Reasoning pipeline (16 stages)

| # | Stage | Phase | Inputs → Outputs | Why it exists / benefit |
|---|---|---|---|---|
| 1 | User intent analysis | 0 | request → subject, deliverable class, routing check | catches wrong-workflow early (routing honesty) |
| 2 | Audience analysis | 0 | Q&A → role, seniority, technicality | calibrates density, tone, VO register |
| 3 | Communication goals | 0 | Q&A → desired action + must-land claims | every later cut is judged against these |
| 4 | Story structure | 1 | mode + goals → arc (mode structures kept) | promo/showcase/tutorial spines |
| 5 | Beat extraction | 1 | arc + product facts → `## Frame N` blocks | beats are dispatch units (official format) |
| 6 | Emotional pacing | 1 | Phase-0 journey → `tone:`/`energy:` curve | **finally consumes** the collected arc; drives easing, seams, music |
| 7 | Information hierarchy | 1 | claims → per-frame `density:` + disclosure order | anti-overload; tutorial comprehension |
| 8 | Visual semantics | 1/frame | goal → `abstraction:` (literal>analog>metaphor>symbolic) | real product beats metaphor — spine doctrine |
| 9 | Metaphor selection | 1/frame | concept → `grammar/metaphors.md` entry | comprehension for the invisible; consistency rule |
| 10 | Scene planning | 1/frame | 8+9 → layout roles, focal, assets | staging; one focal per beat |
| 11 | Camera planning | 1/frame | goal+energy → `grammar/camera.md` move | camera answers a named viewer question |
| 12 | Motion planning | 1/frame | tone+density → blueprint/rules by name | vocabulary cited, never invented |
| 13 | Capability derivation | 1/frame | cited grammar entries + asset realities → capability tags (mechanical union, ADR-005) | technology-free requirements; no judgment, no drift |
| 14 | Runtime + skill selection | 1/frame | tags → `reasoning/capability-catalog.md` verdict + rejections | GSAP-first, hero budget, auditable `runtime_rejected:` |
| 15 | Rendering plan | 3 | spec + storyboard → frame.md, blocks list, packet plan | registry-first; blocks installed pre-fan-out |
| 16 | Prompt generation | 4 | packets → builder prompts (delta + recipes inlined) | builders see only their packet — official worker model |

Stages 8–14 are the per-scene instrument: `reasoning/scene-analysis.md` (twelve questions,
video-level budgets, pacing→mechanics table).

## 12–13. Capability & runtime selection frameworks

Full artifacts: `reasoning/capability-catalog.md`. Essence: scenes state **capabilities**
(spatial-depth, perspective-camera, volumetric-count, text-choreography, prebaked-asset,
gpu-compute…), the catalog maps them to runtimes with the official "GSAP default for 95%"
prior, a 1–3 hero-beat budget shared by three/html-in-canvas/typegpu, environment gating via
`doctor`, and a 3-term scoring heuristic where looks-only gains cap below understanding gains.
Every non-default selection and rejection is recorded in the storyboard. Future adapters =
one new table row; the procedure never changes. Three.js specifics (scene categories,
ingredients, rejection checklist): `grammar/three-taxonomy.md`.

## 14. HyperFrames skill orchestration strategy

Per-skill contract — *when / why / what it owns / what the director keeps*:

| Skill | When loaded | It owns | Director keeps |
|---|---|---|---|
| `/hyperframes-core` | P3/P4 authoring; packet assembly | composition contract, determinism, sub-comps, tracks, worker role core, production/review loop semantics | phase gating & consent wrapped around those loops |
| `/hyperframes-animation` | P1 (vocabulary indexes), P3/P4 (recipes, adapters, transitions) | all motion implementation, runtime adapters (incl. **three**), transition catalog | *choosing* from its indexes (grammars) |
| `/hyperframes-keyframes` | P3 on demand | pose contracts, motion proof diagnostics | deciding when proof is required |
| `/hyperframes-creative` | P1 (story-spine, narration, beat-direction), P3 (design spec, palettes, presets, adherence) | design-spec format & verification, generic styles | vendored brand design-systems (Path A), brief consent |
| `/motion-doctrine` + `/seam-craft` + `/cut-the-curve` | P1 (transition plan), P4 (ledger, stamp, gate) | seam law, numeric verification, render compositing | energy curve feeding seam choices |
| `/oversized-cursor` | P3 UI-demo scenes | cursor-as-eye-carrier technique | when a demo beat needs it |
| `/media-use` | P5 (+P2/P3 asset resolve) | TTS (ElevenLabs in cascade), BGM, SFX, transcription, caption data, grading/LUTs, media ops, preference memory | exact-track consent, caption review governance, mix approval |
| `/hyperframes-registry` | P3/P4 | 97 blocks, wiring contracts, contribution path | which block serves which beat (catalog-map pattern) |
| `/hyperframes-cli` | P2–P5 | capture(url), lint, **check**, snapshot, preview/Studio, render, doctor, cloud | gate *sequencing* + hero-frame check + approval gating |
| `/figma` | P2 | Figma asset/token/motion import | routing figma.com inputs to it |
| official workflows (PLV, pr-to-video, faceless-explainer, music-to-video, slideshow, website-to-video) | Phase −1 routing | their whole genres | honest hand-off offer; borrowing story shape only ("not their private scripts, pipeline state, or directory contract") |

Minimized duplication rule: this skill may *quote a pointer*, never a mechanism. The DON'Ts
section becomes pointers + four local laws (`prompts/skill-rewrite.md` §2b).

## 15. Storytelling framework

Keep the three mode spines and the product-spine doctrine; layer on: `story-spine.md` hook/
value-first discipline and storyboard-as-proposal presentation (P1 checkpoint becomes a frame
table with per-frame "why"); `beat-direction.md` motion verbs; the tone/energy curve (stage 6)
with its pacing→mechanics mapping; blueprint role menus as the beat→visual bridge; anti-slop
law as the editorial constitution; changelog-video's editorial-cut budget model for tutorial
chapters ("cutting is the job"); duration-variance check as an explicit gate.

## 16–19. Grammars

Delivered as implementation-ready modules: **camera** (`grammar/camera.md` — 17 moves, two
tiers, hard rules, pacing coupling), **motion** (`grammar/motion.md` — 15 principles mapped to
official owners + vocabulary sources), **metaphors** (`grammar/metaphors.md` — 8 domains ×
concept rows with runtime/camera/motion/why + selection rules), **Three.js taxonomy**
(`grammar/three-taxonomy.md` — 8 scene categories, ingredient defaults, rejection checklist).

## 20–21. Capability catalog & scene planning

Delivered: `reasoning/capability-catalog.md`, `reasoning/scene-analysis.md` (see §11–13).

## 22–24. Prompt refactoring, concrete modifications, SKILL.md improvements

Delivered: `prompts/skill-rewrite.md` — target layout with line budgets (workflows 3,122→
~1,710), complete replacement SKILL.md sections (Ecosystem Delegation Map, DON'Ts-as-pointers,
gate-modernization diff, Reasoning Pipeline section), per-phase rewrite shapes, the complete
new `sub-agents/scene-builder-delta.md`, and a before/after scene-direction comparison.

## 25. Modularization strategy

- One concern per file; phases stay <450 ln; modules <300 ln.
- `reasoning/` = judgment instruments; `grammar/` = vocabularies; both loaded by phases, never
  by builders (builders get packets).
- Kill lockstep duplication mechanically: resolver stated once in SKILL.md and *referenced*
  by phases; GSAP SRI tag ceases to matter as templates migrate to registry blocks; extend
  `test_question_contract.py` into a general parity/pointer-validity suite (assert every
  cross-skill path referenced actually exists on disk — would have caught the INDEX.md rot).
- Inline programs either die (clip-audio → media-use) or are promoted to tested scripts.

## 26. Suggested additional skills

Only where the ecosystem has nothing: **none need to be new sibling skills** — the reasoning/
grammar layer belongs inside this skill (it is its differentiation). Two upstream
*contributions* instead: (a) offer `design-systems/` brand packs to `hyperframes-creative`
(FRAME.md-ified, keeping the legal posture); (b) offer the authenticated-capture protocol +
native `capture_screen.py` pattern upstream once stable — they fill the ecosystem's only
capture gap. Anti-recommendation: do NOT create `/three`-style runtime skills; adapters exist.

## 27. Migration strategy

Principles: user-visible behavior never regresses mid-migration; each step independently
shippable + testable; legacy generated projects keep working via `validate_brief.py`'s
existing consent-gated migration pattern (extended with a `project-plan.md → BRIEF.md`
converter in M4).

Asset disposition (full table in the assets report; deltas already argued): retire
`metallic-swoosh.md`, `search_music.py`, `generate_voiceover.py`, INDEX.md-as-is; slim
`visual-patterns.md` (budgets/legibility only), `transition-catalog.md` (mood map only),
`marker-highlight.md` (stub); keep everything in §6; templates: governance + terminal + clip
pairs kept, text archetypes migrate to registry blocks with NaN-guard property preserved
(guards move into the packet contract: "a missing number is a build error").

## 28. Prioritized roadmap

| # | Step | Contents | Impact | Cx | Deps | Risks |
|---|---|---|---|---|---|---|
| M0 | Pointer & gate hotfix | Fix dead INDEX/catalog paths to split-skill layout; `lint\|inspect\|validate` → `lint`+`check` everywhere; delete `node_modules/...` path in favor of `check --snapshots` | Unbreaks today's runs | S | none | version skew on older CLI — feature-detect `check`, fall back |
| M0.5 | Compat thin waist (ADR-007) | `compat/ecosystem.md` symbolic-name map (only file with cross-skill paths/CLI names); skills-lock.json as tested-against pin; pointer-validity test suite; feature-detection probes; M0's fixes land inside the map | Ecosystem churn → one-file updates | S–M | M0 | discipline drift — CI-enforced by the pointer suite |
| M1 | Reasoning layer | Ship `reasoning/` + `grammar/`; Phase 1 gains stages 6–14; storyboard director keys (bespoke format still) | Mission's core value; auto-runtime-selection incl. Three.js | M | M0 | key sprawl — cap at the twelve questions; extend question-contract tests |
| M2 | Audio delegation | Phase 5 on media-use engine (ElevenLabs via cascade); retire 2 scripts; keep caption governance + mix consent | −~400 prose ln; word-timestamps, SFX, prefs for free | M | M0 | provider auth UX; keep verified mix recipes until media-use owns mixing |
| M3 | Seam system | Adopt motion-doctrine ledger + seam-stamp/seam-gate + seam-craft; retire transition mechanics prose | Numeric gate replaces verbal DON'Ts | M | M1 | Tier-A morphs stay hand-authored — scope gate to stamped seams |
| M4 | Format adoption | BRIEF.md/STORYBOARD.md/SCRIPT.md/frame.md; `validate_brief.py` v2 fingerprints official artifacts; legacy converter | Full ecosystem citizenship; Studio board/sidecar review for free | L | M1 | **highest-risk step** — parser round-trip tests + consent-gated migration mandatory |
| M5 | Build re-base | Registry-first scenes; frame packets + builder delta; dispatch economics; retire skeletons | Parallel builds; template debt (SRI ×7) dissolves | M | M3, M4 | block coverage gaps — keep terminal/clip templates as the fallback |
| M6 | Prune & rebuild example | Disposition table applied; example/ rebuilt end-to-end via the new pipeline; upstream contributions offered | Proof artifact; doc truth | M | M1–M5 | none material |

## 28b. What the first end-to-end run changed

The roadmap was implemented and then *exercised* — a 60s promo built by the skill, on the branch,
through every phase and gate to a rendered MP4. That run is the reason several things in this
document are now stated more strongly than they were proposed.

**It found nine defects that four review passes and 220 tests did not.** Five were skill defects
and are fixed on the branch; the rest were errors in the run's own artifacts. The pattern is what
matters, not the count:

| Defect | Why nothing else caught it |
|---|---|
| Sub-comp scripts lose module semantics | only the host document executes the clone |
| Classic scripts run under injected Proxies | appears only after converting away from modules |
| `hf-seek` carries the **root** clock | a frozen WebGL plate is a valid frame to every gate |
| Phase 1 never offered a validator-accepted music value | no test asserts prompt/validator parity |
| A cited recipe's inputs were never checked against the frame | the builder, not the gate, hit the contradiction |

The first three are the class ADR-003's amendment now names: **assembly-only defects**. They are
invisible in isolation, invisible to `lint`/`check`, invisible in a single-scene preview, and
reachable only at assembly — the latest and most expensive point. This is the architectural
argument for treating the `example/` rebuild (#33) as a release gate.

**Two decisions were reversed by contact with reality.** M6 deleted `scripts/search_music.py` as
superseded; the superseding path then stalled for two hours in its first real use, and the script
was restored (ADR-006 gained a retirement rule). M4's local music *generation* is no longer offered,
because a generated bed carries none of the provenance the brief is built to pin (ADR-008 gained a
provenance clause).

**What held up.** The consent machinery behaved exactly as designed: changing `music_strategy`
bumped the story fingerprint and staled all five phases without being asked to. The capability→
runtime selection put Three.js on exactly one frame of eight and recorded its rejection on another.
The caption contract refused three malformed approvals in a row. Builders reported conflicts rather
than silently resolving them — including one that corrected the orchestrator's own diagnosis.

## 29. Future-proofing

**Stability posture (ADR-007):** the HyperFrames ecosystem publishes no stability guarantees
and demonstrably evolves fast (recent monolith→split relayout, `validate`/`inspect`
deprecation) — but with good versioning affordances (graceful deprecations flagged in
`--json`, `skills check/update`, per-project CLI pinning, content-hash lockfile). The design
therefore assumes change: all cross-skill paths/CLI names live in one compat map
(`compat/ecosystem.md`, M0.5), pinned via `skills-lock.json` and CI-verified by the
pointer-validity suite; capabilities are feature-detected, never version-sniffed.

New HyperFrames runtime → one capability-catalog row. New blocks/blueprints → grammars cite
indexes, not items, so they appear automatically. Gate improvements → inherited via `check`/
`doctor`. Format evolution → validate_brief v2 wraps the official parser instead of owning a
format. The pointer-validity test suite turns ecosystem drift from silent rot into a red test.
Cross-runtime portability (Claude Code + Copilot CLI) is preserved because delegation targets
are files-on-disk and CLI calls, resolved through the existing `$SKILL_HOMES` mechanism.

---

## Self-review note

Checked for placeholders (none), internal consistency (delegation map ↔ roadmap ↔ disposition
agree), scope (M0–M2 are independently implementable; M4 isolated as the risk step), and
ambiguity (every "delegate" names its target file). Known open questions intentionally left
for the maintainer: (1) keep `project-plan.md` as a user-facing summary generated *from*
BRIEF.md, or drop it entirely in M4; (2) whether design-systems upstreaming waits for
HyperFrames interest or ships as a PR proactively; (3) example/ deletion in the working tree —
assumed intentional pending rebuild, not restored here.

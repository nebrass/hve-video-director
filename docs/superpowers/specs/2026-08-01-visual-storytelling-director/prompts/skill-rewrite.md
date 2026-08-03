# Concrete Prompt Modifications — SKILL.md & Workflows

> **Proposed replacement content** (deliverables: prompt refactoring strategy, concrete prompt
> modifications, SKILL.md improvements). Everything here is ready to apply after approval.
> Notation: 🆕 new section, ✂️ deletion, ♻️ rewrite-in-place.

## 1. Target file layout

```
SKILL.md                        ♻️  thin orchestrator (~250 lines; today 492)
workflows/
  phase-0-discovery.md          ♻️  light trim (~140 lines; today 152)
  phase-1-storytelling.md       ♻️  story reasoning + scene analysis (~350; today 593)
  phase-2-capture.md            ♻️  capture moat, dedup'd (~450; today 600)
  phase-3-design.md             ♻️  delegation + direction (~220; today 423)
  phase-4-production.md         ♻️  assembly delta on production-loop (~200; today 488)
  phase-5-audio.md              ♻️  media-use delegation + caption governance (~350; today 866)
reasoning/                      🆕  scene-analysis.md, capability-catalog.md
grammar/                        🆕  camera.md, motion.md, metaphors.md, three-taxonomy.md
sub-agents/
  scene-builder-delta.md        🆕  ~40-line delta prepended by frame-worker-core.md
patterns/                       ✂️➡️ keep: anti-slop, authenticated-browser-capture,
                                    cli-terminal-capture; slim: visual-patterns (budgets only),
                                    transition-catalog (mood map only), marker-highlight (stub);
                                    retire: metallic-swoosh, INDEX.md (rewrite as 20-line map)
compat/ecosystem.md             🆕  the thin waist (ADR-007): sole home of cross-skill paths,
                                    CLI names, format notes + named behavior probes
templates/                      ♻️  keep governance (context/plan/storyboard) + terminal pair +
                                    clip contract pair; migrate text archetypes → registry blocks
scripts/                        ✂️  retire search_music.py, generate_voiceover.py;
                                    keep validate_brief, caption_gen, capture_screen,
                                    stitch_clip, check_requirements
```

Net prompt-line budget: ~3,120 workflow lines → ~1,710, **plus** ~900 lines of new reasoning/
grammar modules that are pure director IP. Total shrinks slightly while the *reasoning* share
rises from ~25% to ~70%.

## 2. SKILL.md — replacement sections

### 2a. 🆕 § Ecosystem Delegation Map (insert after § Runtime Compatibility)

```markdown
## Ecosystem Delegation Map

This skill is a HyperFrames WORKFLOW: it owns the deliverable, the phase gates, and the
consent model. Every rendering, animation, design, and media capability is DELEGATED to the
official HyperFrames domain skills. Load them at the moments below — never restate their
content in this repo, and treat their rules as superseding any older local guidance.

| Capability | Owner (load on demand) | Used in |
|---|---|---|
| Composition contract, determinism, sub-comps, tracks | /hyperframes-core | 3, 4 |
| Motion recipes, blueprints, transitions, runtime adapters | /hyperframes-animation | 1, 3, 4 |
| Seek-safe keyframes + motion proof diagnostics | /hyperframes-keyframes | 3 (on demand) |
| Design specs, palettes, presets, story-spine, narration | /hyperframes-creative | 1, 3 |
| Seam law + ledger + numeric seam gate | /motion-doctrine (+ /seam-craft, /cut-the-curve) | 1, 4 |
| TTS, BGM, SFX, transcription, captions data, grading | /media-use | 5 |
| Registry blocks/components (`hyperframes add`) | /hyperframes-registry | 3, 4 |
| CLI: init/capture/lint/check/snapshot/preview/render/doctor | /hyperframes-cli | 2–5 |
| Figma sources | /figma | 2 |

Routing honesty — before Phase 0, if the request matches an official workflow better, say so
and offer it: plain commercial URL with no live-app capture → /product-launch-video; GitHub
PR → /pr-to-video; topic with no product → /faceless-explainer; music-driven → /music-to-video;
deck → /slideshow. This skill's home turf: a REAL running product (authenticated web app,
desktop app, CLI) captured for real, tutorial mode, vendored brand design systems, and the
consent-first creative brief.
```

### 2b. ♻️ § DON'Ts — shrink to pointers + the four local laws

Replace the 10-bullet renderer-knowledge list with:

```markdown
## DON'Ts

Authoritative motion/composition law lives in the ecosystem — load, don't restate:
determinism + composition contract → /hyperframes-core (references/determinism-rules.md);
seam law (exits, carriers, vectors, budgets) → /motion-doctrine; transition mechanics →
/hyperframes-animation (transitions/) + /seam-craft; property rules incl. the tl.from() trap,
display/visibility, <img> wrappers, clip <video> data-* contract → /hyperframes-core
(references/data-attributes.md, variables-and-media.md) + /hyperframes-animation (adapters/gsap.md).

Local law this repo still owns:
- No invented metrics — data scenes use real numbers or are cut (patterns/anti-slop.md; NaN
  guards in templates enforce it).
- Real product on screen is the spine — capture-coverage gate (Phase 3 entry).
- Cognitive-load budgets (emphasis, marker, hero beats, transitions) — single-sourced in
  reasoning/scene-analysis.md; cite, never restate numbers (ADR-008).
- Consent doctrine: recommendations are visible guidance, never a selection.
```

(The retired bullets' *content* survives — it moved upstream; the pointers make that explicit.
This ends the triple-statement drift risk on the clip contract and the GSAP traps.)

### 2c. ♻️ Gate modernization (Phase 4/5 prerequisites, everywhere they appear)

```diff
-Phase 5 needs `index.html` (root composition) and passing `npx hyperframes lint|inspect|validate`
+Phase 5 needs `index.html` (root composition) and passing `npx hyperframes lint` + `npx hyperframes check`
+(`inspect`/`validate` are deprecated aliases of `check`), plus `seam-gate.mjs verify` when a
+seam ledger exists (motion-doctrine).
```

Same substitution in `workflows/phase-4-production.md`, `phase-5-audio.md`, `CLAUDE.md`,
`README.md`. Add the hero-frame content check *after* `check` (it catches what green gates
cannot: wrong footage/stale src).

### 2d. 🆕 § Reasoning Pipeline (insert before § Pipeline)

```markdown
## Reasoning Pipeline

Sixteen stages, distributed across phases. Stages 1–7 are video-level; 8–16 run per scene.

Phase 0: (1) intent  (2) audience  (3) communication goals — recorded in context.md, and the
         emotional-journey answer becomes the tone: curve consumed in Phase 1 (stage 6).
Phase 1: (4) story structure  (5) beats  (6) emotional pacing  (7) information hierarchy —
         then per frame via reasoning/scene-analysis.md:
         (8) visual semantics  (9) metaphor [grammar/metaphors.md]  (10) scene plan
         (11) camera [grammar/camera.md]  (12) motion [grammar/motion.md]
         (13) capability requirements  (14) runtime + skill selection
         [reasoning/capability-catalog.md]
Phase 3: (15) rendering plan (design spec + registry blocks + packet assembly)
Phase 4: (16) builder prompt generation (frame packets; sub-agents/scene-builder-delta.md)

Every stage's output is a named artifact key — auditable in context.md or STORYBOARD.md.
```

## 3. Workflow rewrites — shape per phase

**phase-1-storytelling.md** ♻️ — keep: consent-owned Creative Brief collection, confirm-story
gate, mode structures, spine doctrine. Add: stage 6 emotional-pacing step (tone curve from
Phase 0), and a "run scene analysis" step iterating `reasoning/scene-analysis.md` over every
planned frame, then the video-level budget check. Delete: the ~175-line identity JSON menus
(generate the two-tier prompt from `design-systems/README.md` + the live
`../hyperframes-creative/references/visual-styles.md` at runtime); the transition-seconds
mapping (point at transitions doctrine); capture mechanics leakage (point at Phase 2);
the literal voice-ID (point at SKILL.md table).

**phase-3-design.md** ♻️ — becomes: (1) load `/hyperframes-creative` design-spec rules; resolve
identity path A–D into a `frame.md`-style spec (vendored brand DESIGN.md files remain Path A
sources); (2) registry-first: for each frame, `npx hyperframes add` any block the storyboard
named, customize in place (motion-graphics builder doctrine); (3) author remaining scenes via
frame packets. ✂️ both inline HTML/GSAP skeletons (~120 lines), the caption JS, the video
contract restatement — owners: hyperframes-core/animation + the two shipped clip templates.

**phase-4-production.md** ♻️ — becomes the assembly delta on the official production loop:
duration-sync from real VO timings; assemble sub-comps per `/hyperframes-core`; stamp seams
from the ledger (`seam-stamp.mjs`); gates = `lint` → `check` → `seam-gate verify` → hero-frame
content check → user preview approval. ✂️ init-template table, catalog table, the ~90-line
skeleton, transition recipes, the `node_modules/...` animation-map path (replace with
`npx hyperframes check --snapshots` + `snapshot --at` contact sheets).

**phase-5-audio.md** ♻️ — VO/BGM/SFX/transcription through `/media-use`'s audio engine
(ElevenLabs stays available as a cascade provider; the phonetic/comma doctrine moves to
SCRIPT.md conventions). Keep: exact-track consent, caption_gen.py draft→approve→finalize→
validate governance, loudness/sidechain verified recipes (until media-use owns mixing),
render approval. ✂️ the 95-line inline clip-audio program (promote to a tested script if kept),
CLI-version troubleshooting lore (→ `npx hyperframes doctor`).

## 4. 🆕 sub-agents/scene-builder-delta.md (complete file)

```markdown
# Scene builder — hve-video-director delta

You build ONE scene of a product video. The shared role contract precedes this delta
(frame-worker-core.md). Additions for this workflow:

- Your packet carries director keys: goal, tone, energy, density, camera, metaphor,
  blueprint/motion, runtime. They are binding direction. Implement cited blueprints/rules
  from the packet's inlined recipe bodies — never invent motion names.
- runtime: three | html-in-canvas → follow the packet's adapter excerpt exactly
  (hf-seek render, data-duration, preloaded assets). GSAP remains the timeline owner.
- Real captures are sacred: frame them per the design spec; never crop out product chrome,
  never overlay text on UI content regions, never replace a capture with an invented mock.
- Data honesty: numeric content comes only from packet-provided real values. A missing
  number is a build error, not an invitation (report it back; do not invent).
- Terminal scenes use the shipped templates (scene-terminal[-clip].html) verbatim.
- Captions: obey the overlay law (true vertical center; no reserved dead band) —
  captions-overlay doctrine.
```

## 5. Before/after — one representative scene-direction block

**Before (phase-3 v1):** 62-line HTML skeleton + "copy it instead of retyping, and keep it and
this skeleton in sync" + restated GSAP traps.

**After (storyboard frame, v2):**

```markdown
## Frame 4 — Dashboards that build themselves
- duration: 7.5
- goal: viewer believes setup takes one command
- abstraction: literal
- tone: relief   - energy: peak   - density: focal
- camera: push-in
- blueprint: cursor-ui-demo
- motion: oversized-cursor, control-target-sync
- capabilities: ui-micro-motion, timeline-choreography
- screenshot: public/screenshots/04-dashboard@2x.png
- transition_in: zoom-through
```

Twelve auditable lines of direction replace sixty lines of duplicated implementation; the
builder gets the recipes from the packet; the reviewer sees *why* every choice exists.

# Patterns Index — Wayfinding

Quick map: *"I need to do X"* → *"read this file."* hve-video-director leans on the HyperFrames domain skills for deep authoring guidance; this index keeps you from re-discovering which local pattern — and which ecosystem capability — covers which situation.

## Local patterns (in this directory)

| File | What it covers |
|---|---|
| `visual-patterns.md` | Easing vocabulary, scene-entry tweens (fade-up, scale-in, stagger, typewriter, counter), screenshot mockups (browser, floating card, device frame), **camera & depth** (camera moves on stills, scroll-within-frame, motivated parallax, anchored callout/spotlight, in-scene shine sweep, masked reveal), colour psychology, text sizing, project-wide DON'Ts |
| `metallic-swoosh.md` | Diagonal-shine transition between two scenes (inline in root timeline, not a sub-comp) |
| `marker-highlight.md` | 5 word-emphasis patterns: highlight, circle, burst, scribble, sketchout — for kicker lines, stat reveals, before/after |
| `transition-catalog.md` | One-page map of every CSS transition family + catalog blocks, mapped to product-video moments |
| `anti-slop.md` | Cardinal sins, soft tells, polish tells — distinguishes "shipped by a marketer" from "AI default output". Includes **§ AI Tool Promo Specifics** (dogfooding loop, show-don't-tell, 1-based phase numbering) and **§ CTA discipline** (full URL on screen, match canonical command). |
| `cli-terminal-capture.md` | Professional CLI scene recording via `asciinema` + `agg`: install, shell pre-flight (prompt, secrets, size), recording flags, cast editing, theme→palette pairing, MP4 render, quality gate, troubleshooting. Read when the storyboard calls for a real terminal clip; for the no-dep fallback see `templates/scene-terminal.html`. |
| `authenticated-browser-capture.md` | Connect Chrome DevTools MCP to an already-open Chrome 144+ session, select the exact SSO/MFA tab, capture without navigation, protect auth data, and restore viewport state. |

Seam/transition **law** now lives in the `motion-doctrine` skill (with `seam-craft` for render mechanics); it supersedes local transition guidance where the two disagree.

## Ecosystem capabilities

HyperFrames authoring guidance is split across several skills, pulled in on demand during Phases 3–5. Every capability we use is registered in **`compat/ecosystem.md`** — one row per capability, giving the owning skill, the exact skill-relative path, what it is, and who uses it.

Skill *names* are stable, so this index (like every workflow) names the skill and the capability SYMBOL — `hyperframes-creative` → VISUAL_STYLES. The intra-skill *paths* churn, so they live in the compat map and nowhere else: an upstream file move is then a one-file edit. A path pointing *inside* a skill, written anywhere outside that map, is the bug.

Read by-task, not by-default — loading a whole skill at once eats context.

## Decision flow

```
Phase 1 (storytelling)
  └─ Where does the visual identity come from?
      ├─ A vendored brand ("make it look like Stripe / Linear / Notion")
      │     → ../design-systems/<slug>/DESIGN.md — Path A, most specific;
      │       skips Phase 3 extraction entirely
      ├─ A named HF identity (one of 8 moods)
      │     → hyperframes-creative → VISUAL_STYLES + PALETTES (pair them) — Path B;
      │       skips extraction, allows minor tuning
      └─ Neither → Path C: Phase 3 extracts brand from screenshots → DESIGN.md

Phase 3 (design)
  ├─ Scene authoring → hyperframes-core → DATA_ATTRIBUTES (the data-* contract)
  │                    + hyperframes-creative → COMPOSITION_RECIPES
  │                      (picture-in-picture, title card, slide show)
  ├─ Motion philosophy, once per project → hyperframes-creative → MOTION_PRINCIPLES
  ├─ Animation → ../visual-patterns.md (this repo)
  ├─ Camera & depth on a still → ../visual-patterns.md § Camera & Depth (this repo):
  │     ├─ Push / pull / drift on a screenshot → § Camera Moves on Stills
  │     ├─ Pan a tall full-page capture        → § Scroll-Within-Frame
  │     ├─ Depth from real product layers      → § Motivated Parallax
  │     ├─ Direct the eye to a UI region       → § Anchored Callout / Spotlight
  │     ├─ Specular pass over a UI card        → § In-Scene Shine Sweep
  │     └─ Wipe an element in via a mask        → § Masked Reveal (mask-position)
  ├─ Charts/counters → hyperframes-creative → DATA_IN_MOTION
  └─ Emphasis on text → ../marker-highlight.md (this repo)

Phase 4 (production)
  ├─ Root composition wiring → hyperframes-core → COMPOSITION_ARCHITECTURE
  │                            (this repo is always the modular-orchestrator shape)
  ├─ Inter-scene transitions → law first: motion-doctrine → SEAM_LAW
  │                            → ../transition-catalog.md (this repo)
  │                            → hyperframes-animation → TRANSITION_CATALOG (+ TRANSITION_FAMILIES)
  └─ Quality gates → hyperframes-cli → CHECK_GATE
                     (`lint` while iterating, `check` as the final gate)

Phase 5 (audio)
  ├─ Voiceover → workflows/phase-5-audio.md
  ├─ On-screen captions → media-use → CAPTIONS_AUTHORING (+ TRANSCRIPT_HANDLING)
  │     optional in promo/showcase, REQUIRED in tutorial mode on footage segments
  │     (workflows/phase-5-audio.md § "Captions (REQUIRED in tutorial mode)", spec §7.2);
  │     reviewed out/final.srt + .vtt sidecars are required in ALL modes (Step 5.3b)
  └─ Audio-reactive flourishes → hyperframes-creative → AUDIO_REACTIVE
```

**Do not merge COMPOSITION_ARCHITECTURE and COMPOSITION_RECIPES.** The two upstream documents
carry near-identical names but answer different questions, and this index has already pointed at
the wrong one once. `hyperframes-core` → COMPOSITION_ARCHITECTURE is the **project shape** —
monolithic vs modular and the thin orchestrator root that declares slots, mounts audio, and
registers a near-empty root timeline; that is Phase 4's root-wiring concern, and this repo is
always modular. `hyperframes-creative` → COMPOSITION_RECIPES is the **scene arrangement** —
picture-in-picture, text-behind-subject, title card, slide show; that is a Phase 3 concern. The
creative document's own top-level example is a flat, clip-level composition, so it is *not* a
substitute for the orchestrator shape. Citing by SYMBOL rather than by filename is what keeps the
two apart — see `compat/ecosystem.md` § Disambiguation.

## Less common needs

- Word-emphasis in full depth (multi-line, mode cycling, per-word styling) → `hyperframes-animation` → MARKER_PATTERNS; our `marker-highlight.md` is the product-video subset.
- Picking a transition: start local (`transition-catalog.md`) for the wayfinding, descend to `hyperframes-animation` → TRANSITION_OVERVIEW + TRANSITION_FAMILIES for the implementation.
- Font pairing, especially stat-heavy scenes (tabular-nums) → `hyperframes-creative` → TYPOGRAPHY.
- No strong opinion on motion, colour or type → `hyperframes-creative` → HOUSE_STYLE.
- No `ELEVENLABS_API_KEY` → `media-use` → TTS_LOCAL (Kokoro-82M; prerequisites in AUDIO_REQUIREMENTS); word-level timestamps for caption sync → TRANSCRIBE; karaoke / beat-sync caption styling → CAPTIONS_MOTION.
- Dropping a live web page into a frame (rare — a screenshot is usually better) → `hyperframes-animation` → HTML_IN_CANVAS.

## Convention

When a phase workflow says *"see the hyperframes skill for X"*, that's a hint to invoke the `hyperframes` skill — now an intent **router** that points at the domain skill owning X. The domain skills (`hyperframes-core`, `-animation`, `-creative`, `-cli`, `-registry`, plus `media-use` and `motion-doctrine`) load on demand. Don't load a whole skill — take the capability SYMBOL from this index, resolve its one file through `compat/ecosystem.md`, and read only that.

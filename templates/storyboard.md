# Storyboard — {project-name}

**Duration:** {total}s | **Canvas:** {width}×{height} ({aspect}) | **Renderer:** HyperFrames
**Mode:** {promo | showcase | tutorial} | **Theme:** {light | dark}
**Product surface:** {ui | none}   *(ui = real captures are the spine; none = intentional abstract/no-product film — waives the Phase-3 capture-coverage gate)*
**Capture plan:** {N bound artifacts | none — skip Phase 2}
**Web capture source:** {navigate | attached-session | pending | n/a}
**Emotional journey:** {the film's tone curve, e.g. curiosity → tension → relief → confidence} *(Phase 1 Step 1.4a — read back from the Phase-0 emotional-journey answer in `context.md`. Every scene's `tone:` key traces this curve; Phase 5 reads it for the music brief.)*

All times are in **seconds**. Each scene below maps 1:1 to a HyperFrames sub-composition under `scenes/`. The Phase 4 root `index.html` references them via `data-composition-src`.

> **Scene numbering:** internal files use 0-based indices (`scenes/00-hero.html`) to match developer convention. **Viewer-facing labels** in the rendered video (e.g. pipeline chip numbers, "Scene 1 / Scene 2") use 1-based numbering. See `patterns/anti-slop.md` § "AI Tool Promo Specifics".

> **VO timing:** word count is a weak proxy for spoken duration. TTS voices often pause ~0.3–0.5s per comma. When a section overruns budget, drop commas before dropping words. See `workflows/phase-5-audio.md` § "Voice timing is non-linear".

> **Pronunciation:** TTS models render space-separated capital letters as a phonetic blob ("H V E" → "Sage V E"). Write acronyms phonetically ("Aitch Vee Ee") to force letter-by-letter pronunciation. See `workflows/phase-5-audio.md` § "Pronouncing acronyms".

---

### Scene {N}: {title}

**Window:** {start}s → {end}s ({duration}s)
**Scene file:** `scenes/{NN}-{slug}.html`
**Screenshot:** `public/screenshots/scene-{NN}-{desc}.png` *(REQUIRED for spine/product scenes — name the real capture this scene composites on screen; write `none — connective tissue` only for an intentional text/title/stat/CTA beat. A promo/showcase storyboard where NO scene names a screenshot or clip trips the Phase-3 capture-coverage gate unless Product surface is `none`.)*
**Capture:** none | screenshot | screencast | screen-recording | terminal | terminal-clip | supplied
*(default: `screenshot` for a product/spine scene; `none` for connective text/title/stat/CTA beats)*
**Capture duration:** {seconds}                              *(REQUIRED when Capture: screen-recording; fixed native recording duration)*
**Capture region:** {x,y,w,h}                               *(screen-recording only; optional — omit for the full desktop)*
**Command:** `<exact shell command>`                          *(REQUIRED when Capture: terminal-clip — the skill executes this autonomously via `asciinema rec --command`. Use `bash -c '…'` for multi-step pipelines. Omit for Capture: terminal, which uses authored output.)*
**Record timeout:** {seconds}                                *(terminal-clip only; default: scene duration + 2s — bounds non-terminating commands like dev servers / TUIs)*
**Clip:** `public/clips/scene-{NN}-{slug}.mp4`                *(REQUIRED exact output path when Capture: screen-recording; present when any Capture yields a clip)*
**Clip in/out:** {in}s–{out}s                                *(trim into the source; default: whole clip)*
**Speed:** 1.0                                               *(allowed: 0.1–5.0; defaultPlaybackRate; >1 only over dead air)*
**Clip audio:** none                                         *(default; set to a volume 0.0–1.0 to play the clip's own sound and duck the VO under it — Phase 5 Step 5.3a, spec §5.1/§14)*
**Captions:** auto                                           *(auto = Whisper on the VO; `carried` = on-screen copy already shows the spoken line, tutorial-only)*
**Chapter:** {title}                                         *(tutorial mode only — chapter/section name)*
**Step label:** Step {n} of {M}                              *(tutorial mode only — on-screen step pill)*

**Director keys:** *(Phase 1 Step 1.4b. `reasoning/scene-analysis.md` owns the twelve questions, the closed key set, and every allowed value — read them there; the list below is the shape, not the contract. Keep them as `- key: value` bullets: unknown bullets are preserved verbatim by the official storyboard parser (`STORYBOARD_EXTRA_KEYS`), so they survive a format migration untouched.)*
- goal: {one sentence, the viewer's perspective — what they understand when this frame ends}
- abstraction: {literal | analog | metaphor | symbolic}
- complexity: {atomic | compound | systemic}
- tone: {one lowercase word, from the film's `Emotional journey` above}
- energy: {calm | build | peak | resolve}
- density: {focal | composed | dense}
- camera: {the **Key** literal copied verbatim from `grammar/camera.md`'s Key column, or `static`. Never derive it from the Move display name — eight of sixteen rows disagree with naive lowercasing. A `-3d` suffix requests the Tier-B branch, which the Step 1.4c hero-beat check may deny}
- metaphor: {an entry name from `grammar/metaphors.md`, or `none — real product`}
- blueprint: {one blueprint id resolved through `BLUEPRINT_INDEX`}
- motion: {2–4 rule names resolved through `RULES_INDEX`, comma-separated, backticked, no directory, no `.md`}   *(at least one of `blueprint:` / `motion:` is REQUIRED; both together is the Adapt/Compose posture)*
- capabilities: {DERIVED, never chosen — the union of the tags declared by every grammar entry this frame cites, plus asset/subject realities, plus additions each carrying a stated reason. Vocabulary owned by `reasoning/capability-catalog.md`; never invent a tag}
- runtime: {omit this line entirely for the default runtime; otherwise the value the selection procedure in `reasoning/capability-catalog.md` returns}
- runtime_rejected: {`<runtime> — <reason>`, REQUIRED whenever a non-default runtime was considered and not chosen; omit the line when none was}
- user_directed: true                                        *(only when the user explicitly directed this frame; exempt from the budgets, but still counted and shown in the Step 1.4c report)*

> **Filled example** — scene 04 of a promo, the architecture beat:
>
> - goal: the viewer understands the product is three cooperating layers, not one box
> - abstraction: metaphor
> - complexity: compound
> - tone: curiosity
> - energy: build
> - density: composed
> - camera: exploded
> - metaphor: Layered architecture
> - motion: `depth-scatter-assemble`, `center-outward-expansion`
> - capabilities: timeline-choreography, spatial-depth
> - runtime_rejected: three — requested as `camera: exploded-3d`, but the film's hero beats are already committed elsewhere (budget table in `reasoning/scene-analysis.md`), so the frame re-derives to its Tier-A branch
>
> No `runtime:` line: the derived capabilities are served by the default. No `blueprint:` line: the
> two cited rules are the whole shape of this frame. This frame's `Screenshot:` is
> `none — connective tissue` — a metaphor beat draws invisible structure, so no capture is bound;
> a beat that *does* bind one gets `metaphor: none — real product` instead (`grammar/metaphors.md`
> selection rule 1).

**Visual:**
- Text on screen: "{headline}"
- Elements: {description — title, subtitle, mockup, stat card, etc.}

**Voiceover:**
> "{exact text to speak}"

**Animation (GSAP):**
- Entry: {e.g. "Headline `tl.fromTo('#headline', { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' }, 0.2)`; subtitle staggered 0.15s later. Always use `fromTo()` for opacity tweens — bare `tl.from()` on an `opacity:0` rest state flashes-then-disappears under stagger (see `patterns/visual-patterns.md`)."}
- During: {e.g. "Stat counter tweens 0 → 12,500 over 2.2s with `power1.out`"}
- Exit: *handled by the inter-scene transition — do not animate this scene out*

**Transition to next:** {crossfade | metallic-swoosh | zoom-through | slide-from-bottom | none} {0.4s quick | 0.7s medium | 1.2s slow} — derive from the confirmed `transition_style` / `transition_speed`; use the chosen style at main section boundaries, crossfade within a section, and `none` on the closing scene. Owned by the root composition, not this scene.

---

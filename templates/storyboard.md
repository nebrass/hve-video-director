# Storyboard — {project-name}

**Duration:** {total}s | **Canvas:** {width}×{height} ({aspect}) | **Renderer:** HyperFrames
**Mode:** {promo | showcase | tutorial} | **Theme:** {light | dark}
**Product surface:** {ui | none}   *(ui = real captures are the spine; none = intentional abstract/no-product film — waives the Phase-3 capture-coverage gate)*
**Capture plan:** {N bound artifacts | none — skip Phase 2}

All times are in **seconds**. Each scene below maps 1:1 to a HyperFrames sub-composition under `scenes/`. The Phase 4 root `index.html` references them via `data-composition-src`.

> **Scene numbering:** internal files use 0-based indices (`scenes/00-hero.html`) to match developer convention. **Viewer-facing labels** in the rendered video (e.g. pipeline chip numbers, "Scene 1 / Scene 2") use 1-based numbering. See `patterns/anti-slop.md` § "AI Tool Promo Specifics".

> **VO timing:** word count is a weak proxy for spoken duration. Comma density inflates significantly — Matilda (ElevenLabs) pauses ~0.3–0.5s per comma. When a section overruns budget, drop commas before dropping words. See `workflows/phase-5-audio.md` § "Voice timing is non-linear".

> **Pronunciation:** TTS models render space-separated capital letters as a phonetic blob ("H V E" → "Sage V E"). Write acronyms phonetically ("Aitch Vee Ee") to force letter-by-letter pronunciation. See `workflows/phase-5-audio.md` § "Pronouncing acronyms".

---

### Scene {N}: {title}

**Window:** {start}s → {end}s ({duration}s)
**Scene file:** `scenes/{NN}-{slug}.html`
**Screenshot:** `public/screenshots/scene-{NN}-{desc}.png` *(REQUIRED for spine/product scenes — name the real capture this scene composites on screen; write `none — connective tissue` only for an intentional text/title/stat/CTA beat. A promo/showcase storyboard where NO scene names a screenshot or clip trips the Phase-3 capture-coverage gate unless Product surface is `none`.)*
**Capture:** none | screenshot | screencast | terminal | terminal-clip | supplied
*(default: `screenshot` for a product/spine scene; `none` for connective text/title/stat/CTA beats)*
**Command:** `<exact shell command>`                          *(REQUIRED when Capture: terminal-clip — the skill executes this autonomously via `asciinema rec --command`. Use `bash -c '…'` for multi-step pipelines. Omit for Capture: terminal, which uses authored output.)*
**Record timeout:** {seconds}                                *(terminal-clip only; default: scene duration + 2s — bounds non-terminating commands like dev servers / TUIs)*
**Clip:** `public/clips/scene-{NN}-{slug}.mp4`                *(present when Capture yields a clip)*
**Clip in/out:** {in}s–{out}s                                *(trim into the source; default: whole clip)*
**Speed:** 1.0                                               *(allowed: 0.1–5.0; defaultPlaybackRate; >1 only over dead air)*
**Clip audio:** none                                         *(default; set to a volume 0.0–1.0 to play the clip's own sound and duck the VO under it — Phase 5 Step 5.3a, spec §5.1/§14)*
**Captions:** auto                                           *(auto = Whisper on the VO; `carried` = on-screen copy already shows the spoken line, tutorial-only)*
**Chapter:** {title}                                         *(tutorial mode only — chapter/section name)*
**Step label:** Step {n} of {M}                              *(tutorial mode only — on-screen step pill)*

**Visual:**
- Text on screen: "{headline}"
- Elements: {description — title, subtitle, mockup, stat card, etc.}

**Voiceover:**
> "{exact text to speak}"

**Animation (GSAP):**
- Entry: {e.g. "Headline `tl.fromTo('#headline', { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' }, 0.2)`; subtitle staggered 0.15s later. Always use `fromTo()` for opacity tweens — bare `tl.from()` on an `opacity:0` rest state flashes-then-disappears under stagger (see `patterns/visual-patterns.md`)."}
- During: {e.g. "Stat counter tweens 0 → 12,500 over 2.2s with `power1.out`"}
- Exit: *handled by the inter-scene transition — do not animate this scene out*

**Transition to next:** {Crossfade 0.4s | Metallic swoosh 0.4s | Hard cut} — owned by the root composition, not this scene.

---

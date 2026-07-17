# Storyboard — blog.nebrass.fr promo

**Duration:** ~53s | **Canvas:** 1920×1080 (16:9) | **Renderer:** HyperFrames
**Mode:** promo | **Theme:** light (Vercel-style)
**Product surface:** ui   *(real captures are the spine; built by hve-spielberg, signs off with the tool)*
**Capture plan:** 4 bound screenshots

5 scenes. The **real blog is the spine**: scenes 0–3 each composite a live Phase-2 capture in
browser chrome with a distinct, motivated camera move; scene 4 is the closing text CTA
(connective tissue). All times in seconds. Each scene maps 1:1 to a HyperFrames sub-composition
under `scenes/`.

VO timing discipline (per `workflows/phase-5-audio.md`):
- VO starts ≥1.0s after scene start; ends ≥0.5s before scene end.
- Adjacent scenes OVERLAP during the 0.4s crossfade (data-duration extends 0.4s past nominal end; next data-start moves 0.4s earlier).
- VO end-times below are nominal; verify with `npx hyperframes transcribe voiceover.mp3`.
- **Durations are deliberately varied** (8.4 / 12.4 / 10.4 / 12.4 / 11s) so the product scenes don't read as an even slideshow.

---

### Scene 0: Establishing — the blog itself

**Window:** 0s → 8.4s (incl. crossfade overlap)
**Scene file:** `scenes/00-establishing.html`  *(from `templates/scene-screenshot.html`)*
**Screenshot:** `public/screenshots/01-home-hero-light.png`
**Capture:** screenshot
**Camera:** slow motivated push-in (1.0→1.05) on the `.shot-browser` wrapper, transformOrigin toward the hero text; released before the crossfade.

**Visual:**
- The homepage hero in a light browser frame (traffic lights + `blog.nebrass.fr` in the URL bar), soft elevation shadow on the Vercel near-white surface.
- Optional one-line caption beneath: "blog.nebrass.fr".

**Voiceover (1.0s → ~6.8s):**
> "This is Nebrass's blog — software engineering, the cloud, and Java, written by someone who actually ships."

**Animation:** `.shot-browser` `fromTo({y:48, autoAlpha:0} → {y:0, autoAlpha:1}, 0.7s, expo.out)` at 0.2s; caption at 0.9s; push-in 1.1→ (released ~7.4s).

**Transition to next:** crossfade 0.4s at 8s.

---

### Scene 1: Depth — every post goes deep

**Window:** 8s → 20.4s
**Scene file:** `scenes/01-depth.html`  *(from `templates/scene-screenshot.html`)*
**Screenshot:** `public/screenshots/04-post-code-light.png`
**Capture:** screenshot
**Camera:** motivated push-in toward the code/diff block (transformOrigin on the highlighted code), then hold; released before the crossfade.

**Visual:**
- A real post reading view with syntax-highlighted code + red/green diff blocks ("Bug #1: a misplaced ffmpeg flag"), framed in browser chrome (`blog.nebrass.fr/playing-with-puppeteer…`).

**Voiceover (9.0s → ~18.5s):**
> "Every post goes deep. Real bugs, real fixes — like the two compounding bugs that were slowing Puppeteer's screencasts, traced and merged upstream."

**Animation:** wrapper entrance at 0.2s; push-in toward the code at ~1.2s (transformOrigin ~"30% 62%"), released ~11.4s.

**Transition to next:** crossfade 0.4s at 20s.

---

### Scene 2: Breadth — dozens of topics

**Window:** 20s → 30.4s
**Scene file:** `scenes/02-breadth.html`  *(from `templates/scene-screenshot.html`)*
**Screenshot:** `public/screenshots/05-categories-light.png`
**Capture:** screenshot
**Camera:** none — a clean settle (rhythm variety: not every scene moves). Static frame after entrance.

**Visual:**
- The categories index (tag cloud with real counts: Kubernetes, Security, Azure, Java, AI/ML…), framed in browser chrome (`blog.nebrass.fr/categories`).

**Voiceover (21.0s → ~28.8s):**
> "Kubernetes, security, Azure, machine learning — dozens of topics, all in one place."

**Animation:** `.shot-browser` `fromTo({y:48, autoAlpha:0} → {y:0, autoAlpha:1}, 0.7s, expo.out)` at 0.2s. No camera move (deliberate beat of stillness).

**Transition to next:** crossfade 0.4s at 30s.

---

### Scene 3: Volume — years of writing (scroll-within-frame)

**Window:** 30s → 42.4s
**Scene file:** `scenes/03-scroll.html`  *(from `templates/scene-screenshot.html`, scroll-within-frame variant)*
**Screenshot:** `public/screenshots/01-home-full-light.png`  *(full-page, 3840×15366)*
**Capture:** screenshot
**Camera:** scroll-within-frame — timeline-driven `translateY` on the inner `.shot-pan` wrapper, panning the tall homepage down the post list; ends on a lower post, released before the crossfade. (NOT scrollTop/listeners.)

**Visual:**
- The full homepage in a fixed browser frame; the long post list scrolls past inside the viewport — showing there's a lot to read.

**Voiceover (31.0s → ~40.5s):**
> "Years of write-ups — free to read, and always something new."

**Animation:** wrapper entrance at 0.2s; `.shot-pan` `to({y: −(imgRenderedHeight − viewHeight)*fraction})` over ~7s `power1.inOut` from ~1.2s; released ~41.4s.

**Transition to next:** crossfade 0.4s at 42s.

---

### Scene 4: CTA — where to find it (+ made-with sign-off)

**Window:** 42s → 53s (held final frame)
**Scene file:** `scenes/04-cta.html`  *(inline text skeleton — connective tissue / closing)*
**Screenshot:** `none — connective tissue`
**Capture:** none

**Visual:**
- URL on a clean canvas: `blog.nebrass.fr` (Geist, large), with a hairline rule.
- Sign-off line: "made with `/hve-spielberg`" (the dogfood hook survives).
- Held final 2s (no exit; closing scene).

**Voiceover (43.0s → ~51.0s):**
> "Find it at blog dot nebrass dot eff arr. And this whole video? Made with one command — slash Aitch Vee Ee Spielberg."

**Animation:** URL `fromTo({y:40, autoAlpha:0} → {y:0, autoAlpha:1}, 0.6s, expo.out)` at 0.3s; hairline width 0→540 at 0.9s; sign-off line at 1.6s; held from ~2.2s.

**Transition to next:** *none — closing scene, held final frame.*

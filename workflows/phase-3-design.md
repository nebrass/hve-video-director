# Phase 3: Design (HyperFrames scene templates)

Translate the selected visual identity and any Phase-2 capture artifacts into a `DESIGN.md` and
a set of brand-matched HTML scene templates. An intentional no-product film may reach this phase
without Phase-2 artifacts.

The authoring engine is **HyperFrames** (HTML + GSAP). There is no React, no JSX, no `useCurrentFrame`. Scene timing is expressed in **seconds** via `data-start` and `data-duration` attributes; motion is authored as GSAP tweens on paused timelines.

## Step 3.1: Seed DESIGN.md (3 strategies)

Pick the most specific path that Phase 1 Step 1.2 set up.

### Path A — Curated design system (fastest)

**If Phase 1 recorded `design_system: <slug>`** in `project-plan.md` (one of `stripe`, `linear-app`, `apple`, `notion`, `vercel`, `airbnb`, `github`, `cal`, `arc`, `bento`), the brand specification ships with the skill. Copy it straight into the project root:

```bash
# $SKILL_HOMES is the canonical home list defined in SKILL.md § Runtime Compatibility.
# Keep this line identical to that definition; edit it there, not here.
SKILL_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SKILL_HOMES="$HOME/.claude/skills|$HOME/.copilot/skills|$HOME/.agents/skills|$HOME/.pi/agent/skills|$HOME/.config/opencode/skills|$HOME/.cursor/skills|$HOME/.codex/skills|/etc/codex/skills|.claude/skills|.github/skills|.agents/skills|.pi/skills|.opencode/skills|.cursor/skills|.codex/skills|$SKILL_ROOT/.claude/skills|$SKILL_ROOT/.github/skills|$SKILL_ROOT/.agents/skills|$SKILL_ROOT/.pi/skills|$SKILL_ROOT/.opencode/skills|$SKILL_ROOT/.cursor/skills|$SKILL_ROOT/.codex/skills"
SKILL_DIR=$(
  OLD_IFS=$IFS
  IFS='|'
  for h in $SKILL_HOMES; do
    [ -d "$h/hve-spielberg" ] && { echo "$h/hve-spielberg"; break; }
  done
  IFS=$OLD_IFS
)
[ -n "$SKILL_DIR" ] || { echo "ERROR: hve-spielberg install dir not found — set SKILL_DIR to the skill's path manually" >&2; }
cp "$SKILL_DIR/design-systems/<slug>/DESIGN.md" ./DESIGN.md
```

Every preset includes the sections a HyperFrames composition actually needs: atmosphere, palette, typography, depth, **motion** (the section that distinguishes a video preset from a generic web spec), per-scene-type applications, and brand-specific anti-patterns. See `design-systems/README.md` for the catalog.

Then skim the captured screenshots only for **product-specific overrides**: a custom logo wordmark, a screenshot that suggests a different shade of the brand's accent colour, or a UI element worth referencing in a feature scene. Note these as **additions** to the seeded DESIGN.md, not replacements. This skim only enriches DESIGN.md *tokens* — the screenshots themselves remain the on-screen **spine** in scene authoring (Step 3.2 below), not palette fodder. Skip the rest of this section.

### Path B — HyperFrames named style (medium)

**If Phase 1 recorded `style: <name>`** (Swiss Pulse, Velvet Standard, Deconstructed, Maximalist Type, Data Drift, Soft Signal, Folk Frequency, Shadow Cut), invoke `Skill(hyperframes)` and read `visual-styles.md` for that style's palette, type, and motion feel. Pre-fill DESIGN.md from those values; skim the screenshots only to spot any conflicting brand cue worth overriding. Skip the rest of this section.

### Path C — Derive from screenshots (default)

Analyze the captured screenshots to identify the app's design language:

- **Color palette** — dominant colors, accent colors, surface/background, on-surface text
- **Typography** — font families (web-safe or Google Fonts equivalents), weight ladder, size relationships
- **Spacing** — padding, margins, gaps
- **Shape language** — border radius, shadow elevation, border treatment
- **Visual style** — glassmorphism, flat, material, neumorphism, brutalist, editorial

Write `DESIGN.md` at the project root. We use this as the design contract — it satisfies the HyperFrames Visual Identity Gate (which otherwise accepts a `visual-style.md`, a named style preset, or a 3-question fallback):

```markdown
## Design Contract

### Palette
- Primary:    #3b82f6
- Secondary:  #8b5cf6
- Surface:    #0f172a (dark) | #ffffff (light)
- On-surface: #f8fafc | #1e293b
- Accent:     #22c55e

### Typography
- Display:  Inter Bold, 80–120px
- Headline: Inter Bold, 60–80px
- Body:     Inter Regular, 32–44px
- Mono:     JetBrains Mono (for code excerpts)

### Shape
- Radius:    12px (cards), 999px (pills)
- Shadow:    0 30px 60px rgba(0,0,0,0.35)
- Borders:   1px hsl(220 14% 24%) for dark, 1px hsl(220 14% 90%) for light

### Motion Defaults
- Entrance ease: power3.out
- Stagger:       0.08–0.12s
- Transition:    crossfade 0.4s; metallic-swoosh between major sections only
```

The Phase 4 composition will reference values from this file; do not hard-code colors or font sizes in scene templates that aren't also documented here.

## Step 3.2: Author Scene Templates via the HyperFrames Skill

Invoke the `hyperframes` skill and request authoring of brand-matched scene templates. Each template is a **standalone HTML file** that will later be loaded as a sub-composition by the Phase 4 root `index.html`.

```
Invoke: Skill(hyperframes)
Context: "Author scene templates for {project-name}, using the palette and
typography defined in DESIGN.md. Output one HTML file per scene archetype
below into scenes/. Each file is a complete sub-composition with paused
GSAP timeline registered on window.__timelines."
```

**The spine of the video is the real product on screen.** Lead with capture-bearing
scenes that frame your Phase-2 screenshots/clips with depth; the text scenes (title,
stat, CTA) are *connective tissue between product beats*, not the substance. The Phase-2
captures are the **subject of the frame** — composite them on screen, do not merely sample
them for a palette. A film that is all text cards is the flat-slideshow failure mode
(`patterns/anti-slop.md` § The screenshot test); so is a film that buries the product
under decorative effects. Show the product, framed.

Request these scene archetypes (adapt to mode — promo or showcase).

**Spine — the real product, framed (lead with these):**

| File | Copy from | Purpose |
|---|---|---|
| `scenes/00-establishing.html` | `templates/scene-screenshot.html` | Opening hero: a real screenshot in a browser frame, with an optional **motivated** push-in |
| `scenes/NN-feature.html` | `templates/scene-screenshot.html` | A capability shown on the real UI — **requires** `<img src="public/screenshots/…">` inside a frame (or a clip) |
| `scenes/NN-compare.html` | `templates/scene-split-compare.html` | Before/after or pain→relief — both panes are real captures |
| `scenes/NN-clip.html` | `templates/scene-clip.html` | Real footage clip framed in a device/browser frame with overlays |
| `scenes/NN-terminal-clip.html` | `templates/scene-terminal-clip.html` | asciinema/agg terminal footage in a macOS-style window |

**Connective tissue — text & proof between product beats:**

| File | Copy from | Purpose |
|---|---|---|
| `scenes/NN-stat.html` | `templates/scene-stat.html` | A proof metric anchored **beside a real capture** — never a number on a blank canvas |
| `scenes/NN-title-card.html` | inline skeleton below | Headline + subtitle for the opening hook or a section break |
| `scenes/NN-cta.html` | adapt the title-card skeleton below | Call to action: headline, command/URL, brand sign-off |
| `scenes/NN-recap.html` | `templates/scene-recap.html` | **Tutorial-mode only** — chapter-summary recap beat (~90s segment cap) |

> This re-steers the **default** scene mix and the worked example only — it does **not**
> change the Phase-3 file-presence prerequisite. An intentionally abstract / no-product brand
> film is still valid (mark it `Product surface: none` — see `SKILL.md`). The Phase-2 capture
> **checkpoint** stays warn-don't-block, but the Phase-3 **capture-coverage gate** BLOCKS for
> promo/showcase when `product_surface: ui` and no scene shows a real capture (it WARNS in
> tutorial) — see `SKILL.md` § Entry Modes → `jump`.

Premium screenshot presentation (browser/device framing, motivated camera moves,
scroll-within-frame, parallax depth, anchored callouts) lives in
`patterns/visual-patterns.md` § Screenshot Presentation and § Camera & Depth — read them before hand-authoring,
and prefer pulling an equivalent HyperFrames catalog block (`app-showcase`, `ui-3d-reveal`)
where one exists.

Each scene template must:

- Be a valid HyperFrames **sub-composition** — the root is a `<div data-composition-id="…" data-width="{W}" data-height="{H}">` wrapped in a `<template>` (per HyperFrames `patterns.md`). Use the canvas dimensions chosen in Phase 1 (1920×1080, 1080×1920, 1080×1080, or 1080×1350). Sub-comps loaded via `data-composition-src` *require* this `<template>` wrapper; only the root `index.html` skips it.
- Author the **resting layout first** in static CSS, then layer GSAP entrance tweens via `tl.fromTo()` (explicit from/to states — never bare `tl.from()` on opacity-bearing elements; see `patterns/visual-patterns.md` § "tl.from() stagger trap"). Never animate to a position — animate from an offset to the rest position.
- Initialize and register the timeline: `window.__timelines = window.__timelines || {}; window.__timelines["<composition-id>"] = tl;` (paused).
- Use palette and typography tokens from `DESIGN.md`. Reference colors and fonts inline; HyperFrames embeds supported fonts automatically.
- Place every visible animated element at `opacity: 0` inline so the first paint is invisible.
- Use the canvas dimensions selected in Phase 1 — do not hard-code 1920×1080 if the project is vertical or square.

### Scene template skeleton — the spine (a real screenshot in a browser frame)

This is the canonical scene: a Phase-2 capture composited in browser chrome with depth.
The fully-commented copy-ready file (plus scroll-within-frame, split-compare, and stat
variants) is `templates/scene-screenshot.html` — **copy it instead of retyping**, and keep
it and this skeleton in sync (same GSAP SRI, same wrapper-only motion). The `<img>` lives in
a **non-timed wrapper**; all motion is on the wrapper, never on the image.

```html
<template id="scene-00-establishing-template">
  <div data-composition-id="scene-00-establishing"
       data-width="1920" data-height="1080"> <!-- swap for 1080×1920 / 1080×1080 / 1080×1350 if vertical / square / portrait -->

    <div class="shot-stage">
      <div class="shot-browser">                          <!-- ANIMATED WRAPPER — never the <img>; scoped classes, no bare #id -->
        <div class="shot-bar">
          <span class="dot dr"></span><span class="dot dy"></span><span class="dot dg"></span>
          <span class="shot-host">app.yourproduct.com</span>
        </div>
        <div class="shot-view">                             <!-- overflow-hidden viewport -->
          <div class="shot-pan">                            <!-- inner wrapper for scroll-within-frame -->
            <img class="shot-img" src="public/screenshots/REPLACE.png" alt="">
          </div>
        </div>
      </div>
      <p class="shot-caption" id="shot-caption">Optional supporting line — or delete</p>
    </div>

    <style>
      [data-composition-id="scene-00-establishing"]{position:absolute;inset:0;display:flex;
        align-items:center;justify-content:center;
        background:radial-gradient(120% 120% at 50% 0%, #ffffff 0%, #eef1f5 100%); /* DESIGN.md surface */
        font-family:"Inter",system-ui,sans-serif}
      [data-composition-id="scene-00-establishing"] .shot-stage{display:flex;flex-direction:column;
        align-items:center;gap:40px;width:100%}
      [data-composition-id="scene-00-establishing"] .shot-browser{width:72%;max-width:1480px;
        border-radius:14px;overflow:hidden;background:#fff;visibility:hidden;opacity:0;     /* revealed via autoAlpha */
        box-shadow:0 0 0 1px rgba(0,0,0,.06),0 2px 6px rgba(0,0,0,.05),0 40px 90px rgba(0,0,0,.18)}
      [data-composition-id="scene-00-establishing"] .shot-bar{display:flex;align-items:center;gap:9px;
        padding:14px 18px;background:#f3f4f6;border-bottom:1px solid rgba(0,0,0,.06)}
      [data-composition-id="scene-00-establishing"] .dot{width:13px;height:13px;border-radius:50%}
      [data-composition-id="scene-00-establishing"] .dr{background:#ff5f56}
      [data-composition-id="scene-00-establishing"] .dy{background:#ffbd2e}
      [data-composition-id="scene-00-establishing"] .dg{background:#27c93f}
      [data-composition-id="scene-00-establishing"] .shot-host{margin-left:14px;color:#6b7280;
        font:18px "Geist Mono","JetBrains Mono",monospace}
      [data-composition-id="scene-00-establishing"] .shot-view{position:relative;width:100%;
        max-height:72vh;overflow:hidden;background:#fff} /* real fixed window: caps tall captures, pan target for scroll */
      [data-composition-id="scene-00-establishing"] .shot-img{display:block;width:100%;height:auto} /* dims via CSS, NEVER tweened */
      [data-composition-id="scene-00-establishing"] .shot-caption{font-size:30px;color:#4b5563;
        text-align:center;max-width:1100px;visibility:hidden;opacity:0}
    </style>

    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js" integrity="sha384-sG0Hv1tP1lZCk9KQmrIbY/XNwi+OY84GQqhMscbnsoBFqAz8KNCil1kvfL3Hbbk2" crossorigin="anonymous"></script>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      const root = '[data-composition-id="scene-00-establishing"]';
      // Entrance: animate the WRAPPER (autoAlpha + fromTo). Never tl.from(); never the <img>.
      tl.fromTo(root + ' .shot-browser', { y: 48, autoAlpha: 0 },
        { y: 0, autoAlpha: 1, duration: 0.7, ease: "expo.out" }, 0.2);
      tl.fromTo(root + ' .shot-caption', { y: 16, autoAlpha: 0 },
        { y: 0, autoAlpha: 1, duration: 0.5, ease: "power2.out" }, 0.9);
      // OPTIONAL motivated push-in (wrapper only; release before the crossfade; never on the closing scene):
      // tl.fromTo(root+' .shot-browser', {scale:1.0}, {scale:1.06, transformOrigin:"32% 28%", duration:2.2, ease:"power1.inOut"}, 1.1);
      window.__timelines["scene-00-establishing"] = tl;
    </script>
  </div>
</template>
```

### Secondary skeleton — title card (connective tissue)

Use between product beats — an opening hook, a section break, a sign-off. Selectors are
scoped (not bare `#id`) so two text scenes in one composition never collide.

```html
<template id="scene-NN-title-card-template">
  <div data-composition-id="scene-NN-title-card" data-width="1920" data-height="1080">
    <h1 class="tc-h" style="opacity:0">Your headline here</h1>
    <p  class="tc-s" style="opacity:0">Supporting copy</p>
    <style>
      [data-composition-id="scene-NN-title-card"]{position:absolute;inset:0;display:flex;
        flex-direction:column;align-items:center;justify-content:center;
        background:#0f172a;color:#f8fafc;font-family:"Inter",sans-serif}  /* DESIGN.md surface / on-surface */
      [data-composition-id="scene-NN-title-card"] .tc-h{font-size:96px;font-weight:800}
      [data-composition-id="scene-NN-title-card"] .tc-s{font-size:44px;margin-top:24px}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js" integrity="sha384-sG0Hv1tP1lZCk9KQmrIbY/XNwi+OY84GQqhMscbnsoBFqAz8KNCil1kvfL3Hbbk2" crossorigin="anonymous"></script>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      const root = '[data-composition-id="scene-NN-title-card"]';
      // Always fromTo() for opacity tweens (see patterns/visual-patterns.md § "tl.from() stagger trap").
      tl.fromTo(root + ' .tc-h', { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: "power3.out" }, 0.2);
      tl.fromTo(root + ' .tc-s', { y: 24, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, ease: "power2.out" }, 0.5);
      window.__timelines["scene-NN-title-card"] = tl;
    </script>
  </div>
</template>
```

The `data-composition-id` value on the inner `<div>` must match the `data-composition-id` on the loader in the Phase 4 root `index.html`.

Animation pattern reference: `patterns/visual-patterns.md`.
Transition pattern reference (when an archetype owns its own outgoing flourish): `patterns/metallic-swoosh.md`.

**Before authoring a scene from scratch**, check the HyperFrames catalog — blocks like `app-showcase`, `ui-3d-reveal`, `data-chart`, `logo-outro`, and `reddit-post` are drop-in sub-compositions that cover most product-video archetypes. See Phase 4 Step 4.2 for the `npx hyperframes add <name>` workflow. Pulling a catalog block is almost always faster than hand-authoring an equivalent scene.

### Clip scene (real footage)

A clip scene is a normal sub-composition containing a `<video muted playsinline>` that carries
the explicit clip contract: `id`, `data-start="0"`, `data-duration`, `data-media-start`, and
`data-track-index="0"`. The runtime frame-syncs the video's `currentTime` to this scene's window
from those attributes (Wiring S — render-verified). Two values matter:

- `data-duration` = the scene loader's **full** `data-duration` from `index.html` — i.e.
  `(out-in)/speed` **plus the 0.4s crossfade extension** (Phase 4 Step 4.5 /
  `patterns/transition-catalog.md`). If the video's track ends at the nominal clip length,
  the runtime hides it (`visibility:hidden`) during the crossfade and the outgoing scene
  shows an empty frame.
- `data-media-start` = the storyboard's `Clip in` (trim offset into the source, seconds;
  `0` if the whole clip is used). Without it the runtime plays from source `t=0`, the
  `Clip in/out` trim is silently ignored, and the footage desyncs from Phase 5's
  clip-audio extraction (`CIN`).
- Set the video's `defaultPlaybackRate` and `playbackRate` to the storyboard `Speed` before
  registering the timeline. Reject values outside **0.1–5.0** (the HyperFrames runtime's
  supported range). Scene duration and clip-own audio both use the same value; leaving the
  video at `1.0` desynchronizes footage whenever `Speed != 1`.

**Do not omit the contract**: the runtime only seeks
videos that carry `data-start`, so a bare `<video>` is displayed but never time-synced — safe only
as the single clip in the whole composition, and with two or more clip scenes bare videos
cross-route (one scene plays another's footage, another plays black). And **never animate the
`<video>` dimensions** — wrap it in a non-timed `.clip-frame` div and animate the wrapper. Copy
`templates/scene-clip.html` as the starting point (`templates/scene-terminal-clip.html` for
asciinema/agg terminal footage).

**Mandatory brand treatments** (so footage reads premium, not raw): device/browser frame +
drop shadow, a vignette toward the brand canvas, a hidden OS cursor replaced by a brand-styled
pointer with a click pulse, and a color-grade toward the active design system's tokens. The
`<video>` stays muted; clip-own audio, if enabled, is mixed separately in Phase 5 Step 5.3a.

- **Tutorial mode:** layer a Step-Label / Chapter overlay (`patterns/visual-patterns.md` § Step Label / Chapter Overlay) so each instructional scene shows `Step N of M` + chapter title (spec §7.2c).

### Caption track for footage scenes (tutorial mode)

When content-mode is `tutorial`, author one caption sub-comp per footage scene from the
Phase-5 `transcript.json` (word-level), then wire it over the scene window in Phase 4.
Mechanism per `references/captions.md` — invoke `Skill(hyperframes)` and read it. Skeleton
(deterministic, fully seekable — no `Math.random()`/`Date.now()`):

```js
// GROUPS: [{text,start,end}] from transcript.json (3–5 words/group; break on sentence
// boundaries or 150ms+ pauses). One group visible at a time; cg-<i> element IDs.
GROUPS.forEach(function (g, gi) {
  var el = document.getElementById("cg-" + gi);
  tl.fromTo(el, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.18, ease: "power2.out" }, g.start);
  tl.to(el, { opacity: 0, duration: 0.12, ease: "power2.in" }, g.end - 0.12);
  tl.set(el, { opacity: 0, visibility: "hidden" }, g.end);   // deterministic hard kill
});
```

Positioning (per `captions.md`): bottom 80–120px, `position:absolute; overflow:visible`,
full-width centered container (NOT `left:50%;translateX(-50%)`). Text ≥24px, high contrast.
Run the `[caption-lint]` self-check before `window.__timelines[id] = tl`.

## Step 3.3: Author Scenes (preview + gates run in Phase 4)

Build each scene template to match `DESIGN.md`. A scene file is a `<template>`-wrapped sub-composition: it can't be previewed standalone (the HyperFrames runtime clones and drives it), and the CLI gates take a project **directory** that resolves `index.html` — which doesn't exist until Phase 4. So per-scene preview and the mechanical gates run in Phase 4, after `index.html` references the scenes:

- `npx hyperframes preview .` opens the studio, which lists `main` **plus every scene composition individually** for scrubbing.
- `npx hyperframes lint .` / `inspect . --samples 10` / `validate .` check the assembled project.

Author with these failure modes in mind so Phase 4's gates pass first try:

- Overlapping elements at rest (Phase 4 `inspect` flags container/text overflow)
- Text contrast below WCAG AA (Phase 4 `validate` runs a contrast audit)
- Animations that imply an exit (Phase 4 transitions own the exit — see DON'Ts in `SKILL.md`)

Then ask the user:

```json
{
  "questions": [{
    "question": "How do the branded scene templates look?",
    "header": "Review",
    "options": [
      { "label": "Looks great", "description": "Proceed to composition assembly (Phase 4)" },
      { "label": "Needs refinement", "description": "I'll give specific feedback per scene" }
    ],
    "multiSelect": false
  }]
}
```

## Output

- `DESIGN.md` — design contract (palette, typography, shape, motion defaults)
- `scenes/*.html` — brand-matched HyperFrames scene templates
- `scenes/assets/` — any decorative assets (icons, brand marks) referenced by templates

Any Phase-2 artifacts already live at their storyboard-bound paths under `public/screenshots/`,
`public/clips/`, or `scenes/`. An intentional no-product film with `Capture plan: none` has no
Phase-2 directory requirement.

## Checkpoint

> "Design contract and [N] scene templates ready. Palette + typography locked in `DESIGN.md`. Scenes are verified in Phase 4 — `preview .` lists each one individually for scrubbing and `lint`/`inspect`/`validate .` run on the assembled composition.
>
> Ready to move to Phase 4: Composition assembly?"

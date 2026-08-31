# Phase 3: Design (HyperFrames scene templates)

Translate the selected visual identity and any Phase-2 capture artifacts into a `DESIGN.md` and
a set of brand-matched HTML scene templates. An intentional no-product film may reach this phase
without Phase-2 artifacts.

The authoring engine is **HyperFrames** (HTML + GSAP). There is no React, no JSX, no `useCurrentFrame`. Scene timing is expressed in **seconds** via `data-start` and `data-duration` attributes; motion is authored as GSAP tweens on paused timelines.

This is where the director keys stop being a planning record and start being build input. The phase
runs in five steps: seed the design spec (3.1), plan each scene registry-first (3.2), assemble one
ephemeral **frame packet** per scene (3.3), dispatch the builds (3.4), collect and review (3.5).

Before authoring, require Phase 2 (including an intentional stamped skip) to be fresh:

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" require phase-2
```

A nonzero exit routes to the earliest stale prior phase even when capture files exist.

## Reading the storyboard

Every frame value this phase needs — `src`, `duration`, `screenshot`, `clip`, `clip_in`,
`clip_out`, `speed`, `chapter`, `step_label`, and the director keys — is a `- key: value` bullet in
that frame's metadata block. Read them through the installed validator rather than by eye; it
returns official fields and preserved `extra` bullets in one payload, and that payload is what
Step 3.3 copies into each packet:

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" storyboard --json
```

`format: official` is the shape Phase 1 writes. `format: legacy` is a project created before this
shape: **it parses and it resumes** — nothing here is gated on the shape, and the payload presents
legacy scenes in the same frame structure, so read it and carry on. If converting the file would
genuinely help the user, present it as a choice and run `migrate-storyboard` only on an explicit
yes; that command copies the original aside before writing and never deletes it. Never convert
because it is tidier, and never write official bullets into a legacy-shape file.

## Step 3.1: Seed DESIGN.md (4 strategies)

Use the identity path the user explicitly confirmed in Phase 1. Never substitute another path
because it seems faster or more appropriate.

The confirmed `theme` is a hard design input for every path. Add a `### Confirmed Theme` section
to `DESIGN.md` that names `light` or `dark` and defines the canvas, surface, text, border, shadow,
and browser/terminal chrome tokens for that mode. Do not leave dual light/dark alternatives in
the final contract. If the selected identity cannot produce the confirmed theme, return to Phase 1
instead of improvising or overriding the user.

### Path A — Curated design system

**If Phase 1 recorded `identity_strategy: design-system` and `identity_choice: <slug>`** in
`project-plan.md` (one of `stripe`, `linear-app`, `apple`, `notion`, `vercel`, `airbnb`, `github`,
`cal`, `arc`, `bento`), the brand specification ships with the skill. Copy it straight into the
project root:

```bash
# $SKILL_HOMES is the canonical home list defined in SKILL.md § Runtime Compatibility.
# Keep this line identical to that definition; edit it there, not here.
SKILL_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SKILL_HOMES="$HOME/.claude/skills|$HOME/.copilot/skills|$HOME/.agents/skills|$HOME/.pi/agent/skills|$HOME/.config/opencode/skills|$HOME/.cursor/skills|$HOME/.codex/skills|/etc/codex/skills|.claude/skills|.github/skills|.agents/skills|.pi/skills|.opencode/skills|.cursor/skills|.codex/skills|$SKILL_ROOT/.claude/skills|$SKILL_ROOT/.github/skills|$SKILL_ROOT/.agents/skills|$SKILL_ROOT/.pi/skills|$SKILL_ROOT/.opencode/skills|$SKILL_ROOT/.cursor/skills|$SKILL_ROOT/.codex/skills"
# zsh does not word-split unquoted $SKILL_HOMES and makes an unmatched glob fatal;
# both make this loop silently resolve to nothing. No-ops in bash/dash/sh.
if [ -n "${ZSH_VERSION:-}" ]; then setopt shwordsplit nullglob; fi
SKILL_DIR=$(
  OLD_IFS=$IFS
  IFS='|'
  for h in $SKILL_HOMES; do
    [ -d "$h/hve-video-director" ] && { echo "$h/hve-video-director"; break; }
    # Fallback: a clone left under a pre-v0.1.0 directory name. Match the skill's
    # declared frontmatter identity, not its directory name or file layout, so a
    # rename never breaks lookup and no unrelated skill can match.
    for c in "$h"/*/; do
      [ -f "$c/SKILL.md" ] && grep -q '^name:[[:space:]]*hve-video-director[[:space:]]*$' "$c/SKILL.md" \
        && { echo "${c%/}"; break 2; }
    done
  done
  IFS=$OLD_IFS
)
[ -n "$SKILL_DIR" ] || { echo "ERROR: hve-video-director install dir not found — set SKILL_DIR to the skill's path manually" >&2; }
cp "$SKILL_DIR/design-systems/<slug>/DESIGN.md" ./DESIGN.md
```

Every preset includes the sections a HyperFrames composition actually needs: atmosphere, palette, typography, depth, **motion** (the section that distinguishes a video preset from a generic web spec), per-scene-type applications, and brand-specific anti-patterns. See `design-systems/README.md` for the catalog.

Immediately resolve the copied preset to the confirmed theme using the compatibility table from
Phase 1. For dual-theme systems, choose the documented role values for that mode. For single-theme
systems, the validator has already required their native mode; do not invert the palette. Then
skim the captured screenshots only for **product-specific overrides**: a custom logo wordmark, a
screenshot that suggests a different shade of the brand's accent colour, or a UI element worth
referencing in a feature scene. Note these as **additions** to the seeded DESIGN.md, not
replacements. This skim only enriches DESIGN.md *tokens* — the screenshots themselves remain the
on-screen **spine** in scene authoring (Step 3.2 below), not palette fodder. Skip the rest of this
section.

### Path B — HyperFrames named style

**If Phase 1 recorded `identity_strategy: hyperframes-style` and the style name in
`identity_choice`** (Swiss Pulse, Velvet Standard, Deconstructed, Maximalist Type, Data Drift,
Soft Signal, Folk Frequency, Shadow Cut), invoke `Skill(hyperframes-creative)` and read its
`VISUAL_STYLES` reference (path in `compat/ecosystem.md`) for that style's palette, type, and
motion feel. Pre-fill DESIGN.md from those values; skim the
screenshots only to spot any conflicting brand cue worth overriding. Resolve every semantic color
role to the confirmed theme while preserving the named style's identity. Skip the rest of this
section.

### Path C — Custom identity

**If Phase 1 recorded `identity_strategy: custom`**, use the exact guide, `DESIGN.md`, or named
direction in `identity_choice`. Preserve the user's stated constraints and translate them into the
same palette, typography, depth, shape, and motion sections required below. Do not replace the
custom direction with a curated system or named style. If the guide explicitly requires the
opposite theme, return to Phase 1 and ask the user to change the theme or custom identity.

### Path D — Derive from screenshots

Analyze only captures that passed the Phase-2 confirmed-theme gate to identify the app's design
language:

- **Color palette** — dominant colors, accent colors, surface/background, on-surface text
- **Typography** — font families (web-safe or Google Fonts equivalents), weight ladder, size relationships
- **Spacing** — padding, margins, gaps
- **Shape language** — border radius, shadow elevation, border treatment
- **Visual style** — glassmorphism, flat, material, neumorphism, brutalist, editorial

Write `DESIGN.md` at the project root; it is this pipeline's design contract. `DESIGN_SPEC` owns the resolution order upstream applies when several design files exist, and is worth reading once — note that `DESIGN.md` is **last** in it, so a project carrying one of the earlier names would be resolved to that instead. This skill writes only `DESIGN.md`. (An earlier version of this step cited a "Visual Identity Gate" and a `visual-style.md`; neither exists upstream, which is what the `DESIGN_SPEC` row now pins.)

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
- Transition:    {confirmed transition_style} at {0.4s quick | 0.7s medium | 1.2s slow}
- Connective cut: crossfade at the same confirmed duration
```

Copy `transition_style` and `transition_speed` from the confirmed Creative Brief into these motion
defaults. The Phase 4 composition will reference values from this file; do not hard-code colors,
font sizes, transition styles, or transition durations that aren't also documented here.

## Step 3.2: Plan the scenes — registry first

Every storyboard frame becomes one **standalone HTML file** under `scenes/`, loaded as a
sub-composition by the Phase 4 root `index.html`. This step decides *what* each scene is and which
starting point it uses; Steps 3.3–3.4 build them from packets.

Every scene's body canvas, surfaces, text, controls, mockup chrome, screenshot framing, terminal
chrome, and clip matte must use the one confirmed-theme token set in `DESIGN.md`. Do not fall back
to a template's original light or dark defaults. Before the review checkpoint (Step 3.5), inspect
every authored scene and reject any opposite-theme canvas or surface.

**Check the shipped catalog before planning any hand-authored scene.** Invoke
`Skill(hyperframes-registry)` and read `REGISTRY_CATALOG` (path in `compat/ecosystem.md`) for the
exact block names `add` accepts — `app-showcase`, `ui-3d-reveal`, `data-chart`, `logo-outro`, the
six VFX blocks, and more cover most product-video archetypes. A tested block beats a hand-built
scene: install it with `npx hyperframes add <name>`, note on the frame which block it came from,
and let the packet carry the block plus this project's content instead of a from-scratch brief.
Hand-author only the gap. Wiring is `REGISTRY_BLOCKS`, worked through in `REGISTRY_ADD_EXAMPLE`;
Phase 4 Step 4.2 re-uses both.

**The spine of the video is the real product on screen.** Lead with capture-bearing
scenes that frame your Phase-2 screenshots/clips with depth; the text scenes (title,
stat, CTA) are *connective tissue between product beats*, not the substance. The Phase-2
captures are the **subject of the frame** — composite them on screen, do not merely sample
them for a palette. A film that is all text cards is the flat-slideshow failure mode
(`patterns/anti-slop.md` § The screenshot test); so is a film that buries the product
under decorative effects. Show the product, framed.

Plan these scene archetypes (adapt to mode — promo or showcase). Each row's **Copy from** file is
the starting point that ships in the packet unless Step 3.2 chose a registry block instead.

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
> film is still valid (mark it `product_surface: none` in the Creative Brief — see `SKILL.md`).
> The Phase-2 capture
> **checkpoint** stays warn-don't-block, but the Phase-3 **capture-coverage gate** BLOCKS for
> promo/showcase when `product_surface: ui` and no scene shows a real capture (it WARNS in
> tutorial) — see `SKILL.md` § Entry Modes → `jump`.

Premium screenshot presentation (browser/device framing, motivated camera moves,
scroll-within-frame, parallax depth, anchored callouts) lives in
`patterns/visual-patterns.md` § Screenshot Presentation and § Camera & Depth — read them before hand-authoring,
and prefer pulling an equivalent HyperFrames catalog block (`app-showcase`, `ui-3d-reveal`)
where one exists.

Each scene template must satisfy the list below. These are the skeleton's own constraints, so they
reach a builder through the packet's starting-point file rather than as separate instructions:

- Be a valid HyperFrames **sub-composition** — the root is a `<div data-composition-id="…" data-width="{W}" data-height="{H}">` wrapped in a `<template>` (per `hyperframes-core` → `SUB_COMPOSITIONS`, path in `compat/ecosystem.md`). Use the canvas dimensions chosen in Phase 1 (1920×1080, 1080×1920, 1080×1080, or 1080×1350). Sub-comps loaded via `data-composition-src` *require* this `<template>` wrapper; only the root `index.html` skips it.
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
        box-shadow:0 0 0 1px rgba(0,0,0,.06),3px 2px 6px rgba(0,0,0,.05),9px 40px 90px rgba(0,0,0,.18),inset 0 1px 0 rgba(255,255,255,.5)}
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

Motion recipes are `RULES_INDEX` and the ease register is `EASING_AND_STAGGER`;
`patterns/visual-patterns.md` carries only what those do not — the camera-on-a-still craft, the
legibility floor, the emphasis budget and the repo DON'Ts.
Scenes do not author their own outgoing flourish — the seam owns the exit. Transition selection: `patterns/transition-catalog.md`; the seam law itself is `SEAM_LAW` (`motion-doctrine`).

**Registry-first still applies to every skeleton on this page.** A hand-authored scene is the fallback, not the default — re-read the catalog check in Step 3.2 before typing a scene that a shipped block already does.

### Clip scene (real footage)

A clip scene is a normal sub-composition containing a `<video muted playsinline>` that carries
the explicit clip contract: `id`, `data-start="0"`, `data-duration`, `data-media-start`, and
`data-track-index="0"`. The runtime frame-syncs the video's `currentTime` to this scene's window
from those attributes (Wiring S — render-verified). Two values matter:

- `data-duration` = the scene loader's **full** `data-duration` from `index.html` — i.e.
  `(out-in)/speed` **plus the confirmed transition-duration extension** (Phase 4 Step 4.5 /
  `patterns/transition-catalog.md`). If the video's track ends at the nominal clip length,
  the runtime hides it (`visibility:hidden`) during the transition and the outgoing scene
  shows an empty frame.
- `data-media-start` = the frame's `clip_in` bullet (trim offset into the source, seconds;
  `0` if the whole clip is used). Without it the runtime plays from source `t=0`, the
  `clip_in` / `clip_out` trim is silently ignored, and the footage desyncs from Phase 5's
  clip-audio extraction (`CIN`).
- Set the video's `defaultPlaybackRate` and `playbackRate` to the frame's `speed` bullet before
  registering the timeline. Reject values outside **0.1–5.0** (the HyperFrames runtime's
  supported range). Scene duration and clip-own audio both use the same value; leaving the
  video at `1.0` desynchronizes footage whenever `speed != 1`.

**Do not omit the contract**: the runtime only seeks
videos that carry `data-start`, so a video without it is displayed but never time-synced. `lint`
errors on that case (`media_missing_data_start`, `media_missing_id`) and `check` skips the browser
when lint errors — so the *bare* video is caught. The dangerous case is the partly wired one: no
lint rule covers `data-media-start` or a media element's `data-track-index`, so a video with an id
and a start but the wrong offset plays the wrong footage, or another scene's, with every gate
green. And **never animate the
`<video>` dimensions** — wrap it in a non-timed `.clip-frame` div and animate the wrapper. Copy
`templates/scene-clip.html` as the starting point (`templates/scene-terminal-clip.html` for
asciinema/agg terminal footage).

**Mandatory brand treatments** (so footage reads premium, not raw): device/browser frame +
drop shadow, a vignette toward the brand canvas, a hidden OS cursor replaced by a brand-styled
pointer with a click pulse, and a color-grade toward the active design system's tokens. The
`<video>` stays muted; clip-own audio, if enabled, is mixed separately in Phase 5 Step 5.3a.
When the packet binds a `<clip>.replay.json` sidecar and `replay_pointer:` is `branded`, the
brand pointer's travel and click pulses follow the sidecar's **pointer track** — each entry's
clip-local timecode and target bounding box (scaled from the recorded viewport to the scene
canvas), eased with the track's named easing — never an invented path; replay footage itself is
pointer-free (`SCREENCAST_POINTER_ABSENCE`). `replay_pointer: none` drops the pointer overlay on
replayed clips — the user's per-run choice (ADR-001, via Phase 2 Step 2.1b).

- **Tutorial mode:** layer a Step-Label / Chapter overlay (`patterns/visual-patterns.md` § Step Label / Chapter Overlay) so each instructional scene shows `Step N of M` + chapter title, taken verbatim from that frame's `step_label` and `chapter` bullets — never re-derived from the frame number, which counts the cold open (spec §7.2c).

### Caption track for footage scenes (tutorial mode)

When content-mode is `tutorial`, author one caption sub-comp per footage scene from the
Phase-5 `transcript.json` (word-level), then wire it over the scene window in Phase 4.
Mechanism per `media-use` → `CAPTIONS_AUTHORING` (path in `compat/ecosystem.md`) — invoke `Skill(media-use)` and read it. Skeleton
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

Positioning (per the same `media-use` → `CAPTIONS_AUTHORING`): bottom 80–120px, `position:absolute; overflow:visible`,
full-width centered container (NOT `left:50%;translateX(-50%)`). Text ≥24px, high contrast.
Run the `[caption-lint]` self-check before `window.__timelines[id] = tl`.

## Step 3.3: Assemble one frame packet per scene

The director keys Phase 1 wrote onto each frame become **build input** here. A scene is built from a
**packet** — never from this workflow, and never from a summary of the storyboard.

A packet is **ephemeral**: assembled at dispatch time, regenerated on every run, written to a
scratch path and never committed. It contains exactly five things, and a builder that has to
resolve a citation itself has been handed the wrong packet.

| # | What goes in | Where it comes from |
|---|---|---|
| 1 | that ONE frame's storyboard block, **verbatim**, including every director key | the `storyboard --json` payload read at the top of this phase — official fields plus the preserved `extra` bullets, in the frame's own order |
| 2 | the project's design spec | `DESIGN.md` from Step 3.1, inlined whole |
| 3 | the **bodies** of the upstream recipes the frame cites | read from the installed skill *at this moment* and pasted in: the `blueprint:` id resolved through `BLUEPRINT_INDEX`, each `motion:` name through `RULES_INDEX`, plus the adapter contract when `runtime:` names a non-default runtime (the Contract column of `reasoning/capability-catalog.md` says which one), followed by this skill's `sub-agents/non-default-runtime-rider.md` — labelled as a local narrowing constraint, so a reader can tell which half upstream owns |
| 4 | the scene-builder role | `FRAME_WORKER_CORE`, read from the installed skill, followed by this skill's `sub-agents/scene-builder-delta.md` — core first, delta second, read as one role. **Once per worker, not once per packet** — see Step 3.4 |
| 5 | canvas size, the captions flag, and the exact paths of any bound capture artifacts | the Phase-1 canvas dimensions; the frame's `captions:` bullet; the frame's `screenshot:` / `clip:` bullets, as project-relative paths — plus, when the clip was cut from a recorded flow, its `<clip>.replay.json` sidecar path and the frontmatter `replay_pointer:` choice (the sidecar is a capture artifact bound by path, not a sixth item) |

Plus the starting point Step 3.2 chose for that archetype — the copy-ready `templates/scene-*.html`
file, or the block already installed from the registry.

**Inline, never restate.** Item 3 is a mechanical copy of upstream text into a throwaway packet, and
that is the only thing that makes it legal: this repo does not become the author of record for
upstream mechanism text. Paste the bodies in at dispatch time and let them die with the run. Do not
paraphrase, do not summarize, and never write a copy into a committed file. A cited name that
resolves to nothing is a **Phase-1 defect** — send the frame back rather than dispatching a builder
who will guess a motion from the spelling of its name.

**What a packet must NOT carry.** No `reasoning/` file, no `grammar/` file, no other frame's block,
and no film-wide storyboard state. Those produced the director keys; the keys *are* the conclusion,
and shipping the derivation alongside them is what makes builder context unbounded.

## Step 3.4: Dispatch — inline for a short film, fan out only past it

Fan-out pays only at scale, and the measurement behind that is `DISPATCH_ECONOMICS` — read it
there. It is not restated here, and the numbers are deliberately absent: if upstream re-measures,
a copy in this file becomes wrong silently, which is exactly the failure ADR-002 exists to stop.
Packet assembly (Step 3.3) happens either way — it is what turns the director keys into
build input. Only the dispatch differs.

| Frames to build | How |
|---|---|
| up to ~6 short frames | **Build them yourself, in sequence**, reading each frame's packet as you start its scene. Faster than fanning out, and every rule below still binds. |
| more than ~6 | **Fan out**: give each worker **2–3 frames**, never one, and start **all** workers in a single wave. |

**Send the role once per worker, not once per packet.** Packet item 4 is the same ~29 KB for every
frame, so a worker holding three packets receives three identical copies of it — on an eight-frame
film that is eight copies where three would do, and item 4 is the largest single share of all
packet bytes. Give a worker the role once, then its 2–3 frame packets; each packet still *is* the
five items, and item 4 is satisfied by the role that worker already holds. Nothing else dedupes:
items 1, 3 and 5 differ per frame by definition, and item 2 is the same `DESIGN.md` but is small.
Building inline pays it once for the whole phase, which is why this only matters past the
fan-out threshold.

When you fan out, hold the contract exactly:

- A worker receives its packets and nothing else, and returns exactly **one scene HTML file per
  packet**, at the `src` path that packet names. It runs no CLI, edits no storyboard, and touches
  no other frame.
- **At most one retry per frame, and only with a concrete finding** — a missing or malformed output
  file, a bound capture that was not composited, or specific per-scene feedback from the Step 3.5
  review. "Make it better" is not a finding; fix the packet instead. A frame that fails twice comes
  back to you to build inline.
- Builders cannot meaningfully lint or check their own output: those gates operate on the
  **assembled project**, which does not exist until Phase 4, so a builder running them would read
  other files and come back falsely green. Phase 4 runs the gates for real; a scene that fails
  there returns to Phase 3 (Phase 4 Step 4.6) with a finding a retry packet can carry.
- Dispatch is named as an **action**, not as one runtime's tool identifier. Resolve the runtime's
  delegation capability the way `SKILL.md` § Runtime Compatibility resolves a question prompt or a
  skill load; where a runtime exposes none, build inline regardless of frame count.

## Step 3.5: Collect the scenes, review, advance status

Preview and the mechanical gates run in Phase 4. A scene file is a `<template>`-wrapped
sub-composition — the HyperFrames runtime clones and drives it, so it cannot be previewed
standalone — and the CLI gates take a project **directory** that resolves `index.html`, which does
not exist until Phase 4:

- `npx hyperframes preview .` opens the studio, which lists `main` **plus every scene composition individually** for scrubbing.
- `npx hyperframes lint .` is the fast static check while iterating; `npx hyperframes check . --samples 10` is the required gate on the assembled project.

So verify by reading, before the checkpoint. Every collected scene must:

- Exist at the `src` path its frame names, wrapped in `<template>`, with a `data-composition-id`
  matching what the packet specified and one paused timeline registered under that same id.
- Composite the capture its frame binds. **Capture-coverage gate:** for promo/showcase with
  `product_surface: ui`, no scene showing a real screenshot or clip BLOCKS this phase (it WARNS in
  tutorial mode) — and a scene that swapped its bound capture for an invented mock fails the same
  way, because a plausible redraw is exactly what the gate exists to catch.
- Carry no invented number, metric, or product string — a value the packet did not supply is a
  build error to fix, not a figure to keep.
- Avoid the three failure modes Phase 4's gates catch: overlapping elements at rest (`check` flags
  container/text overflow), text contrast below WCAG AA (`check` runs a contrast audit), and
  animations that imply an exit (Phase 4 transitions own the exit — see DON'Ts in `SKILL.md`).

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

### Advance each built frame's `status`

Once the user answers **Looks great**, every frame whose scene file this phase produced exists with
its motion done, so advance that frame's `status` bullet from `outline` to `animated` — the rung the
official format uses for a frame that is built and animated. This is the one write this phase makes
into the user's own artifact, so it is narrow:

- **A targeted edit to that single line, never a regenerate.** Rewriting the file would reorder
  every frame's bullets; only the `status:` line changes. Never reflow other bullets, reorder
  frames, or touch the prose.
- Only on a storyboard the validator reports as `format: official`. Skip the update entirely on a
  legacy-shape file; injecting official bullets into one is a migration, and migrations are
  consent-gated.
- Only for frames whose scene file actually landed in this phase — collected, verified, and
  accepted. Leave every other frame at the value it already carries, and never mark a frame
  `animated` to make the board look finished.

The official ladder has a middle rung, `built` (layout confirmed, motion not yet added). **This
pipeline does not drive it**: a scene builder lays a scene out and animates it in the same pass, so
a frame here is either still planned or finished.

## Output

- `DESIGN.md` — design contract (palette, typography, shape, motion defaults)
- `scenes/*.html` — brand-matched HyperFrames scene templates, one per storyboard frame
- `scenes/assets/` — any decorative assets (icons, brand marks) referenced by templates
- `storyboard.md` — unchanged except for the `status` line of each frame built here

Frame packets are **not** an output. They are scratch, regenerated on every run, and nothing
downstream may read one: a packet that survives the run is a committed restatement of upstream text
by another name.

Any Phase-2 artifacts already live at their storyboard-bound paths under `public/screenshots/`,
`public/clips/`, or `scenes/`. An intentional no-product film whose frontmatter says
`capture_plan: none` has no Phase-2 directory requirement.

## Checkpoint

With the scenes accepted and each built frame's `status` advanced (Step 3.5), stamp Phase 3:

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" stamp phase-3
```

Do not advance on a nonzero exit.

> "Design contract and [N] scene templates ready. Palette + typography locked in `DESIGN.md`. Scenes are verified in Phase 4 — `preview .` lists each one individually for scrubbing and `lint`/`check .` run on the assembled composition.
>
> Ready to move to Phase 4: Composition assembly?"

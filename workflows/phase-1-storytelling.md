# Phase 1: Storytelling

Build the narrative structure and visual plan. Reads `context.md` from Phase 0.

## Step 1.1: Duration & Theme

```json
{
  "questions": [
    {
      "question": "How long should the video be?",
      "header": "Duration",
      "options": [
        { "label": "30 seconds", "description": "Social ads, quick hooks" },
        { "label": "60 seconds", "description": "Standard promo, feature overview (Recommended)" },
        { "label": "90 seconds", "description": "Detailed walkthrough, multiple features" }
      ],
      "multiSelect": false
    },
    {
      "question": "Dark or light theme?",
      "header": "Theme",
      "options": [
        { "label": "Light mode", "description": "Clean, bright, professional" },
        { "label": "Dark mode", "description": "Modern, bold, dramatic" }
      ],
      "multiSelect": false
    },
    {
      "question": "What aspect ratio and canvas size?",
      "header": "Aspect",
      "options": [
        { "label": "16:9 — 1920×1080", "description": "Standard horizontal (YouTube, web, embeds) — Recommended for promos" },
        { "label": "9:16 — 1080×1920", "description": "Vertical for TikTok / Reels / Shorts" },
        { "label": "1:1 — 1080×1080", "description": "Square for Instagram feed / LinkedIn carousels" },
        { "label": "4:5 — 1080×1350", "description": "Portrait for Instagram feed (taller than 1:1)" }
      ],
      "multiSelect": false
    }
  ]
}
```

Record the choice in `project-plan.md`. Phase 3 scene templates and the Phase 4 root composition will use these dimensions for their `data-width` / `data-height`. Once chosen, the canvas size is locked — scene templates won't reflow gracefully across aspect ratios.

## Step 1.2: Visual Identity (3 strategies)

Three ways to lock in the visual identity. Pick the most specific one that fits — each is faster than the next.

```json
{
  "questions": [{
    "question": "How should the visual identity be set?",
    "header": "Identity",
    "options": [
      { "label": "Use a curated design system (fastest)", "description": "Pick a known brand: Stripe, Linear, Apple, Notion, Vercel, Airbnb, GitHub, Cal, Arc, Bento. Skips brand extraction entirely; Phase 3 copies design-systems/<name>/DESIGN.md straight into the project. Best when the user says 'make it look like X'." },
      { "label": "Pick a HyperFrames named style (medium)", "description": "Pick from 8 styles: Swiss Pulse, Velvet Standard, Deconstructed, Maximalist Type, Data Drift, Soft Signal, Folk Frequency, Shadow Cut. Phase 3 seeds the project's DESIGN.md from the named style; still allows minor screenshot-based tuning." },
      { "label": "Derive from screenshots (default)", "description": "Phase 3 extracts colors, typography, and shape language from the captured app screenshots. Best when the user wants an identity that matches their actual product." }
    ],
    "multiSelect": false
  }]
}
```

If `Product surface: none`, omit **Derive from screenshots** because Phase 2 may be skipped;
offer only the curated design-system and HyperFrames named-style paths. Do not select a
screenshot-derived identity when no screenshot capture is planned.

### If "curated design system" was picked

Ask which one:

```json
{
  "questions": [{
    "question": "Which design system?",
    "header": "System",
    "options": [
      { "label": "Stripe", "description": "Premium fintech — sohne-var weight 300, blue-tinted shadows, deep navy. Payments / fintech / dev tools." },
      { "label": "Linear", "description": "Engineered minimalism — Inter, restrained accent, glass surfaces. Issue trackers, SaaS, productivity." },
      { "label": "Apple", "description": "Quiet authority — SF Pro, generous whitespace, neutral palette. Hardware, consumer launches." },
      { "label": "Notion", "description": "Editorial-software — soft warmth, hand-drawn touches, calm hierarchy. Productivity, docs, content tools." },
      { "label": "Vercel", "description": "Sharp black-on-white minimalism — Geist, dramatic monochrome. Dev infra, deploy platforms." },
      { "label": "Airbnb", "description": "Warm rounded — Cereal, generous radii, soft shadows. Travel, hospitality, consumer marketplaces." },
      { "label": "GitHub", "description": "Functional dark mode — high-contrast neutrals, monospace anchors. Code platforms, dev tools." },
      { "label": "Cal.com", "description": "Friendly OSS clarity — minimal palette, approachable type. Scheduling, OSS tools." },
      { "label": "Arc", "description": "Playful chrome — gradients, vivid colour. Browsers, consumer SaaS." },
      { "label": "Bento", "description": "Playful link-in-bio — bold colour blocks. Social, creator tools." }
    ],
    "multiSelect": false
  }]
}
```

Record `design_system: <slug>` in `project-plan.md` (slugs: `stripe`, `linear-app`, `apple`, `notion`, `vercel`, `airbnb`, `github`, `cal`, `arc`, `bento`). Phase 3 will copy `design-systems/<slug>/DESIGN.md` to the project root as `DESIGN.md`. See `design-systems/README.md` for catalog details and how to add more.

### If "HyperFrames named style" was picked

Ask which one:

```json
{
  "questions": [{
    "question": "Which HyperFrames named style?",
    "header": "Style",
    "options": [
      { "label": "Swiss Pulse", "description": "Clinical, precise — SaaS, dev tools, dashboards. Black + white + one accent. Helvetica/Inter. Cinematic Zoom transitions." },
      { "label": "Velvet Standard", "description": "Premium, timeless — luxury, enterprise, keynotes. Cross-Warp Morph transitions." },
      { "label": "Deconstructed", "description": "Industrial, raw — tech launches, security, punk. Glitch / Whip-Pan transitions." },
      { "label": "Maximalist Type", "description": "Loud, kinetic — big announcements, launches. Ridged Burn transitions." },
      { "label": "Data Drift", "description": "Futuristic, immersive — AI, ML, cutting-edge tech. Gravitational Lens / Domain Warp." },
      { "label": "Soft Signal", "description": "Intimate, warm — wellness, personal stories, brand. Thermal Distortion." },
      { "label": "Folk Frequency", "description": "Cultural, vivid — consumer apps, food, communities. Swirl Vortex / Ripple Waves." },
      { "label": "Shadow Cut", "description": "Dark, cinematic — dramatic reveals, security, exposé. Domain Warp." }
    ],
    "multiSelect": false
  }]
}
```

Record `style: <name>` in `project-plan.md`. Full descriptions live in the `hyperframes` skill at `visual-styles.md` (palette, fonts, motion feel, primary shader transition). For palette pairing see `hyperframes/palettes/*.md`.

### If "derive from screenshots" was picked

No follow-up. Phase 3 will run the full extraction workflow.

## Step 1.3: Voice Selection

```json
{
  "questions": [{
    "question": "What voice for the voiceover?",
    "header": "Voice",
    "options": [
      { "label": "Matilda", "description": "Warm, confident female — polished (Recommended)" },
      { "label": "Rachel", "description": "Calm, clear female — authoritative" },
      { "label": "Daniel", "description": "Authoritative male — broadcast tone" },
      { "label": "Josh", "description": "Friendly, conversational male" }
    ],
    "multiSelect": false
  }]
}
```

## Step 1.4: Narrative Structure

**The real product on screen is the spine.** In every mode below, the backbone of the video
is real captures of the product (Phase-2 screenshots/clips) framed with depth; the text / stat
/ CTA beats are *connective tissue between product beats*, not the substance. Build the
structure so the product carries the story — but do **not** swing to the opposite failure mode
of a uniform product-card slideshow: keep at least one unconventional beat and **vary scene
durations** (equal-length cards read as a slideshow — see `patterns/anti-slop.md`). The one
exception is a no-product / abstract film (`product_surface: none`), where text carries it.

Based on mode:

### Promo Mode Structure
```
Scene 1: HOOK (0-5s)        — Attention-grabbing statement + key stat
Scene 2: PAIN (5-15s)       — 2-3 pain points the audience relates to
Scene 3: SOLUTION (15-20s)  — Product reveal + one-line value prop
Scene 4: FEATURES (20-45s)  — 3-5 feature highlights with UI screenshots
Scene 5: RESULTS (45-52s)   — Stats, outcomes, social proof
Scene 6: CTA (52-60s)       — Call to action + branding
```

### Showcase Mode Structure
```
Scene 1: INTRO (0-8s)       — Product name + what it is + hero screenshot
Scene 2: WALKTHROUGH (8-35s) — Feature-by-feature tour with screenshots
Scene 3: HIGHLIGHTS (35-50s) — Design details, UX choices, tech stack
Scene 4: CLOSER (50-60s)    — Key takeaway + links/contact
```

### Tutorial Mode Structure
```
Scene 0: COLD OPEN (0-6s)   — Show the finished payoff FIRST (the end result the viewer will achieve)
Scene 1: STEP 1 (6-Xs)      — Chapter "Step 1 of M" — one concrete goal; clip when capture is available
Scene 2: STEP 2 (...)       — Chapter "Step 2 of M" — next goal in task order
Scene N: STEP M (...)       — Chapter "Step M of M" — final goal; lands back on the payoff
Scene N+1: RECAP / NEXT     — Summarize the steps + where to go next (docs, install, repo)
```

Chapters are **task-ordered**: each scene is one step with a single concrete goal, labeled
on-screen "Step N of M" (from the storyboard `Step label:`/`Chapter:` fields — see Phase 3/4).
**Cold-open on the payoff** (spec §7.2d): scene 0 is a ~2–4s teaser of the finished end-state
so the viewer knows what they're building toward. Tutorial mode **prefers clip scenes**
(`Capture: screencast`/`terminal`) but does **not require** them — without capture, steps fall
back to stills and the step labels + captions carry the narrative (spec §7.3). Break any
continuous run >~90s with an authored recap beat (Phase 4) before the next step.

Adjust durations based on selected total length.

## Step 1.5: Transition Selection

```json
{
  "questions": [
    {
      "question": "What transition between main sections?",
      "header": "Sections",
      "options": [
        { "label": "Metallic swoosh", "description": "Diagonal gradient shine sweeps across" },
        { "label": "Zoom through", "description": "Scale up and push through" },
        { "label": "Fade", "description": "Classic smooth crossfade" },
        { "label": "Slide from bottom", "description": "Next scene pushes up" }
      ],
      "multiSelect": false
    },
    {
      "question": "Transition speed?",
      "header": "Speed",
      "options": [
        { "label": "Quick (0.4s)", "description": "Snappy, energetic" },
        { "label": "Medium (0.7s)", "description": "Balanced, professional" },
        { "label": "Slow (1.2s)", "description": "Dramatic, cinematic" }
      ],
      "multiSelect": false
    }
  ]
}
```

**If "Metallic swoosh" selected:** Read [../patterns/metallic-swoosh.md](../patterns/metallic-swoosh.md) before implementing. Uses crossfade + shine overlay — do NOT use clipPath.

## Step 1.6: Build Storyboard

For each scene, define:
- **Timecode** — start/end in seconds
- **Visual** — what appears on screen (screenshot reference, text, stats, mockup)
- **Voiceover** — what's being said (matched to visual content)
- **Animation** — how elements enter/exit
- **Transition** — how this scene connects to the next

Generate `storyboard.md` from `templates/storyboard.md`.

### Capture type per scene (optional)

Each product/spine scene defaults to a still **screenshot**. Connective title/text/CTA scenes
use `Capture: none`. A scene may instead be a **clip** (real motion footage) by setting
`Capture:` to `screencast` (web app, Phase 2),
`terminal` (CLI tool — an authored animated terminal from real command output),
`terminal-clip` (CLI tool — a **real** recording: Phase 2 runs the command
autonomously via asciinema + agg; requires a `Command:` field with the exact
shell command and honors `Record timeout:`, default scene duration + 2s — see
`patterns/cli-terminal-capture.md`), or `supplied` (you provide the file).
Prefer `terminal-clip` over `terminal` when the command's real output matters
(deploys, test runs, scaffolding) — it degrades to the authored-terminal path
automatically if asciinema/agg aren't installed. Clip scenes use the clip
fields in the storyboard template (`Clip`, `Clip in/out`, `Speed`, `Captions`).
A clip scene's on-screen duration is the footage length (see Phase 4), so plan
the scene's slot around the real clip length. Clips are available in **all**
content modes; in `promo` they must be device-framed accents (Phase 4).

## Step 1.7: Capture Plan

Based on the storyboard, list every artifact Phase 2 must produce. **Bind each capture to a
scene:** every item must map to a storyboard scene that uses it (`Screenshot:` / `Clip:`), and
every spine scene must name its artifact. Captures planned but never placed on screen are exactly
the leak that ships a flat, text-only video.

For web screenshot/screencast scenes, define:
- URL or route to navigate to
- Specific element/state to capture (e.g., "dashboard with sample data", "modal open")
- Device viewport — match the chosen canvas: desktop 1920×1080 for 16:9; mobile 390×844 for 9:16; square viewport 1080×1080 for 1:1; mobile 390×488 (or desktop crop) for 4:5

For terminal scenes, define the exact command and whether the accepted output is an authored
terminal scene or a `terminal-clip`. For supplied footage, define the exact destination path.
When `Product surface: none` and no scene requests any capture, explicitly record
`Capture plan: none — skip Phase 2` rather than inventing an app URL.

## Checkpoint

> "Storyboard complete. [N] scenes, [duration]s total, [M] capture artifacts planned.
>
> [If M > 0: Ready to move to Phase 2: Capture?]
> [If M = 0 and Product surface is none: Capture is intentionally skipped; ready for Phase 3: Design?]"

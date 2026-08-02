# Phase 1: Storytelling

Build the narrative structure and visual plan. Reads `context.md` from Phase 0.

## Creative brief contract — choices belong to the user

The agent owns **craft**: narrative structure, motion choreography, easing, composition polish,
and implementation details. The user owns the **creative brief**. Phase-0 research may justify a
recommendation, but it must never infer, silently default, preselect, or answer a brief question.
If recommending an option, put `Recommended - <reason>` in that option's label or description;
recommendations are visible guidance, never a selection.

Surface and record every lever in the exact `project-plan.md` Creative Brief table:

| Lever | Creative Brief field(s) | Where it is explicitly chosen |
|---|---|---|
| Mode | `mode` | Entry prompt in `SKILL.md` |
| Product surface | `product_surface` | Entry prompt in `SKILL.md` |
| Duration | `duration` | Step 1.1 |
| Theme | `theme` | Step 1.1 |
| Aspect ratio | `aspect_ratio` | Step 1.1 |
| Identity / design system | `identity_strategy`, `identity_choice` | Step 1.2 |
| Voice | `voice` | Step 1.3 |
| Transition style | `transition_style` | Step 1.5 |
| Transition speed | `transition_speed` | Step 1.5 |
| Music strategy | `music_strategy` | Step 1.5 |
| Final exact music track | `final_music_track` | Phase 5, after candidates are known |

Mode and product surface were already presented before Phase 0. Verify that their explicit answers
are in the table. If either is missing or still a placeholder (including on `continue`/`jump`),
present that entry prompt again; do not reconstruct the answer from `context.md`.

## Step 1.1: Duration & Theme

```json
{
  "questions": [
    {
      "question": "How long should the video be?",
      "header": "Duration",
      "options": [
        { "label": "30 seconds", "description": "Social ads, quick hooks" },
        { "label": "60 seconds", "description": "Recommended for a standard promo: enough room for a feature overview" },
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

Record `duration`, `theme`, and `aspect_ratio` in the Creative Brief table. Phase 3 scene
templates and the Phase 4 root composition use these dimensions for `data-width` / `data-height`.
Once chosen, the canvas size is locked; changing it later stales every Phase 1–5 stamp.

## Step 1.2: Visual Identity

This is the video's most visible user-owned choice. Always show the strategy prompt. Do not turn
"developer tool" into an unasked Vercel choice or turn the app screenshots into an unasked derived
identity. A recommendation may be shown in an option description with its reason.

```json
{
  "questions": [{
    "question": "How should the visual identity be set?",
    "header": "Identity",
    "options": [
      { "label": "Curated design system", "description": "Choose one of 10 documented brand systems; Phase 3 copies its video-focused DESIGN.md." },
      { "label": "HyperFrames named style", "description": "Choose one of 8 visual/motion styles; Phase 3 seeds DESIGN.md from that style." },
      { "label": "Derive from captured screenshots", "description": "Match the product's existing colors, typography, and shape language." },
      { "label": "Custom identity", "description": "Provide a custom DESIGN.md, brand guide, or named direction." }
    ],
    "multiSelect": false
  }]
}
```

If `product_surface: none`, omit **Derive from screenshots** because Phase 2 may be skipped;
offer the other three paths. Do not select a screenshot-derived identity when no screenshot
capture is planned.

### If "curated design system" was picked

First ask for a family. This keeps the native prompt within Claude's four-option limit while
retaining all 10 systems:

```json
{
  "questions": [{
    "question": "Which design-system family should we explore?",
    "header": "System group",
    "options": [
      { "label": "Developer and fintech", "description": "Stripe, Linear, Vercel, or GitHub." },
      { "label": "Editorial and utility", "description": "Apple, Notion, or Cal.com." },
      { "label": "Consumer and playful", "description": "Airbnb, Arc, or Bento." }
    ],
    "multiSelect": false
  }]
}
```

Then present only the second-level prompt for the chosen family.

#### Developer and fintech

```json
{
  "questions": [{
    "question": "Which developer or fintech design system?",
    "header": "System",
    "options": [
      { "label": "Stripe", "description": "Premium fintech: light typography, blue-tinted shadows, deep navy." },
      { "label": "Linear", "description": "Dark-only engineered minimalism: restrained accents and glass surfaces." },
      { "label": "Vercel", "description": "Light-only sharp monochrome minimalism for developer infrastructure." },
      { "label": "GitHub", "description": "Functional high-contrast neutrals with monospace anchors." }
    ],
    "multiSelect": false
  }]
}
```

#### Editorial and utility

```json
{
  "questions": [{
    "question": "Which editorial or utility design system?",
    "header": "System",
    "options": [
      { "label": "Apple", "description": "Quiet authority, generous whitespace, and neutral surfaces." },
      { "label": "Notion", "description": "Warm editorial software with calm hierarchy." },
      { "label": "Cal.com", "description": "Light-only open-source clarity with approachable type." }
    ],
    "multiSelect": false
  }]
}
```

#### Consumer and playful

```json
{
  "questions": [{
    "question": "Which consumer or playful design system?",
    "header": "System",
    "options": [
      { "label": "Airbnb", "description": "Light-only rounded forms and soft marketplace depth." },
      { "label": "Arc", "description": "Playful chrome, vivid color, and expressive gradients." },
      { "label": "Bento", "description": "Light-only cream canvas and bold creator-focused color blocks." }
    ],
    "multiSelect": false
  }]
}
```

Record `identity_strategy: design-system` and `identity_choice: <slug>` in the Creative Brief.
Slugs are `stripe`, `linear-app`, `apple`, `notion`, `vercel`, `airbnb`, `github`, `cal`, `arc`,
and `bento`. Phase 3 copies `design-systems/<slug>/DESIGN.md` to the project as `DESIGN.md`.

Theme is authoritative, not a suggestion. Before the brief summary, enforce the shipped systems'
theme support:

| Theme support | Systems |
|---|---|
| Dark only | `linear-app` |
| Light only | `vercel`, `airbnb`, `cal`, `bento` |
| Light or dark | `stripe`, `apple`, `notion`, `github`, `arc` |

If the chosen system and theme conflict, return to the theme or identity prompt and let the user
change one. Never invert a brand palette or silently override the confirmed theme.

### If "HyperFrames named style" was picked

First ask for a style family:

```json
{
  "questions": [{
    "question": "Which HyperFrames style family fits the intended tone?",
    "header": "Style family",
    "options": [
      { "label": "Precise and premium", "description": "Swiss Pulse or Velvet Standard." },
      { "label": "Bold and experimental", "description": "Deconstructed or Maximalist Type." },
      { "label": "Ambient and futuristic", "description": "Data Drift or Soft Signal." },
      { "label": "Cultural and cinematic", "description": "Folk Frequency or Shadow Cut." }
    ],
    "multiSelect": false
  }]
}
```

Then present only the chosen family's second-level prompt.

#### Precise and premium

```json
{
  "questions": [{
    "question": "Which precise or premium style?",
    "header": "Style",
    "options": [
      { "label": "Swiss Pulse", "description": "Clinical SaaS precision with cinematic zoom transitions." },
      { "label": "Velvet Standard", "description": "Premium, timeless keynote energy with morph transitions." }
    ],
    "multiSelect": false
  }]
}
```

#### Bold and experimental

```json
{
  "questions": [{
    "question": "Which bold or experimental style?",
    "header": "Style",
    "options": [
      { "label": "Deconstructed", "description": "Industrial and raw with glitch or whip-pan energy." },
      { "label": "Maximalist Type", "description": "Loud kinetic typography for major announcements." }
    ],
    "multiSelect": false
  }]
}
```

#### Ambient and futuristic

```json
{
  "questions": [{
    "question": "Which ambient or futuristic style?",
    "header": "Style",
    "options": [
      { "label": "Data Drift", "description": "Immersive AI/ML atmosphere with lens and domain-warp motion." },
      { "label": "Soft Signal", "description": "Warm intimacy with restrained thermal-distortion motion." }
    ],
    "multiSelect": false
  }]
}
```

#### Cultural and cinematic

```json
{
  "questions": [{
    "question": "Which cultural or cinematic style?",
    "header": "Style",
    "options": [
      { "label": "Folk Frequency", "description": "Vivid cultural energy with ripple and vortex motion." },
      { "label": "Shadow Cut", "description": "Dark cinematic reveals with domain-warp motion." }
    ],
    "multiSelect": false
  }]
}
```

Record `identity_strategy: hyperframes-style` and the exact style name in `identity_choice`.
Full descriptions live in the `hyperframes-creative` skill under `VISUAL_STYLES` (path registered
in `compat/ecosystem.md`).

### If "derive from screenshots" was picked

Record `identity_strategy: screenshots` and `identity_choice: captured-screenshots`. Phase 3 runs
the full extraction workflow.

### If "custom identity" was picked

Ask the user for the exact custom identity or `DESIGN.md` source. Record
`identity_strategy: custom` and a specific, non-placeholder `identity_choice`.

## Step 1.3: Voice Selection

Choose the provider first. Availability may shape a recommendation but never changes the answer:

```json
{
  "questions": [{
    "question": "Which voice provider should generate the confirmed voice?",
    "header": "Voice source",
    "options": [
      { "label": "ElevenLabs", "description": "Higher-quality hosted TTS; requires ELEVENLABS_API_KEY." },
      { "label": "Kokoro local", "description": "No API key; runs through HyperFrames TTS with a named Kokoro voice." }
    ],
    "multiSelect": false
  }]
}
```

If ElevenLabs was chosen, present:

```json
{
  "questions": [{
    "question": "Which ElevenLabs voice for the voiceover?",
    "header": "Voice",
    "options": [
      { "label": "Matilda", "description": "Recommended for polished promos: warm and confident." },
      { "label": "Rachel", "description": "Calm, clear female — authoritative" },
      { "label": "Daniel", "description": "Authoritative male — broadcast tone" },
      { "label": "Josh", "description": "Friendly, conversational male" }
    ],
    "multiSelect": false
  }]
}
```

The runtime's freeform/custom answer may supply another ElevenLabs name and voice ID. Record
`voice` as `elevenlabs:<name>:<voice-id>` (for example
`elevenlabs:Matilda:XrExE9yKIg1WjnnlVkGX`). If the API key is unavailable, stop and let the user
configure it or return to the provider prompt; never substitute Kokoro.

If Kokoro was chosen, present a starter set:

```json
{
  "questions": [{
    "question": "Which local Kokoro voice should narrate the video?",
    "header": "Voice",
    "options": [
      { "label": "Nova (af_nova)", "description": "Clear American female voice." },
      { "label": "Heart (af_heart)", "description": "Warm American female voice." },
      { "label": "George (bm_george)", "description": "Grounded British male voice." },
      { "label": "Browse exact ID", "description": "List all local voices, then choose an exact Kokoro ID." }
    ],
    "multiSelect": false
  }]
}
```

For **Browse exact ID**, run `npx hyperframes tts --list` and present its real results in pages of
at most three voices plus **More voices**. Record `voice` as `kokoro:<voice-id>` (for example
`kokoro:af_nova`). Never infer a voice from the product category, and never switch providers after
confirmation.

## Step 1.4: Narrative Structure

**The real product on screen is the spine.** In every mode below, the backbone of the video
is real captures of the product (Phase-2 screenshots/clips) framed with depth; the text / stat
/ CTA beats are *connective tissue between product beats*, not the substance. Build the
structure so the product carries the story — but do **not** swing to the opposite failure mode
of a uniform product-card slideshow: keep at least one unconventional beat and **vary scene
durations** (equal-length cards read as a slideshow — see `patterns/anti-slop.md`). The one
exception is a no-product / abstract film (`product_surface: none`), where text carries it.

Based on mode:

Beats are numbered as the storyboard numbers them: **frames are 1-based** (`## Frame 1`) while the
scene *files* they point at stay 0-based, so frame 1's `src` is `scenes/00-…`.

### Promo Mode Structure
```
Frame 1: HOOK (0-5s)        — Attention-grabbing statement + key stat
Frame 2: PAIN (5-15s)       — 2-3 pain points the audience relates to
Frame 3: SOLUTION (15-20s)  — Product reveal + one-line value prop
Frame 4: FEATURES (20-45s)  — 3-5 feature highlights with UI screenshots
Frame 5: RESULTS (45-52s)   — Stats, outcomes, social proof
Frame 6: CTA (52-60s)       — Call to action + branding
```

### Showcase Mode Structure
```
Frame 1: INTRO (0-8s)       — Product name + what it is + hero screenshot
Frame 2: WALKTHROUGH (8-35s) — Feature-by-feature tour with screenshots
Frame 3: HIGHLIGHTS (35-50s) — Design details, UX choices, tech stack
Frame 4: CLOSER (50-60s)    — Key takeaway + links/contact
```

### Tutorial Mode Structure
```
Frame 1: COLD OPEN (0-6s)   — Show the finished payoff FIRST (the end result the viewer will achieve)
Frame 2: STEP 1 (6-Xs)      — Chapter "Step 1 of M" — one concrete goal; clip when capture is available
Frame 3: STEP 2 (...)       — Chapter "Step 2 of M" — next goal in task order
Frame N: STEP M (...)       — Chapter "Step M of M" — final goal; lands back on the payoff
Frame N+1: RECAP / NEXT     — Summarize the steps + where to go next (docs, install, repo)
```

Chapters are **task-ordered**: each step frame has a single concrete goal, labeled on-screen
"Step N of M" (from the frame's `step_label` / `chapter` bullets — see Phase 3/4). The frame number
is **not** the step number: the cold open is frame 1, so step 1 lands on frame 2. `step_label`
carries the step count; never re-derive it from the heading.
**Cold-open on the payoff** (spec §7.2d): frame 1 is a ~2–4s teaser of the finished end-state
so the viewer knows what they're building toward. Tutorial mode **prefers clip frames**
(`capture: screencast`/`screen-recording`/`terminal-clip`) but does **not require** them — without capture, steps fall
back to stills and the step labels + captions carry the narrative (spec §7.3). Break any
continuous run >~90s with an authored recap beat (Phase 4) before the next step.

Adjust durations based on selected total length.

## Step 1.4a: Emotional Pacing

Phase 0 asked what the viewer should *feel* (Step 0.1, question 4). Until this step that answer was
collected and never used. Read it back from `context.md` and turn it into the film's **tone and
energy curve**; the curve is written to the storyboard frontmatter (`emotional_journey`) when the
storyboard is created in Step 1.6, so later phases read one authored arc instead of re-deriving
it. If `context.md` carries no explicit emotional-journey
answer, ask that Phase-0 question again and record the user's answer before continuing — never
infer the arc from product research.

Give every beat from Step 1.4 one `tone:` word drawn from that journey and one `energy:` value. The
curve is film-level: it starts where the journey starts, lands where it ends, and changes at least
once. A curve that never changes is the slideshow failure in another form.

| Source | Feeds | Then consumed by |
|---|---|---|
| the Phase-0 emotional journey in `context.md` | the storyboard's frontmatter `emotional_journey`, and each frame's `tone:` bullet | the emotional-arc-closure row of the budget table in `reasoning/scene-analysis.md` |
| the tone → energy defaults in `reasoning/scene-analysis.md` | each frame's `energy:` bullet | scene durations, camera pacing (`grammar/camera.md`), transition energy between adjacent frames |
| the music column of that same table | the Phase-5 music brief | track candidates, ducking, the final hit |

**The curve advises; it never answers a brief question.** `transition_style`, `transition_speed`,
and `music_strategy` remain the user's in Step 1.5. A derived curve may only shape a
`Recommended - <reason>` label on an option. It may never preselect one, and never skip a prompt.

## Step 1.4b: Scene Analysis

For each beat planned above, answer the twelve questions in `reasoning/scene-analysis.md` and write
the resulting **director keys** as ordinary `- key: value` bullets in that frame's metadata block in
Step 1.6 (`templates/storyboard.md` carries the key list and a filled example). That file owns the questions,
the closed key set, and every allowed value — read them there. Do not restate them here or in the
storyboard: two copies drift, and these keys are exactly what Phase 3 forwards to its scene
builders.

Three things this step must not get wrong:

- **Q1–Q10 are judgment; Q11 is a derivation.** A frame's `capabilities:` is the union of the tags
  declared by every grammar entry it cites in Q8–Q10 (`grammar/camera.md`, `grammar/metaphors.md`,
  `grammar/motion.md`), *starting from the baseline capability every scene implies* — that rule is
  owned and stated by `reasoning/capability-catalog.md`; a grammar row declares only what it adds
  beyond it, so an empty tag cell adds nothing and no frame's set is ever empty. Plus asset and
  subject realities, plus additions that each carry a stated reason on the frame. Never a taste call and never an invented tag — the vocabulary is owned by
  `reasoning/capability-catalog.md`, whose selection procedure then answers Q12.
- **Motion names are cited, never invented.** A `blueprint:` id resolves through `BLUEPRINT_INDEX`
  and `motion:` rule names through `RULES_INDEX` — backticked, no directory, no `.md`. A name in
  neither index is invalid: drop it, or map it to the nearest real entry and say so
  (`compat/ecosystem.md` § Citing upstream vocabulary).
- **Runtime is an outcome, not a wish.** Omit `runtime:` when the default serves the frame; whenever
  a non-default runtime was considered and not chosen, record `runtime_rejected: <runtime> — <reason>`.

A reviewer reading only the keys must be able to reconstruct why every visual choice exists. Where
the user explicitly directed a frame — an instruction, not a preference — state the tradeoff once,
comply, and record `user_directed: true`.

## Step 1.4c: Video-level Budget Check

Once every frame carries keys, check the film against the cognitive-load budget table in
`reasoning/scene-analysis.md`: hero beats, transitions, emphasis, marker highlight, density,
duration variance, metaphor consistency, and emotional-arc closure. **That table is the only place
those numbers live** — never copy one into this workflow, the storyboard, or a scene prompt.

Report the outcome as a short list: budget, verdict, and what changed to come back under it. Frames
carrying `user_directed: true` are exempt from the budgets but are still counted and shown, so the
user sees the choice was theirs and not the agent's. Re-run the transition and duration-variance
rows at the end of Step 1.6, once every frame's `duration` and `transition_in` exist — those two
rows read fields that do not exist yet at this point.

## Step 1.5: Transition and Music Strategy

This choice decides whether the film's boundaries can be verified at all, so disclose that with
the question rather than after it. `zoom-through` and `slide-from-bottom` are velocity-matched
cuts: each becomes a row in the Phase-4 seam ledger and is checked numerically by `SEAM_VERIFIER`.
`crossfade` and `metallic-swoosh` are dissolves; a dissolve cannot be a ledger row, so a film built
from them leaves that gate with nothing to check and it exits green regardless. Even under a cut
style the connective crossfades inside a section stay dissolves, so Phase 4 counts and reports the
unverified boundaries either way. Both are legitimate choices — say this once, then record
whatever the user picks (ADR-001).

```json
{
  "questions": [
    {
      "question": "What transition between main sections?",
      "header": "Sections",
      "options": [
        { "label": "Metallic swoosh", "description": "Diagonal gradient shine sweeps across. A dissolve — the Phase-4 seam gate cannot verify it." },
        { "label": "Zoom through", "description": "Scale up and push through. Recommended - a velocity-matched cut, which the Phase-4 seam gate verifies." },
        { "label": "Fade", "description": "Classic smooth crossfade. A dissolve — the Phase-4 seam gate cannot verify it." },
        { "label": "Slide from bottom", "description": "Next scene pushes up. Recommended - a velocity-matched cut, which the Phase-4 seam gate verifies." }
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

Record the stable slugs in the Creative Brief:

- Metallic swoosh → `transition_style: metallic-swoosh`
- Zoom through → `transition_style: zoom-through`
- Fade → `transition_style: crossfade`
- Slide from bottom → `transition_style: slide-from-bottom`
- Quick / Medium / Slow → `transition_speed: quick | medium | slow`

The duration mapping is stable and must be carried into every storyboard transition:
`quick → 0.4s`, `medium → 0.7s`, `slow → 1.2s`. The style choice applies at main section
boundaries; quiet transitions between beats inside the same section use `crossfade` at the same
confirmed duration. The storyboard records each boundary as `transition_in` on the frame it leads
*into* (Step 1.6), so the opening frame carries none and the closing frame is followed by no
boundary at all.

**If "Metallic swoosh" selected:** the look is a full-frame light overlay riding an incoming-only crossfade — the light family, implemented from `TRANSITION_FAMILIES`. See [../patterns/transition-catalog.md](../patterns/transition-catalog.md) and Phase 4 Step 4.5. Never a clipPath wipe ([../patterns/visual-patterns.md](../patterns/visual-patterns.md) § DON'Ts carries the why).

Choose the music acquisition strategy now. The exact track remains unselected until Phase 5 has
real candidates; selecting a strategy is not permission for the agent to pick a track.

```json
{
  "questions": [{
    "question": "How should Phase 5 source background music?",
    "header": "Music source",
    "options": [
      { "label": "A Freesound track I pick", "description": "You choose a CC0/CC-BY track and give me its URL; Phase 5 confirms that exact track before mixing." },
      { "label": "Let the media-use engine source it", "description": "The engine retrieves or generates a bed from the storyboard mood; Phase 5 still confirms the exact track and records its provenance before mixing. Needs the media-use skill installed." },
      { "label": "Use my audio file", "description": "I will provide a path; Phase 5 will confirm that exact file before mixing." },
      { "label": "No background music", "description": "Voiceover only; Phase 5 will still require an explicit no-music confirmation." }
    ],
    "multiSelect": false
  }]
}
```

Record `music_strategy: freesound | user-provided | none`. Leave `final_music_track` as its
placeholder until Phase 5.

### Confirm the complete story brief before storyboarding

Present one concise summary containing every story-owned field:

| Summary label | Creative Brief value |
|---|---|
| Mode | `mode` |
| Product surface | `product_surface` |
| Duration | `duration` |
| Theme | `theme` |
| Aspect | `aspect_ratio` |
| Identity | `identity_strategy` + `identity_choice` |
| Voice | `voice` |
| Transition style | `transition_style` |
| Transition speed | `transition_speed` |
| Music strategy | `music_strategy` |

Then require an explicit native confirmation:

```json
{
  "questions": [{
    "question": "Confirm this complete story brief before I create the storyboard?",
    "header": "Story brief",
    "options": [
      { "label": "Confirm story brief", "description": "Fingerprint these choices and proceed to storyboard creation." },
      { "label": "Change choices", "description": "Return to the relevant prompt; do not create the storyboard yet." }
    ],
    "multiSelect": false
  }]
}
```

If the user chooses **Change choices**, update the table, re-present the complete summary, and ask
again. Do not advance until the user chooses **Confirm story brief**. Then run the installed
validator (resolve `$SKILL_DIR` as described in `SKILL.md`):

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" confirm-story --json
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" require story
```

Any nonzero result blocks storyboard creation. Repair the named missing/placeholder field or
malformed table and present the confirmation again. Confirmation writes
`.hve/brief-state.json` atomically; it does not delete stale artifacts.

## Step 1.6: Build Storyboard

Only begin this step after `require story` passes for the current fingerprint.

Generate `storyboard.md` from `templates/storyboard.md`. It is written in the **official
HyperFrames storyboard shape** (`STORYBOARD_FORMAT`): YAML frontmatter first, then one
`## Frame N — Title` section per frame, its `- key: value` metadata bullets in a single contiguous
block directly under the heading, and free prose below them. The template owns the skeleton, the
key tables, and a filled example — read it there rather than restating any of it here. Everything
the official key set has no home for (the capture bindings, the clip fields, the director keys)
rides as an extra bullet, and the parser preserves those verbatim under the frame's `extra`; that
is the whole reason this shape can carry our keys at all.

For each frame, write:

| What | Bullet |
|---|---|
| Lifecycle | `status: outline` — Phase 1 plans, it does not build; Phase 3 advances this |
| Scene file | `src: scenes/{NN}-{slug}.html` |
| Length | `duration: {n}s` — **authoritative**; add `window: {start}s → {end}s` as a reading aid only |
| Seam into this frame | `transition_in` + `transition_speed` (see below) |
| Board caption | `scene` — one line, what a reviewer sees on the contact sheet |
| Narration | `voiceover` — the exact line to speak, one line, in quotes |
| Poster | `poster: {n}s` — past the intro animation |
| Capture binding | `screenshot` / `clip`, plus the capture keys below |
| Director keys | the keys derived in Step 1.4b, as ordinary bullets in the same block |
| Visual + choreography | the free prose under the bullets: what is on screen, how elements enter, why the beat earns its seconds |

Exit motion belongs to the *next* frame's seam, so never write one into a frame's prose — the
closing frame is the only exception.

**Transitions invert under this shape.** The official key is `transition_in` — the seam **into** a
frame — so the boundary between frames N and N+1 is recorded on frame **N+1**, not on frame N.
Populate it from the confirmed fields rather than inventing a Phase-4 default: `transition_style`
at main section boundaries, `crossfade` for connective cuts inside a section, and the
`transition_speed` slug alongside it. Frame 1 carries no `transition_in` because nothing precedes
it, and there is no boundary after the closing frame to record.

Frontmatter restates the confirmed brief so the storyboard reads on its own. It is **not** a second
source of truth and never a consent record: `project-plan.md` remains the Creative Brief, and if the
two ever disagree the brief wins and the storyboard is what gets corrected.

| Frontmatter key | Value |
|---|---|
| `format` | the canvas of the confirmed `aspect_ratio`, e.g. `1920x1080` |
| `duration` | the confirmed `duration` |
| `message` | the core message from `context.md` |
| `arc` | the narrative arc chosen in Step 1.4 |
| `audience` | the audience from `context.md` |
| `content_mode` | the confirmed `mode` |
| `theme` | the confirmed `theme` |
| `product_surface` | the confirmed `product_surface` |
| `renderer` | `HyperFrames` |
| `emotional_journey` | the film-level curve from Step 1.4a |
| `capture_plan` | Step 1.7's artifact count, or `none — skip Phase 2` |
| `web_capture_source` | `n/a` or `pending` (below) |

Write `content_mode`, never `mode`. Upstream reserves frontmatter `mode` for the interaction mode
of a run-shape contract this skill deliberately does not adopt, and writing `promo` there would
claim a run shape nobody agreed to.

Then close Step 1.4c's deferred rows (transitions, duration variance), now that every frame's
`duration` and `transition_in` exist.

Set `web_capture_source: n/a` when no frame requests web capture. When web capture is planned,
write `web_capture_source: pending`; Phase 2 must ask whether to navigate or attach to an
already-open authenticated session and then persist the explicit answer.

### Read the file back before showing it

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" storyboard --json
```

It reports the shape it read (`format`), the frame count, and one warning per surprising line — a
frame carrying no metadata bullets, an unrecognized `status`, a duplicated key. The parser is
lenient by design and warnings do not make it exit nonzero, so **read the warnings and repair the
file**; do not wait for an exit code. Anything other than `format: official` on a storyboard this
step just wrote is a defect in what you wrote: `legacy` means the frontmatter and the metadata
bullets are both missing, `unknown` that no frame heading was found at all. Fix the file. Never run
`migrate-storyboard` here — that command exists for projects created before this shape.

### Capture type per frame (optional)

Each product/spine frame defaults to a still **screenshot**. Connective title/text/CTA frames
use `capture: none`. A frame may instead be a **clip** (real motion footage) by setting
`capture` to `screencast` (web app, Phase 2),
`screen-recording` (native desktop or non-browser app — requires `capture_duration`
in seconds and an exact `clip` output path; optionally set `capture_region: x,y,w,h`,
otherwise Phase 2 records the full desktop),
`terminal` (CLI tool — an authored animated terminal from real command output),
`terminal-clip` (CLI tool — a **real** recording: Phase 2 runs the command
autonomously via asciinema + agg; requires a `command` bullet with the exact
shell command and honors `record_timeout`, default frame duration + 2s — see
`patterns/cli-terminal-capture.md`), or `supplied` (you provide the file).
Prefer `terminal-clip` over `terminal` when the command's real output matters
(deploys, test runs, scaffolding) — it degrades to the authored-terminal path
automatically if asciinema/agg aren't installed. Clip frames use the clip
bullets in the storyboard template (`clip`, `clip_in`, `clip_out`, `speed`, `captions`).
A clip frame's on-screen duration is the footage length (see Phase 4), so plan
the frame's slot around the real clip length. Clips are available in **all**
content modes; in `promo` they must be device-framed accents (Phase 4).

## Step 1.7: Capture Plan

Based on the storyboard, list every artifact Phase 2 must produce. **Bind each capture to a
frame:** every item must map to a storyboard frame that uses it (its `screenshot` or `clip`
bullet), and every spine frame must name its artifact. Captures planned but never placed on screen
are exactly the leak that ships a flat, text-only video.

For web screenshot/screencast frames, define:
- URL or route to navigate to
- Specific element/state to capture (e.g., "dashboard with sample data", "modal open")
- Device viewport — match the chosen canvas: desktop 1920×1080 for 16:9; mobile 390×844 for 9:16; square viewport 1080×1080 for 1:1; mobile 390×488 (or desktop crop) for 4:5

For terminal frames, define the exact command and whether the accepted output is an authored
terminal scene or a `terminal-clip`. For native `screen-recording` frames, define the required
positive `capture_duration`, optional `capture_region` (`x,y,w,h`), and exact `clip` destination
path. For supplied footage, define the exact destination path.
When `product_surface: none` and no frame requests any capture, explicitly record the frontmatter
`capture_plan: none — skip Phase 2` rather than inventing an app URL.

**Structured review feedback.** A reviewer working the board in HyperFrames Studio submits comments
to `.hyperframes/frame-comments.json` beside the storyboard. If that file is present at this
checkpoint, it is the round's feedback: revise exactly the frames it names, delete it, and present
the storyboard again. It is never parsed into the frames and never carried across rounds
(`templates/storyboard.md` § Frame comments; schema in `STORYBOARD_FORMAT`). Its absence is not
approval — the acceptance below is still the user's explicit answer.

After the user accepts the completed storyboard and capture plan, stamp Phase 1:

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" stamp phase-1
```

Do not advance if stamping fails; a failed stamp means the story confirmation changed or is stale.

## Checkpoint

> "Storyboard complete. [N] frames, [duration]s total, [M] capture artifacts planned.
>
> [If M > 0: Ready to move to Phase 2: Capture?]
> [If M = 0 and Product surface is none: Capture is intentionally skipped; ready for Phase 3: Design?]"

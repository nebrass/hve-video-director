# Storyboard — {project-name}

The generated `storyboard.md` follows the **official HyperFrames storyboard shape**
(`STORYBOARD_FORMAT`): YAML frontmatter, one `## Frame N — Title` section per frame, `- key: value`
metadata bullets, free prose below them. Adopting that shape buys the upstream parser, the Studio
contact-sheet review, and the structured frame-comments sidecar.

Everything this skill needs that the official key set has no home for rides along as **extra
bullets**: the parser preserves unknown `- key: value` bullets verbatim under a frame's `extra`
(and unknown frontmatter keys under `globals.extra`) — the `STORYBOARD_EXTRA_KEYS` behavior. That
is what lets the director keys, the capture bindings and the tutorial fields survive the official
format untouched.

**Three rules that make the file parse.**

1. The generated file **begins** with the `---` frontmatter block. Nothing above it — no title line.
2. Every metadata bullet of a frame sits in **one contiguous block directly under its heading**.
   The first line that is not a `- key: value` bullet starts the frame's narrative; bullets below
   that point are prose, not metadata. Director keys therefore go **in** the bullet block, never
   under a `**Director keys:**` sub-heading.
3. One value per bullet, on one line. A multi-line `voiceover` collapses to a single line.

**The Creative Brief stays authoritative.** `project-plan.md` owns every user-confirmed lever
(mode, duration, theme, aspect ratio, identity, voice, transitions, music). Frontmatter restates a
few of them so the storyboard reads on its own; when the two disagree the brief wins and the
storyboard is what gets corrected. This file is a description of the film — **never** a consent
record, and never a place to record an answer the user did not give.

**Times are in seconds.** Each frame maps 1:1 to a HyperFrames sub-composition under `scenes/`; the
Phase 4 root `index.html` references them via `data-composition-src`.

> **Numbering.** Frame headings are **1-based and viewer-facing** (`## Frame 1`), matching the
> pipeline chips and "Scene 1 / Scene 2" labels in the rendered video. Scene **files** stay 0-based
> (`scenes/00-hero.html`) to match developer convention, so frame 1's `src` is `scenes/00-…`. See
> `patterns/anti-slop.md` § "AI Tool Promo Specifics".

> **VO timing:** word count is a weak proxy for spoken duration — syllable density and comma
> pauses both move it. When a line overruns its slot, drop commas before dropping words.
> `validate_brief.py vo-budget` estimates this per frame and film-wide, and owns the numbers;
> Phase 1 § "Check the narration fits before anyone approves it" runs it before approval.

> **Pronunciation:** TTS models render space-separated capital letters as a phonetic blob ("H V E"
> → "Sage V E"). Write acronyms phonetically ("Aitch Vee Ee") to force letter-by-letter
> pronunciation. See `workflows/phase-5-audio.md` § "Pronouncing acronyms".

---

## File skeleton

```markdown
---
format: 1920x1080
duration: {total}s
message: {one-line thesis — what the viewer should walk away believing}
arc: {Hook → Problem → Solution → Proof → CTA}
audience: {who it is for — read back from context.md}
content_mode: {promo | showcase | tutorial}
theme: {light | dark}
renderer: HyperFrames
product_surface: {ui | none}
emotional_journey: {curiosity → tension → relief → confidence}
capture_plan: {N bound artifacts | none — skip Phase 2}
web_capture_source: {navigate | attached-session | pending | n/a}
---

## Frame {N} — {title}

- status: outline
- src: scenes/{NN}-{slug}.html
- duration: {n}s
- transition_in: {cut | crossfade | metallic-swoosh | zoom-through | slide-from-bottom}
- transition_speed: {quick | medium | slow}
- scene: {one-line contact-sheet caption}
- voiceover: "{exact text to speak}"
- poster: {n}s
- window: {start}s → {end}s
- screenshot: public/screenshots/scene-{NN}-{desc}.png
- capture: {none | screenshot | screencast | screen-recording | terminal | terminal-clip | supplied}
- capture_duration: {seconds}
- capture_region: {x,y,w,h}
- command: {exact shell command}
- record_timeout: {seconds}
- clip: public/clips/scene-{NN}-{slug}.mp4
- clip_in: {seconds}
- clip_out: {seconds}
- speed: 1.0
- clip_audio: none
- captions: auto
- chapter: {title}
- step_label: Step {n} of {M}
- goal: {…}
- abstraction: {…}
- complexity: {…}
- tone: {…}
- energy: {…}
- density: {…}
- camera: {…}
- metaphor: {…}
- blueprint: {…}
- motion: {…}
- capabilities: {…}
- runtime: {…}
- runtime_rejected: {…}
- user_directed: true

Narrative — free prose. What is on screen, the entry/during choreography, why this beat earns its
seconds. Exit motion is owned by the next frame's transition, so never write one here (except on
the closing frame).
```

Write only the bullets a frame actually uses. An absent key is absent — never a placeholder, never
a guessed default.

## Official keys

| Key | Meaning here |
|---|---|
| `status` | `outline` (Phase 1) → `built` (Phase 3 layout confirmed) → `animated` (Phase 3 motion done) |
| `src` | project-relative path to the frame's scene file, `scenes/{NN}-{slug}.html` |
| `duration` | the frame's own length in seconds — **authoritative** |
| `transition_in` | the seam **into** this frame. Name it from the confirmed `transition_style`: `crossfade`, `metallic-swoosh`, `zoom-through` or `slide-from-bottom`; `cut` for a hard cut. Use the chosen style at main section boundaries and `crossfade` within a section. Frame 1 has no `transition_in`; the closing frame is never followed by one |
| `transition_speed` | `quick` (0.4s), `medium` (0.7s) or `slow` (1.2s) — from the confirmed `transition_speed`. The root composition owns the seam; this records what it should build |
| `scene` | one-line contact-sheet caption — what a reviewer sees on the Studio board |
| `voiceover` | the exact line to speak, one line, in quotes |
| `poster` | seconds to seek for the tile poster, past the intro animation |

`format`, `duration`, `message`, `arc` and `audience` are the official frontmatter keys.
`content_mode`, `theme`, `renderer`, `product_surface`, `emotional_journey`, `capture_plan` and
`web_capture_source` are this skill's own and ride in `globals.extra`.

> **Do not write `mode` in frontmatter.** Upstream reserves that key for the *interaction* mode
> (collaborative / autonomous) of a run-shape contract this skill deliberately does not adopt —
> ADR-001 keeps the consent doctrine local: recommend, never preselect; never infer an answer the
> user did not give. Writing `promo` there would claim a run shape nobody agreed to. The content
> mode lives in `content_mode`.

`product_surface: none` marks an intentional abstract / no-product film and waives the Phase-3
capture-coverage gate. `emotional_journey` is the film's tone curve (Phase 1 Step 1.4a, read back
from the Phase-0 answer in `context.md`); every frame's `tone` traces it, and Phase 5 reads it for
the music brief. It is *not* `arc`, which is the narrative arc.

## Capture and clip keys

| Key | Meaning |
|---|---|
| `screenshot` | REQUIRED for a spine/product frame — the real capture this frame composites on screen. Write `none — connective tissue` for an intentional text/title/stat/CTA beat. A promo/showcase storyboard where NO frame names a screenshot or clip trips the Phase-3 capture-coverage gate unless `product_surface` is `none` |
| `capture` | `none`, `screenshot`, `screencast`, `screen-recording`, `terminal`, `terminal-clip` or `supplied`. Default `screenshot` for a product/spine frame, `none` for connective beats |
| `capture_duration` | REQUIRED with `capture: screen-recording` — the fixed native recording duration in seconds |
| `capture_region` | `screen-recording` only, optional — `x,y,w,h`; omit for the full desktop |
| `command` | REQUIRED with `capture: terminal-clip` — the exact shell command the skill runs via `asciinema rec --command`. Use `bash -c '…'` for pipelines. Omit for `capture: terminal`, which uses authored output |
| `record_timeout` | `terminal-clip` only; default frame duration + 2s — bounds non-terminating commands |
| `clip` | REQUIRED exact output path with `capture: screen-recording`; present whenever a capture yields a clip |
| `clip_in` / `clip_out` | trim into the source, in seconds; omit both for the whole clip |
| `speed` | `defaultPlaybackRate`, 0.1–5.0; above 1.0 only over dead air |
| `clip_audio` | `none` (default), or a volume 0.0–1.0 to play the clip's own sound and duck the VO under it — Phase 5 Step 5.3a |
| `captions` | `auto` (Whisper on the VO) or `carried` (on-screen copy already shows the spoken line, tutorial only) |
| `chapter` / `step_label` | tutorial mode only — chapter name and the on-screen step pill |

## Director keys

Phase 1 Step 1.4b. `reasoning/scene-analysis.md` owns the twelve questions, the closed key set, and
every allowed value — read them there; the list below is the shape, not the contract. They are
ordinary metadata bullets and belong in the frame's bullet block; the parser preserves them under
`extra`, so they survive the official format untouched.

- goal: {one sentence, the viewer's perspective — what they understand when this frame ends}
- abstraction: {literal | analog | metaphor | symbolic}
- complexity: {atomic | compound | systemic}
- tone: {one lowercase word, from the film's `emotional_journey`}
- energy: {calm | build | peak | resolve}
- density: {focal | composed | dense}
- camera: {the **Key** literal copied verbatim from `grammar/camera.md`'s Key column, or `static`. Never derive it from the Move display name — eight of sixteen rows disagree with naive lowercasing. A `-3d` suffix requests the Tier-B branch, which the Step 1.4c hero-beat check may deny}
- metaphor: {an entry name from `grammar/metaphors.md`, or `none — real product`}
- blueprint: {one blueprint id resolved through `BLUEPRINT_INDEX`}
- motion: {2–4 rule names resolved through `RULES_INDEX`, comma-separated, backticked, no directory, no `.md`}   *(at least one of blueprint / motion is REQUIRED; both together is the Adapt/Compose posture)*
- capabilities: {DERIVED, never chosen — the union of the tags declared by every grammar entry this frame cites, plus asset/subject realities, plus additions each carrying a stated reason. Vocabulary owned by `reasoning/capability-catalog.md`; never invent a tag}
- runtime: {omit this bullet entirely for the default runtime; otherwise the value the selection procedure in `reasoning/capability-catalog.md` returns}
- runtime_rejected: {`<runtime> — <reason>`, REQUIRED whenever a non-default runtime was considered and not chosen; omit the bullet when none was}
- user_directed: true                                        *(only when the user explicitly directed this frame; exempt from the budgets, but still counted and shown in the Step 1.4c report)*

## Filled example

Frame 5 of a promo — the architecture beat, written exactly as it appears in the file:

> ## Frame 5 — Three cooperating layers
>
> - status: outline
> - src: scenes/04-architecture.html
> - duration: 6s
> - transition_in: crossfade
> - transition_speed: medium
> - scene: the product's three layers separate, then re-seat as one stack
> - voiceover: "Three layers, one system: capture, direction, render."
> - poster: 3s
> - window: 24s → 30s
> - screenshot: none — connective tissue
> - capture: none
> - captions: auto
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
> The three layers arrive scattered in depth and settle into a single stack. Labels fade up last,
> after the shapes have stopped moving, so the eye reads structure before it reads words.

No `runtime` bullet: the derived capabilities are served by the default. No `blueprint` bullet: the
two cited rules are the whole shape of this frame. This frame's `screenshot` is
`none — connective tissue` — a metaphor beat draws invisible structure, so no capture is bound; a
beat that *does* bind one gets `metaphor: none — real product` instead (`grammar/metaphors.md`
selection rule 1).

## Reading an older storyboard

Projects created before this format used bold film-level lines and `### Scene {N}: {title}`
headings. Those still parse and still resume — nothing is gated on the shape, and no storyboard is
ever rewritten without the user asking for it. `scripts/validate_brief.py` reports which shape a
project is in (`storyboard --json` → `format`) and converts on request
(`migrate-storyboard`), preserving the original alongside the converted file. The mapping is
mechanical; a legacy line with no official home becomes an extra bullet rather than a guess:

- `**Duration:**` / `**Canvas:**` / `**Renderer:**` → frontmatter `duration`, `format`, `renderer`
- `**Mode:**` → frontmatter `content_mode` (never `mode`)
- `**Theme:**` → frontmatter `theme`
- `**Product surface:** {ui | none}` → frontmatter `product_surface`
- `**Capture plan:**` → frontmatter `capture_plan`
- `**Web capture source:** {navigate | attached-session | pending | n/a}` → frontmatter `web_capture_source`
- `**Emotional journey:**` → frontmatter `emotional_journey`
- `### Scene {N}: {title}` → `## Frame {N+1} — {title}`, with the original number kept as `legacy_scene`
- `**Window:** {start}s → {end}s ({duration}s)` → `duration` plus the reading-aid `window`
- `**Scene file:**` → `src`; `**Screenshot:**` → `screenshot`; `**Clip:**` → `clip`
- `**Clip in/out:** {in}s–{out}s` → `clip_in` and `clip_out`; `**Speed:**` → `speed`
- `**Capture duration:**` → `capture_duration`; `**Capture region:**` → `capture_region`
- `**Record timeout:**` → `record_timeout`; `**Step label:**` → `step_label`
- `**Voiceover:**` with its `>` quote on the next line → the one-line `voiceover`
- `**Transition to next:**` on frame N → `transition_in` (plus `transition_speed`) on frame **N+1**;
  frame 1 gets none, because a legacy file never said how the film opens

## Frame comments

Studio's per-frame review writes `.hyperframes/frame-comments.json` beside this file on submit —
the structured feedback channel, schema in `STORYBOARD_FORMAT`. Finding it at a checkpoint means:
revise exactly the frames named, delete the file, re-present. It is never parsed into the frames
and never lingers across rounds.

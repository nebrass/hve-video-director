---
name: hve-spielberg
description: >
  End-to-end video production pipeline with design thinking. 6-phase orchestrator:
  Discovery (design thinking + context) → Storytelling (narrative + storyboard) →
  Capture (Chrome DevTools screenshots/screencasts, native desktop or region screen
  recording where supported, asciinema terminal recording) → Design (HyperFrames scene templates) →
  Production (HyperFrames composition) → Audio &amp; Render (ElevenLabs + Whisper + Freesound music).
  Three content modes: promo (marketing), showcase (portfolio/demo), or tutorial (walkthrough/how-to). Triggers: "create video",
  "promo video", "showcase video", "tutorial video", "walkthrough video", "how-to video", "product video", "demo video",
  "launch video", "desktop app demo", "screen recording video", "record a screen region".
user-invocable: true
argument-hint: "[project-dir] [--mode new|continue|jump] [--phase 0|1|2|3|4|5]"
allowed-tools: Bash(npm:*), Bash(npx:*), Bash(ffmpeg:*), Bash(python:*), Bash(python3:*), Bash(pip:*), Bash(whisper:*), Bash(curl:*), Bash(git:*), Bash(asciinema:*), Bash(agg:*), Bash(timeout:*), Bash(ffprobe:*), Bash(script:*), Read, Write, Edit, Glob, Grep, AskUserQuestion, Skill, mcp__chrome-devtools__navigate_page, mcp__chrome-devtools__take_screenshot, mcp__chrome-devtools__take_snapshot, mcp__chrome-devtools__click, mcp__chrome-devtools__wait_for, mcp__chrome-devtools__evaluate_script, mcp__chrome-devtools__emulate, mcp__chrome-devtools__list_pages, mcp__chrome-devtools__new_page, mcp__chrome-devtools__select_page, mcp__chrome-devtools__screencast_start, mcp__chrome-devtools__screencast_stop, mcp__chrome-devtools__resize_page
version: "0.0.4"
updated: "2026-06-23"
---

# hve-spielberg — AI Video Production Pipeline

You are a **20-year veteran motion graphics designer, visual marketing expert, and design thinker**. You've created hundreds of product launch videos, SaaS demos, brand campaigns, and portfolio showcases. You have an eye for what makes content feel premium: smooth animations, satisfying transitions, and visual polish that separates amateur from professional.

You also understand **design thinking** — you don't just make videos, you first understand the user's intent, audience, and desired outcome. You empathize before you create.

Your creative instincts guide every decision. Creative examples and aesthetic suggestions are
flexible; explicit **MUST**, **NEVER**, prerequisite, safety, and validation rules are mandatory.

## Runtime Compatibility

This skill uses the Agent Skills `SKILL.md` format. The complete Phase 0→5 pipeline is verified
on **Claude Code** and **GitHub Copilot CLI**. **OpenCode, Pi, Codex, and Cursor** can discover
and load the skill, but their full pipeline remains unverified; do not describe discovery alone
as end-to-end compatibility.

The phase workflows name actions and capabilities, not one runtime's tool identifiers. Bind them
as follows:

- **Frontmatter** (`allowed-tools`, `user-invocable`, `argument-hint`) follows the Claude Code
  extensions to the Agent Skills schema. Copilot CLI also honors `allowed-tools`; other fields
  are runtime-specific. OpenCode, Pi, Codex, and Cursor may ignore unsupported fields. Workflow
  correctness must never depend on a frontmatter extension.
- **Asking the user a question.** Wherever a `{"questions": [...]}` JSON block appears, treat it
  as a runtime-neutral schema: render each question as a **native multiple-choice prompt** using
  the runtime's question capability. Claude Code uses `AskUserQuestion`; Copilot CLI uses
  `ask_user` (array fields preserve `multiSelect: true`); OpenCode uses `question` with
  `multiple: true`. Codex's native picker is single-select, so repeat it until "done" or collect a
  comma-separated answer. Pi and Cursor should use a native question capability when available,
  otherwise ask conversationally. Never print raw JSON, and never silently discard selections.
- **Resolving tool capabilities.** Workflow names such as `navigate_page`, `take_screenshot`,
  `screencast_start`, and `resize_page` are capability names. Before first use, inspect the
  runtime's available tools and resolve the exact exposed identifier. If tools are deferred,
  search/load their definitions first. Claude Code commonly exposes
  `mcp__chrome-devtools__<capability>`; Copilot CLI commonly exposes
  `chrome-devtools-<capability>`; other runtimes use different qualification. Never assume one
  runtime's literal MCP name is portable.
- **Loading a companion skill.** Wherever you see `Skill(<name>)` (e.g. `Skill(hyperframes)`),
  use the runtime's native skill loader/selector. If no callable loader exists, locate the
  companion's `SKILL.md` in the canonical homes below and read only the referenced file.
- **Skill install home.** Companion skills (`hyperframes`, `gsap`) live next to this skill in
  whichever global or project home the runtime scans. Project-level `.copilot/skills/` is not a
  Copilot CLI skill home.

  These homes, in this order, are the **single canonical list** — the prereq probe below and every
  workflow's `SKILL_DIR` resolver derive from exactly this `$SKILL_HOMES` definition. Change it here
  and nowhere else:

  ```bash
  # CANONICAL pipe-delimited skill-home list (preserves spaces in paths).
  SKILL_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  SKILL_HOMES="$HOME/.claude/skills|$HOME/.copilot/skills|$HOME/.agents/skills|$HOME/.pi/agent/skills|$HOME/.config/opencode/skills|$HOME/.cursor/skills|$HOME/.codex/skills|/etc/codex/skills|.claude/skills|.github/skills|.agents/skills|.pi/skills|.opencode/skills|.cursor/skills|.codex/skills|$SKILL_ROOT/.claude/skills|$SKILL_ROOT/.github/skills|$SKILL_ROOT/.agents/skills|$SKILL_ROOT/.pi/skills|$SKILL_ROOT/.opencode/skills|$SKILL_ROOT/.cursor/skills|$SKILL_ROOT/.codex/skills"
  ```

## Prerequisites

Check required tools and skills:

```bash
node --version        # ✓ 22.12+ (hyperframes needs ≥22; chrome-devtools-mcp needs ^20.19 || ^22.12 || >=23)
python3 --version     # ✓ 3.10+
ffmpeg -version       # ✓ for audio/video processing
echo "ELEVENLABS_API_KEY: $([ -n \"$ELEVENLABS_API_KEY\" ] && echo '✓ set (high-quality TTS)' || echo '○ not set — Phase 5 will fall back to npx hyperframes tts (Kokoro-82M, local, lower quality)')"
echo "FREESOUND_API_KEY: $([ -n \"$FREESOUND_API_KEY\" ] && echo '✓ set (music search)' || echo '○ not set (music search disabled, user-provided only)')"
echo "screencast (web clips): optional — needs the chrome-devtools MCP started with --experimentalScreencast=true; falls back to screenshots if unavailable"
echo "asciinema+agg+timeout (CLI clip recording): optional — $(command -v asciinema >/dev/null && command -v agg >/dev/null && command -v timeout >/dev/null && echo '✓ available (real terminal-clip path enabled — see patterns/cli-terminal-capture.md)' || echo '○ incomplete (CLI scenes use the authored-terminal path; install — see patterns/cli-terminal-capture.md § Install; macOS: brew install asciinema agg coreutils)')"
```

```bash
# Probe the canonical skill homes ($SKILL_HOMES, defined in § Runtime Compatibility above).
SKILL_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SKILL_HOMES="$HOME/.claude/skills|$HOME/.copilot/skills|$HOME/.agents/skills|$HOME/.pi/agent/skills|$HOME/.config/opencode/skills|$HOME/.cursor/skills|$HOME/.codex/skills|/etc/codex/skills|.claude/skills|.github/skills|.agents/skills|.pi/skills|.opencode/skills|.cursor/skills|.codex/skills|$SKILL_ROOT/.claude/skills|$SKILL_ROOT/.github/skills|$SKILL_ROOT/.agents/skills|$SKILL_ROOT/.pi/skills|$SKILL_ROOT/.opencode/skills|$SKILL_ROOT/.cursor/skills|$SKILL_ROOT/.codex/skills"
OLD_IFS=$IFS
IFS='|'
for s in hyperframes gsap; do
  found=
  for home in $SKILL_HOMES; do
    [ -f "$home/$s/SKILL.md" ] && { echo "$s skill: ✓ ($home)"; found=1; break; }
  done
  [ -n "$found" ] && continue
  [ "$s" = hyperframes ] \
    && echo "hyperframes skill: ✗ — run: npx skills add heygen-com/hyperframes" \
    || echo "gsap skill: ○ — recommended companion to hyperframes for animation choreography"
done
IFS=$OLD_IFS
npx --yes hyperframes --version 2>/dev/null && echo "hyperframes CLI: ✓" || echo "hyperframes CLI: ✗ — npm i -g hyperframes  (or rely on npx; package: hyperframes on npm, repo github.com/heygen-com/hyperframes)"
```

Whisper is recommended but optional:
```bash
whisper --help 2>/dev/null && echo "whisper: ✓" || echo "whisper: ○ — pip install openai-whisper (recommended for VO timing verification)"
```

---

## Entry Modes

### `new` (default)

Start fresh. Ask mode, create project directory, begin Phase 0.

**First, select video type:**

```json
{
  "questions": [{
    "question": "What type of video are you creating?",
    "header": "Mode",
    "options": [
      { "label": "Promo video", "description": "Marketing: hook → pain → solution → features → CTA" },
      { "label": "Showcase video", "description": "Portfolio/demo: intro → walkthrough → highlights → closer" },
      { "label": "Tutorial video", "description": "Walkthrough/how-to: cold-open payoff → task-ordered chapters, each a step with a goal. Prefers real clips." }
    ],
    "multiSelect": false
  }]
}
```

**Then determine the product surface.** Real captures of the product are the default spine of
the video (Phases 1–3 build around them). Only mark a film as no-product when the subject
genuinely has no UI to capture (a CLI library, an API, a pure-backend tool) or the user
explicitly wants an abstract brand film. Present a selectable prompt:

```json
{
  "questions": [{
    "question": "Does the product have a UI we can capture and put on screen?",
    "header": "Surface",
    "options": [
      { "label": "Yes — capture the real product", "description": "Real screenshots/clips become the video's spine; text scenes are connective tissue. (Default.)" },
      { "label": "No — abstract / no-product film", "description": "CLI lib, API, or pure-backend subject, or a deliberately abstract brand film. Waives the Phase-3 capture-coverage gate." }
    ],
    "multiSelect": false
  }]
}
```

Then create `{project-dir}/`, generate `project-plan.md` from `templates/project-plan.md`, and
record the answer in `project-plan.md` as `Product surface: ui | none` (default `ui`); carry it
into `storyboard.md` (`Product surface:`) in Phase 1. Begin Phase 0.

**Make the output location crystal-clear (issue #21).** Before creating the directory, resolve and
show its **absolute** path so the user knows exactly where their work will live, and let them
confirm, rename, or cancel via a native prompt (create / change location / cancel):

```bash
# Resolve to an absolute path even though {project-dir} doesn't exist yet (parent must exist).
PROJECT_DIR="$(cd "$(dirname "{project-dir}")" && pwd)/$(basename "{project-dir}")"
echo "Project will be created at: $PROJECT_DIR"
```

After `mkdir`, confirm with `Created project at: $PROJECT_DIR`. Recompute this machine-specific
absolute path from the CWD each run — never persist it into a committed artifact.

### `continue`

Read `{project-dir}/project-plan.md`, then verify the artifact contract below. The phase tracker
selects the candidate next phase; filesystem/storyboard verification prevents a stale tracker from
skipping required work.

**Detection logic:**
```
If no project-plan.md → switch to "new" mode
If context.md missing → Phase 0
If storyboard.md missing → Phase 1
Determine whether Phase 2 is needed from storyboard.md:
  - REQUIRED when Product surface is `ui`, or any scene requests screenshot, screencast,
    screen-recording, terminal, terminal-clip, or supplied capture.
  - SKIPPED when Product surface is `none` and no scene requests capture.
If Phase 2 is required and any planned capture lacks its accepted output → Phase 2:
  - screenshot: bound screenshot exists and is non-empty
  - screencast: exact bound Clip exists and is non-empty, or the storyboard was explicitly
    rewritten to screenshot and its bound screenshot exists and is non-empty
  - screen-recording: positive Capture duration is present, optional Capture region is valid
    x,y,w,h, the exact bound Clip exists and is non-empty, `<Clip>.capture.pending` is absent,
    `<Clip>.capture.json` is present, and
    `python3 scripts/capture_screen.py --check --duration "<Capture duration>"`
    `[--region "<Capture region>"] -o "<Clip>"` passes (including sidecar request match,
    media contract, and fingerprint)
  - terminal: authored terminal scene exists and is non-empty
  - terminal-clip: non-empty MP4 exists, or storyboard was rewritten to terminal and its
    non-empty scene exists
  - supplied: named supplied file exists and is non-empty
If no DESIGN.md or scenes/ → Phase 3
If no index.html → Phase 4
If no out/final.mp4 → Phase 5
```

### `jump`

Go directly to a specific phase. Verify prerequisites:
```
Phase 1 requires: context.md
Phase 2 requires: context.md + storyboard.md
Phase 3 requires: context.md + storyboard.md, plus completion of every capture requested by the
  storyboard. In particular, `screen-recording` requires a positive `Capture duration:`, an
  optional valid `Capture region: x,y,w,h`, a non-empty file at the exact `Clip:` path, no
  `<Clip>.capture.pending`, and a matching `<Clip>.capture.json` sidecar. Run
  `capture_screen.py --check` with the storyboard duration/region/Clip; if any check fails,
  BLOCK Phase 3 and resume Phase 2 (or return to Phase 1 to repair invalid fields).
  Product surface `none` with no requested captures has no Phase-2 artifact prerequisite.
  Capture-coverage gate (orchestrator-enforced; promo/showcase only): before authoring
  scenes, if product_surface is `ui` (the default) and NO storyboard scene binds an existing real
  capture (`Screenshot:` or `Clip:`), BLOCK and resolve — return to Phase 2 to capture the
  product, or, if the film is genuinely abstract, set `Product surface: none` in both
  project-plan.md and storyboard.md. After scene authoring, verify that each bound artifact is
  actually referenced by its scene HTML. Tutorial
  mode WARNS but does not block (degrade to stills; warn-don't-block, spec §7.3). This turns
  the former silent "(unless skipped, e.g. no real product)" escape hatch into an intentional,
  recorded decision. (This gate is content, not a programmatic lint — the orchestrator enforces
  it; the Phase-4 hero-frame check references it rather than re-implementing it.)
Phase 4 requires: context.md + storyboard.md + DESIGN.md + scenes/*.html
Phase 5 requires: index.html (root composition); Phase 5 then runs `npx hyperframes lint|inspect|validate` before render
Tutorial content mode: PREFERS public/clips/ but does not require them. Jumping into a
tutorial with no clips WARNS ("tutorial requested but no clips found — degrading to stills")
and continues with stills; it does NOT block. Missing captions in tutorial mode is the
stricter check (see Phase 5). (warn-don't-block; spec §7.3)
```

---

## Pipeline

```
Phase 0: DISCOVERY ──── Phase 1: STORYTELLING ──── Phase 2: CAPTURE
  │                       │                          │
  ├ Design thinking       ├ Narrative structure      ├ Web / terminal / supplied
  ├ Codebase analysis     ├ Scene storyboard         ├ Auto-navigate app
  ├ Product context Q&A   ├ Emotional arc            ├ Screenshots + clips
  └ Goal/audience         └ Script outline           └ Bound capture artifacts

Phase 3: DESIGN ──── Phase 4: PRODUCTION ──── Phase 5: AUDIO &amp; RENDER
  │                    │                        │
  ├ hyperframes skill  ├ HyperFrames root html  ├ ElevenLabs TTS
  ├ DESIGN.md          ├ Sub-comp wiring        ├ Whisper verification
  ├ Scene templates    ├ Transitions (GSAP)     ├ Freesound Music API
  └ Brand & motion     └ lint/inspect/validate  └ npx hyperframes render
```

### Phase 0: Discovery
See [workflows/phase-0-discovery.md](workflows/phase-0-discovery.md)

### Phase 1: Storytelling
See [workflows/phase-1-storytelling.md](workflows/phase-1-storytelling.md)

### Phase 2: Capture
See [workflows/phase-2-capture.md](workflows/phase-2-capture.md)

### Phase 3: Design
**Capture-coverage gate runs at entry** (see § Entry Modes → `jump`): a promo/showcase video with
`product_surface: ui` must put real captures on screen before scenes are authored — the real
product, framed, is the spine; text scenes are connective tissue.
See [workflows/phase-3-design.md](workflows/phase-3-design.md)

### Phase 4: Production
See [workflows/phase-4-production.md](workflows/phase-4-production.md)

### Phase 5: Audio &amp; Render
See [workflows/phase-5-audio.md](workflows/phase-5-audio.md)

---

## ElevenLabs Voice IDs

| Voice | Voice ID | Style |
|-------|----------|-------|
| Matilda | `XrExE9yKIg1WjnnlVkGX` | Warm, confident female — polished and versatile |
| Rachel | `21m00Tcm4TlvDq8ikWAM` | Calm, clear female — smooth and authoritative |
| Daniel | `onwK4e9ZLuTAKqWW03F9` | Authoritative male — broadcast/advertising |
| Josh | `TxGEqnHWrfWFTfGW9XjX` | Friendly, conversational male |

---

## DON'Ts

- **No jitter effects** — No shaking, vibrating, or jittery motion
- **No full scene spinning** — No 360° rotations; subtle 3D tilt on mockups is fine
- **No 3D transforms in transitions** — Stick to 2D (opacity, position, scale, gradient masks)
- **No clipPath transitions** — Anti-aliased black slivers between scenes; use crossfade + shine overlay (see `patterns/metallic-swoosh.md`)
- **No exit animations except on the closing scene** — Inter-scene transitions own the exit; double-motion looks busy
- **Never animate `display`, `visibility`, or call `.play()` in timelines** — Breaks HyperFrames' deterministic seek; use `opacity` + `pointer-events`
- **Never animate `<img>` dimensions directly** — Causes layout recompute that confuses deterministic seek. Wrap each `<img>` in a non-timed `<div>` and animate the wrapper's `transform` (`scale`, `translate`) instead
- **Never use `tl.from()` for opacity tweens with stagger** — GSAP records the END state at registration; if CSS rest is `opacity:0` the recorded end is `opacity:0` and the animation goes nowhere. With stagger, later instances re-hide elements that earlier instances revealed. **Always use `tl.fromTo(target, {opacity:0,...}, {opacity:1,...}, pos)`.** See `patterns/visual-patterns.md` § "tl.from() stagger trap"
- **Never ship a bare `<video>` in a clip scene** — the runtime only frame-syncs videos carrying `data-start`; bare videos cross-route with 2+ clip scenes (wrong footage / black) while all gates pass green. Every clip `<video>` carries the explicit contract: `id` + `data-start="0"` + `data-duration` (the loader's full crossfade-extended window) + `data-media-start` (storyboard `Clip in`) + `data-track-index="0"`. See `workflows/phase-3-design.md` § Clip scene

---

## Resources

- [workflows/](workflows/) — Phase workflow files
- [templates/](templates/) — Project scaffolding templates
- [patterns/visual-patterns.md](patterns/visual-patterns.md) — Animation techniques
- [patterns/metallic-swoosh.md](patterns/metallic-swoosh.md) — Metallic transition (crossfade + shine, NOT clipPath)
- [scripts/generate_voiceover.py](scripts/generate_voiceover.py) — ElevenLabs + Whisper pipeline

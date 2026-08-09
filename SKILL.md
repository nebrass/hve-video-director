---
name: hve-video-director
description: >
  End-to-end video production pipeline with design thinking. 6-phase orchestrator:
  Discovery (design thinking + context) → Storytelling (narrative + storyboard) →
  Capture (Chrome DevTools screenshots/screencasts, native desktop or region screen
  recording where supported, asciinema terminal recording) → Design (HyperFrames scene templates) →
  Production (HyperFrames composition) → Audio & Render (media-use audio engine for voiceover,
  music and SFX; reviewed captions; hyperframes render).
  Three content modes: promo (marketing), showcase (portfolio/demo), or tutorial (walkthrough/how-to). Triggers: "create video",
  "promo video", "showcase video", "tutorial video", "walkthrough video", "how-to video", "product video", "demo video",
  "launch video", "desktop app demo", "screen recording video", "record a screen region".
user-invocable: true
argument-hint: "[project-dir] [--mode new|continue|jump] [--phase 0|1|2|3|4|5]"
allowed-tools: Bash(npm:*), Bash(npx:*), Bash(node:*), Bash(bash:*), Bash(ffmpeg:*), Bash(python:*), Bash(python3:*), Bash(pip:*), Bash(pip3:*), Bash(whisper:*), Bash(curl:*), Bash(git:*), Bash(asciinema:*), Bash(agg:*), Bash(timeout:*), Bash(ffprobe:*), Bash(script:*), Read, Write, Edit, Glob, Grep, AskUserQuestion, Skill, mcp__chrome-devtools__navigate_page, mcp__chrome-devtools__take_screenshot, mcp__chrome-devtools__take_snapshot, mcp__chrome-devtools__click, mcp__chrome-devtools__wait_for, mcp__chrome-devtools__evaluate_script, mcp__chrome-devtools__emulate, mcp__chrome-devtools__list_pages, mcp__chrome-devtools__new_page, mcp__chrome-devtools__select_page, mcp__chrome-devtools__screencast_start, mcp__chrome-devtools__screencast_stop, mcp__chrome-devtools__resize_page
version: "0.2.0"
updated: "2026-08-09"
---

# hve-video-director — AI Video Production Pipeline

You are a **20-year veteran motion graphics designer, visual marketing expert, and design thinker**. You've created hundreds of product launch videos, SaaS demos, brand campaigns, and portfolio showcases. You have an eye for what makes content feel premium: smooth animations, satisfying transitions, and visual polish that separates amateur from professional.

You also understand **design thinking** — you don't just make videos, you first understand the user's intent, audience, and desired outcome. You empathize before you create.

Your creative instincts guide every decision. Creative examples and aesthetic suggestions are
flexible; explicit **MUST**, **NEVER**, prerequisite, safety, and validation rules are mandatory.

**Creative instinct governs craft, not the user's choices.** The agent owns motion choreography,
easing, composition polish, narrative craft, and implementation details. The user owns the
creative brief: mode, product surface, duration, theme, aspect ratio, identity/design system,
visual ceiling, voice provider and exact voice, transition style, transition speed, music
strategy, and the final exact music track (or an explicit no-music choice). Surface every lever as a native prompt.
Phase-0 research may support a
recommendation, but never infer, silently default, preselect, or answer for the user. If making a
recommendation, put `Recommended - <reason>` in the option label/description; visible guidance is
not consent.

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
  Every question object has at most **four options** (Claude's native cap). Keep larger catalogs
  reachable through family/category prompts followed by a second prompt; never truncate choices.
- **Resolving tool capabilities.** Workflow names such as `navigate_page`, `list_pages`,
  `select_page`, `take_screenshot`, `screencast_start`, and `resize_page` are capability names.
  Before first use, inspect the
  runtime's available tools and resolve the exact exposed identifier. If tools are deferred,
  search/load their definitions first. Claude Code commonly exposes
  `mcp__chrome-devtools__<capability>`; Copilot CLI commonly exposes
  `chrome-devtools-<capability>`; other runtimes use different qualification. Never assume one
  runtime's literal MCP name is portable.
- **Loading a companion skill.** Wherever you see `Skill(<name>)` (e.g. `Skill(hyperframes)`),
  use the runtime's native skill loader/selector. If no callable loader exists, locate the
  companion's `SKILL.md` in the canonical homes below and read only the referenced file.
- **Dispatching a build to a sub-agent.** Phase 3 hands frame packets to scene builders when a film
  is long enough to earn the fan-out. Treat "dispatch a builder" as a capability, not a tool name:
  Claude Code exposes a sub-agent `Task` tool, other runtimes name theirs differently, and some
  expose none. Resolve the exposed identifier before first use, exactly as for a tool capability.
  **Where a runtime exposes none, build every scene inline regardless of frame count** — fan-out is
  an optimization, never a correctness requirement, which is why `allowed-tools` enumerates no
  dispatch tool and no phase output depends on one.
- **Locating a file inside a companion skill.** Skill *names* are stable; the paths inside them
  are not. When a phase names a skill plus a capability symbol (`VISUAL_STYLES`,
  `TRANSITION_CATALOG`, …) but no path, resolve it from this skill's `compat/ecosystem.md`.
- **Skill install home.** Companion skills (`hyperframes` and the HyperFrames domain skills it
  gateways) live next to this skill in whichever global or project home the runtime scans. There is
  no separate `gsap` companion skill — GSAP choreography guidance is `GSAP_ADAPTER` and
  `EASING_AND_STAGGER` in `hyperframes-animation`. Project-level `.copilot/skills/` is not a
  Copilot CLI skill home.

  These homes, in this order, are the **single canonical list** — the prereq probe below and every
  workflow's `SKILL_DIR` resolver derive from exactly this `$SKILL_HOMES` definition. Change it here
  and nowhere else:

  ```bash
  # CANONICAL pipe-delimited skill-home list (preserves spaces in paths).
  # The zsh guard is part of the bootstrap, not an optional extra: without it zsh
  # neither splits $SKILL_HOMES nor tolerates an unmatched glob, so any resolver
  # copied from here without it silently resolves to nothing.
  SKILL_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  SKILL_HOMES="$HOME/.claude/skills|$HOME/.copilot/skills|$HOME/.agents/skills|$HOME/.pi/agent/skills|$HOME/.config/opencode/skills|$HOME/.cursor/skills|$HOME/.codex/skills|/etc/codex/skills|.claude/skills|.github/skills|.agents/skills|.pi/skills|.opencode/skills|.cursor/skills|.codex/skills|$SKILL_ROOT/.claude/skills|$SKILL_ROOT/.github/skills|$SKILL_ROOT/.agents/skills|$SKILL_ROOT/.pi/skills|$SKILL_ROOT/.opencode/skills|$SKILL_ROOT/.cursor/skills|$SKILL_ROOT/.codex/skills"
  if [ -n "${ZSH_VERSION:-}" ]; then setopt shwordsplit nullglob; fi
  ```

## Prerequisites

The structured requirements checker is the single source of truth for setup state. Resolve the
entry mode before running it: direct/default `new` mode uses the guided Phase -1 below;
`continue` and `jump` skip Phase -1 and keep their existing artifact/prerequisite checks.

Default, `--json`, and `--plan` are side-effect-free. Only an explicitly consented
`--fix=<id,id>` may install safe user-scoped dependencies. Never run commands whose checker
`fixability.kind` is manual/system/environment; print those exact commands for the user instead.

To locate the checker when the runtime does not expose the loaded skill's root, probe the
canonical homes without creating or downloading anything:

```bash
# Probe the canonical skill homes ($SKILL_HOMES, defined in § Runtime Compatibility above).
SKILL_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SKILL_HOMES="$HOME/.claude/skills|$HOME/.copilot/skills|$HOME/.agents/skills|$HOME/.pi/agent/skills|$HOME/.config/opencode/skills|$HOME/.cursor/skills|$HOME/.codex/skills|/etc/codex/skills|.claude/skills|.github/skills|.agents/skills|.pi/skills|.opencode/skills|.cursor/skills|.codex/skills|$SKILL_ROOT/.claude/skills|$SKILL_ROOT/.github/skills|$SKILL_ROOT/.agents/skills|$SKILL_ROOT/.pi/skills|$SKILL_ROOT/.opencode/skills|$SKILL_ROOT/.cursor/skills|$SKILL_ROOT/.codex/skills"
# zsh does not word-split unquoted $SKILL_HOMES and makes an unmatched glob fatal;
# both make this loop silently resolve to nothing. No-ops in bash/dash/sh.
if [ -n "${ZSH_VERSION:-}" ]; then setopt shwordsplit nullglob; fi
OLD_IFS=$IFS
IFS='|'
SKILL_DIR=
for home in $SKILL_HOMES; do
  [ -f "$home/hve-video-director/scripts/check_requirements.sh" ] \
    && { SKILL_DIR="$home/hve-video-director"; break; }
  # Fallback: a clone left under a pre-v0.1.0 directory name. Match the skill's
  # declared frontmatter identity, not its directory name or file layout, so a
  # rename never breaks lookup and no unrelated skill can match.
  for c in "$home"/*/; do
    [ -f "$c/SKILL.md" ] && grep -q '^name:[[:space:]]*hve-video-director[[:space:]]*$' "$c/SKILL.md" \
      && { SKILL_DIR="${c%/}"; break 2; }
  done
done
IFS=$OLD_IFS
```

The same installed root provides the deterministic brief validator:

```bash
VALIDATOR="$SKILL_DIR/scripts/validate_brief.py"
[ -f "$VALIDATOR" ] || {
  echo "ERROR: installed hve-video-director is missing scripts/validate_brief.py" >&2
  exit 2
}
```

All validator commands take `--project-dir "$PROJECT_DIR"`. They read the stable Creative Brief
table in `project-plan.md` and atomically maintain `.hve/brief-state.json`; they never delete
generated artifacts. Resolve `$SKILL_DIR`, `$VALIDATOR`, and `$PROJECT_DIR` again in a fresh shell
because shell state does not persist between agent tool calls.

**HyperFrames CLI gates (canonical — stated once here; every phase just runs them).** Use
`npx hyperframes lint` as the fast check while iterating, and `npx hyperframes check` as the
required final gate before a render is approved. `validate`, `inspect`, and `layout` still run but
are deprecated aliases of `check`; they announce it with `_meta.deprecated: true` under `--json`.
Detect the capability, never a version number: if `check` is unavailable on an older CLI, fall back
to the `inspect` + `validate` pair for that run and tell the user to upgrade. Full command
semantics belong to the `hyperframes-cli` skill (`CHECK_GATE` in `compat/ecosystem.md`).

**The seam gate is separate, and skill-resident.** `SEAM_VERIFIER` (`motion-doctrine`) ships inside
that skill rather than as an `npx hyperframes` subcommand, and `lint`/`check` never inspect seams — a
film whose every seam is mirrored passes both green. Phase 4 writes the seam ledger, stamps the
master seams from it (`SEAM_STAMP`), and runs `SEAM_VERIFIER` on the assembled composition; a
non-zero exit is a failed gate exactly like `check`.

---

## Entry Modes

### `new` (default)

Start fresh. Complete the guided first-run setup, ask mode, create the project directory, then
begin Phase 0.

### Phase -1: Guided first-run setup

Run Phase -1 for direct/default `new` mode only when there is no `project-plan.md`. Skip it for explicit `continue` and `jump` invocations; do not create the project directory or
`project-plan.md` until this setup has completed.

1. Resolve the installed skill root (`$SKILL_DIR`) from the runtime's loaded skill path, falling
   back to the canonical-home probe in § Prerequisites. Run the checker in structured,
   side-effect-free mode:

   ```bash
   bash "$SKILL_DIR/scripts/check_requirements.sh" --json
   ```

2. Parse the JSON and explain it conversationally rather than dumping it:
   - `ready` means the capability is available.
   - `degraded` means a recommended/optional path is unavailable; name the affected phases and
     the documented fallback.
   - `blocked` means a required dependency is missing; name every affected phase.
   - For each non-ready check, show the exact `fixability.command`. Manual sudo, system,
     download, and environment actions are instructions for the user — print them, never run
     them or set environment variables.

3. If any non-ready check has `fixability.kind: safe-user`, present a native multi-select prompt.
   Include only options whose fix IDs appear in that JSON report; remove already-ready options.
   These are the complete allowed safe IDs:

   ```json
   {
     "questions": [{
       "question": "Which safe, user-scoped setup fixes may I run?",
       "header": "Setup fixes",
       "options": [
         { "label": "Install render browser", "description": "Fix ID: chrome-shell — downloads chrome-headless-shell to the user cache." },
         { "label": "Install HyperFrames skill", "description": "Fix ID: hyperframes-skill — installs the companion skill in an agent skill home." },
         { "label": "Install Whisper", "description": "Fix ID: whisper — runs pip3 install --user openai-whisper." }
       ],
       "multiSelect": true
     }]
   }
   ```

   Treat an empty selection as no consent. Validate every selected value against the safe fix IDs
   returned by the report, join only those IDs with commas, then execute exactly one scoped
   command:

   ```bash
   bash "$SKILL_DIR/scripts/check_requirements.sh" "--fix=$SELECTED_FIX_IDS"
   ```

   Never substitute bare `--fix` for a scoped consent response.

4. After selected fixes finish — or immediately when none were selected — re-run:

   ```bash
   bash "$SKILL_DIR/scripts/check_requirements.sh" --json
   ```

   Block entry to Phase 0 only while a `required` check remains `blocked`. Recommended or
   optional checks may remain `degraded`; explain the affected phases and fallback, then continue.

5. Before Phase 0, show this compact journey and its approval checkpoints:

   | Phase | Work | Approval/checkpoint before advancing |
   |---|---|---|
   | Phase 0 — Discovery | Understand product, audience, goal, and constraints | Approve `context.md`; Phase 1 is where the user chooses how it looks/sounds |
   | Phase 1 — Storytelling | Collect and confirm the user-owned story brief, then build the narrative | Confirm the complete brief before `storyboard.md`; approve the storyboard |
   | Phase 2 — Capture | Gather bound web (including an already-open authenticated Chrome tab), terminal, supplied, or native recordings | Approve the capture set and any fallbacks |
   | Phase 3 — Design | Define brand/motion and author scene HTML | Approve `DESIGN.md` and scene previews |
   | Phase 4 — Production | Wire the root composition and transitions | Approve the preview after the seam gate + lint + check |
   | Phase 5 — Audio & Render | Generate narration, music and SFX through the `media-use` audio engine, review captions, mix, render MP4 | Confirm title/path/source/license (or explicit none) before mixing; approve render |

   Mention that `screen-recording` capture is native where supported: macOS uses the
   `screencapture` adapter, Windows uses FFmpeg `gdigrab`, and X11 uses FFmpeg `x11grab`.
   Wayland is conditional on feature-detected `wf-recorder`; WSL uses an explicit Windows-host
   recording handoff followed by normalization with `stitch_clip.py`.
   If the product needs an already-open authenticated Chrome tab, explain that Phase 2 supports
   it after the user manually enables Chrome remote debugging and configures the Chrome DevTools
   MCP with `--autoConnect` (Chrome 144+). Do not enable it during onboarding.

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

**Then determine the product surface.** When a usable UI exists, recommend real captures as the
video's spine and explain why (Phases 1–3 build around them), but do not preselect that answer.
Only offer the no-product framing for a subject with no UI to capture (a CLI library, an API, a
pure-backend tool) or an explicitly abstract brand film. Present a selectable prompt:

```json
{
  "questions": [{
    "question": "Does the product have a UI we can capture and put on screen?",
    "header": "Surface",
    "options": [
      { "label": "Yes — capture the real product", "description": "Recommended when a usable UI exists: real screenshots/clips become the spine." },
      { "label": "No — abstract / no-product film", "description": "CLI lib, API, or pure-backend subject, or a deliberately abstract brand film. Waives the Phase-3 capture-coverage gate." }
    ],
    "multiSelect": false
  }]
}
```

Then create `{project-dir}/`, generate `project-plan.md` from `templates/project-plan.md`, and
record the explicit answers in the Creative Brief table as `mode: promo | showcase | tutorial`
and `product_surface: ui | none`. Do not mark either option selected before the user's response.
Carry the product surface into the `storyboard.md` frontmatter (`product_surface`) in Phase 1.
Begin Phase 0.

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

Read `{project-dir}/project-plan.md`, resolve the installed validator, and run it even when all
expected files exist:

```bash
python3 "$VALIDATOR" --project-dir "$PROJECT_DIR" status --json
```

Exit 1 means the table is incomplete or a legacy plan needs migration; still parse the JSON. A
structurally complete table may return 0 while `story.confirmed`, `audio.confirmed`, or phase
freshness is false, so always inspect those JSON fields. Exit 2 means malformed Markdown/state and
blocks resume with the validator's actionable error. The phase tracker is informational. The
validator's `earliest_stale_phase` plus the existing file-presence checks are authoritative. Never
delete stale artifacts automatically.

When `migration_required` is `true`, preserve the legacy plan and never promote its old defaults or
agent-inferred decisions into confirmed choices. Explain that migration inserts an empty Creative
Brief table, then present this consent prompt:

```json
{
  "questions": [{
    "question": "This project predates the confirmed Creative Brief schema. Insert an empty brief table and collect every choice from you?",
    "header": "Migration",
    "options": [
      { "label": "Migrate and collect choices", "description": "Preserve the legacy plan, insert placeholders atomically, then ask every Phase-1 brief question." },
      { "label": "Cancel resume", "description": "Leave project-plan.md unchanged and stop." }
    ],
    "multiSelect": false
  }]
}
```

Only after explicit migration consent, run:

```bash
python3 "$VALIDATOR" --project-dir "$PROJECT_DIR" migrate --json
```

The migration never infers values. Continue normal detection afterward: run Phase 0 first if
`context.md` is absent; otherwise route to Phase 1 to collect, summarize, and confirm every
user-owned story field before reusing or replacing any legacy storyboard.

**Detection logic:**
```
If no project-plan.md → report that there is no resumable project and switch to the normal "new"
  prompts, but preserve the explicit-continue origin: skip Phase -1 and begin at video-type selection
If validator migration_required is true → ask migration consent; on approval run migrate, then
  treat every story field as incomplete and route through Phase 0 if needed, otherwise Phase 1
If context.md missing → Phase 0
If validator story.complete is false, story.confirmed is false, or earliest_stale_phase is phase-1
  → Phase 1 (collect/reconfirm the complete story brief before storyboard creation)
If storyboard.md missing → Phase 1
Determine whether Phase 2 is needed from storyboard.md (frame metadata is the `- key: value`
  bullet block under each `## Frame N` heading; `product_surface` is a frontmatter key):
  - REQUIRED when frontmatter `product_surface` is `ui`, or any frame's `capture` bullet is
    screenshot, screencast, screen-recording, terminal, terminal-clip, or supplied.
  - SKIPPED when frontmatter `product_surface` is `none` and no frame requests capture.
If Phase 2 is required and any planned capture lacks its accepted output → Phase 2:
  - screenshot: the frame's bound `screenshot` exists and is non-empty
  - screencast: the exact bound `clip` exists and is non-empty, or the storyboard was explicitly
    rewritten to `capture: screenshot` and its bound `screenshot` exists and is non-empty
  - screen-recording: a positive `capture_duration` is present, an optional `capture_region` is a
    valid `x,y,w,h`, the exact bound `clip` exists and is non-empty, `<clip>.capture.pending` is
    absent, `<clip>.capture.json` is present (both named after the bound `clip` path), and
    `python3 scripts/capture_screen.py --check --duration "<capture_duration>"`
    `[--region "<capture_region>"] -o "<clip>"` passes (including sidecar request match,
    media contract, and fingerprint)
  - terminal: the authored terminal scene file exists and is non-empty
  - terminal-clip: non-empty MP4 exists, or the storyboard was rewritten to `capture: terminal`
    and its non-empty scene file exists
  - supplied: named supplied file exists and is non-empty
If no DESIGN.md or scenes/ → Phase 3
If no index.html → Phase 4
If no out/final.mp4 → Phase 5
If out/final.mp4 exists but
  `python3 "$SKILL_DIR/scripts/caption_gen.py" validate --audio voiceover-with-music.mp3
  --manifest captions-review.json --srt out/final.srt --vtt out/final.vtt
  --state .hve/captions-state.json` fails → Phase 5
Also map validator earliest_stale_phase phase-2..phase-5 directly to that phase, even when its
  files exist. Choose the earliest phase found by either validator state or file checks.
  A changed story field routes to Phase 1 because Phase 1–5 stamps no longer match.
  A changed final_music_track with the same confirmed story routes only to Phase 5.
```

### `jump`

Go directly to a specific phase only after checking current state. Run `status --json`; if its
`earliest_stale_phase` is earlier than the requested phase, reject the jump and route to that
earliest stale phase. Keep every existing file-presence prerequisite below, and add these
fingerprint requirements:

If `migration_required` is true, reject the requested jump. Use the same consent-gated migration
prompt as `continue`, then route through Phase 0 when `context.md` is missing or Phase 1 otherwise.
No legacy value may become confirmed without being presented to the user.

```bash
# Before Phase 2:
python3 "$VALIDATOR" --project-dir "$PROJECT_DIR" require phase-1
# Before Phase 3 / 4 / 5, require phase-2 / phase-3 / phase-4 respectively.
```

Phase 1 itself requires `context.md` and performs `confirm-story` before creating the storyboard.
Phase 5 performs `confirm-audio` after an exact track (or explicit none) is known and before any
mix/encode/render. Verify prerequisites:

```
Phase 1 requires: context.md
Phase 2 requires: context.md + storyboard.md + fresh Phase-1 stamp
Phase 3 requires: context.md + storyboard.md, plus completion of every capture requested by the
  storyboard, and a fresh Phase-2 stamp. Read the requests from each frame's `- key: value`
  bullet block; `product_surface` is a frontmatter key, not a frame bullet. In particular, a
  frame whose `capture` bullet is `screen-recording` requires a positive `capture_duration`, an
  optional valid `capture_region: x,y,w,h`, a non-empty file at the exact `clip` path, no
  `<clip>.capture.pending`, and a matching `<clip>.capture.json` sidecar — both markers are named
  after the bound `clip` path, not after a file called `clip`. Run
  `capture_screen.py --check` with that frame's `capture_duration` / `capture_region` / `clip`;
  if any check fails, BLOCK Phase 3 and resume Phase 2 (or return to Phase 1 to repair invalid
  fields). Frontmatter `product_surface: none` with no requested captures has no Phase-2 artifact
  prerequisite, but the intentional Phase-2 skip must still have a fresh Phase-2 stamp.
  Capture-coverage gate (orchestrator-enforced; promo/showcase only): before authoring
  scenes, if frontmatter `product_surface` is `ui` and NO storyboard frame binds an existing real
  capture (a `screenshot` or `clip` bullet naming a real file — `screenshot: none — connective
  tissue` binds nothing), BLOCK and resolve — return to Phase 2 to capture the
  product, or, if the film is genuinely abstract, set `product_surface: none` in the
  project-plan.md Creative Brief and in the storyboard.md frontmatter. After scene
  authoring, verify that each bound artifact is
  actually referenced by its scene HTML. Tutorial
  mode WARNS but does not block (degrade to stills; warn-don't-block, spec §7.3). This turns
  the former silent "(unless skipped, e.g. no real product)" escape hatch into an intentional,
  recorded decision. (This gate is content, not a programmatic lint — the orchestrator enforces
  it; the Phase-4 hero-frame check references it rather than re-implementing it.)
Phase 4 requires: context.md + storyboard.md + DESIGN.md + scenes/*.html + fresh Phase-3 stamp
Phase 5 requires: index.html (root composition) + fresh Phase-4 stamp; Phase 4's exit gate includes
  `SEAM_VERIFIER`, and re-timing scenes to the voiceover re-opens the seams it touches — re-run the
  seam gate before render approval. Phase 5 then confirms the
  exact audio fingerprint, runs `npx hyperframes lint` + `npx hyperframes check`, and requires
  reviewed `out/final.srt` + `out/final.vtt` whose caption state validates against the final
  mixed-audio fingerprint before stamping completion. Narration, music and SFX are generated by
  the `media-use` audio engine (AUDIO_ENGINE); with no engine installed, a confirmed `kokoro:`
  voice synthesizes locally via `npx hyperframes tts` (a confirmed `elevenlabs:` voice is never
  substituted — its takes must be user-supplied) and the music bed follows the brief's
  `music_strategy` — Freesound search via `scripts/search_music.py`, or user-provided. Neither
  path skips the exact-track confirmation, the caption review, or render approval.
Tutorial content mode: PREFERS public/clips/ but does not require them. Jumping into a
tutorial with no clips WARNS ("tutorial requested but no clips found — degrading to stills")
and continues with stills; it does NOT block. Missing captions in tutorial mode is the
stricter check (see Phase 5). (warn-don't-block; spec §7.3)
```

---

## Reasoning Pipeline

Sixteen stages carry a request from raw intent to builder prompts. They are not an extra phase —
each phase owns a contiguous span, and the modules under `reasoning/` and `grammar/` are where that
thinking is written down. The procedure for running them stays in the phase workflow (stages 4–14
in `workflows/phase-1-storytelling.md`); this table is the map, not the method.

| Stages | Phase | What happens |
|---|---|---|
| 1–3 · user intent · audience · communication goals | 0 | who this is for and what must land; every later cut is judged against these |
| 4–7 · story structure · beat extraction · emotional pacing · information hierarchy | 1 | the arc becomes frames carrying a `tone:`/`energy:` curve and a per-frame `density:` |
| 8–12 · visual semantics · metaphor · scene · camera · motion planning | 1, per frame | visual intelligence — judgment, guided by the grammars; no technology named |
| 13 · capability derivation | 1, per frame | the **mechanical** union of the capability tags declared by every grammar entry the frame cites, plus asset/subject realities — never a judgment call |
| 14 · runtime selection | 1, per frame; re-checked in 3 | capabilities become a runtime — GSAP-first, hero budget, and the rejected candidate recorded |
| 15 · rendering plan | 3 | design spec, registry blocks chosen before anything is hand-authored, one frame packet per scene |
| 16 · prompt generation | 3; again in 4 on a finding | each builder receives only its packet — that frame's own block, the design spec, and the inlined bodies of the recipes it cites |

Stages 8–14 run through `reasoning/scene-analysis.md`: it owns the per-frame question set, the
director keys those answers become, and — single-sourced — the cognitive-load budgets that every
other file cites without repeating a number. The vocabulary those stages choose from is
`grammar/camera.md`, `grammar/motion.md`, `grammar/metaphors.md`, and `grammar/three-taxonomy.md`;
the capability-tag vocabulary is owned and versioned by `reasoning/capability-catalog.md`.

**The grammars decide when and why; the HyperFrames ecosystem owns how.** Motion is cited by bare
rule or blueprint name, resolved through `RULES_INDEX` / `BLUEPRINT_INDEX`, and its mechanism is
never restated here. And the consent doctrine outranks the pipeline: a user's explicit creative
instruction overrides any derived verdict, including runtime selection and every budget — state the
tradeoff once, comply, and record `user_directed: true` on the frame.

---

## Pipeline

```
Phase 0: DISCOVERY ──── Phase 1: STORYTELLING ──── Phase 2: CAPTURE
  │                       │                          │
  ├ Design thinking       ├ Narrative structure      ├ Web / terminal / supplied
  ├ Codebase analysis     ├ Scene storyboard         ├ Auto-navigate app
  ├ Product context Q&A   ├ Emotional arc            ├ Screenshots + clips
  └ Goal/audience         └ Script outline           └ Bound capture artifacts

Phase 3: DESIGN ──── Phase 4: PRODUCTION ──── Phase 5: AUDIO & RENDER
  │                    │                        │
  ├ DESIGN.md          ├ HyperFrames root html  ├ media-use audio engine
  ├ Registry blocks    ├ Sub-comp wiring        ├ Reviewed captions
  ├ Frame packets      ├ Seam ledger + stamp    ├ Confirmed track + mix
  └ Scene builds       └ seam gate + lint/check └ npx hyperframes render
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

**Scenes are built from frame packets.** The director keys Phase 1 wrote onto each frame stop being
a planning record here. Step 3.3 assembles one **ephemeral** packet per frame — that frame's
storyboard block verbatim with its keys, `DESIGN.md`, the inlined bodies of the recipes the frame
cites, the scene-builder role, and the canvas / captions flag / bound capture paths — and a builder
returns exactly one scene HTML file from it, running no CLI and touching no other frame. Packets are
regenerated every run and never committed. Check the shipped catalog first (`REGISTRY_CATALOG`,
installed with `npx hyperframes add`): a tested block beats a hand-built scene, and hand-authoring is
for the gap. Up to ~6 short frames build faster inline than fanned out; past that, workers take 2–3
frames each and start in a single wave.

See [workflows/phase-3-design.md](workflows/phase-3-design.md)

### Phase 4: Production
**The gates live here, and so does re-dispatch.** A scene builder saw one frame and ran no CLI, so
`lint`, `check`, the seam gate and the hero-frame check — all of which need the assembled project —
run in this phase, and everything cross-frame (loader windows, track indices, the ledger, the audio
mount) is repaired here. A failure that lives *inside* one scene file goes back to its builder as a
regenerated packet plus one concrete finding: **one retry per frame**, never "make it better".

See [workflows/phase-4-production.md](workflows/phase-4-production.md)

### Phase 5: Audio & Render
**Audio generation is delegated to the `media-use` skill.** Its AUDIO_ENGINE produces narration,
the music bed (BGM) and SFX from one request and returns the assets plus per-line metadata. The
word timings in that metadata are **relative to each line's own audio**, so they are never the
caption clock: composition-absolute timing comes from TRANSCRIBE over the *assembled*
`voiceover.mp3`, with no provider branch — Phase 5 runs it whichever voice spoke.
**M6 removed the local *narration* acquisition fallback.** There is no local ElevenLabs generator
any more; `scripts/search_music.py` was retired with it but has since been **restored** — Freesound
search is the engine-free music path and the `freesound` strategy's engine, so the music bed is
never engine-gated. With no engine installed, narration is `npx hyperframes tts` on an explicitly
confirmed `kokoro:` voice; a confirmed `elevenlabs:` voice's takes must be user-supplied. What
survives in this repo is
`scripts/generate_voiceover.py --assemble-only` — the section assembler **both** paths use to place
narration at its exact start times. A confirmed voice provider is never substituted
automatically. A HeyGen credential does not change which voice speaks: the brief's `voice`
vocabulary is `elevenlabs:<name>:<id>` or `kokoro:<id>`, enforced by `scripts/validate_brief.py`,
so the engine's HeyGen voice route is not selectable through this skill's vocabulary. What the
credential buys Phase 5 is the engine's catalog retrieval for sound effects and for the music bed —
the retrieve-or-generate route being a user choice, because the two carry different licensing (see
`workflows/phase-5-audio.md` § Delegated strategy).

What this skill still owns and never delegates: the exact-track music confirmation — whatever
produced the candidate (catalog retrieval, generation, a manual Freesound download, or a
user-supplied file), the user confirms that exact track or an explicit none before any mix — the
`scripts/caption_gen.py` `draft` → `approve` → `finalize` → `validate` review contract over the
caption data, the verified
mix recipes, and render approval.
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
- **No full scene spinning** — No 360° rotations. Subtle tilt on mockups only, and every axis is capped: `rotateY` ≤ 8°, `rotateX` ≤ 4°, `rotateZ` ≤ 4°. State the axis whenever you state a limit — an unqualified "tilt ≤3°" leaves a builder to pick which rotation it governs (`grammar/camera.md` § Hard rules gives the reasoning for the asymmetry)
- **Seams are `SEAM_LAW`, not a rule of this file** — how a scene exits determines how the next one enters (axis, direction, speed, phase), so no scene hand-authors its own exit: the seam owns it, and only the closing scene (which has no seam after it) may animate out. `motion-doctrine` states that its rules supersede generic guidance, and `SEAM_STAMP` → `SEAM_VERIFIER` turn them into a numeric build gate. **Where prose here and the gate disagree, the gate is authoritative** — repair the seam ledger, never the assertion. A crossfade carries nothing across the cut: it is a dissolve, not a seam; the named seam techniques and their parameters are `CUT_CATALOG`. The gate governs how a boundary is executed, never which style the user confirmed (ADR-001)
- **This repo's additive seam bans — narrowing only, never overriding** — no `clipPath`-driven inter-scene wipe (polygon interpolation leaves an anti-aliased black sliver at the boundary; the render-side compositing rules are `SEAM_RENDER_MECHANICS`), and no 3D/perspective transforms as a seam effect — a Z seam is a signed *scale* change. Both further restrict what `SEAM_LAW` permits; neither is an argument against a gate verdict
- **Never animate `display`, `visibility`, or call `.play()` in timelines** — Breaks HyperFrames' deterministic seek; use `opacity` + `pointer-events`
- **Never animate `<img>` dimensions directly** — Causes layout recompute that confuses deterministic seek. Wrap each `<img>` in a non-timed `<div>` and animate the wrapper's `transform` (`scale`, `translate`) instead
- **Never use `tl.from()` for opacity tweens with stagger** — GSAP records the END state at registration; if CSS rest is `opacity:0` the recorded end is `opacity:0` and the animation goes nowhere. With stagger, later instances re-hide elements that earlier instances revealed. **Always use `tl.fromTo(target, {opacity:0,...}, {opacity:1,...}, pos)`.** See `patterns/visual-patterns.md` § "tl.from() stagger trap"
- **Never ship a partly wired `<video>` in a clip scene** — the runtime frame-syncs only videos carrying `data-start`. `lint` catches a *bare* one — `media_missing_data_start` and `media_missing_id` are both **errors** on the pinned CLI, and `check` skips the browser when lint errors. What no rule covers is a *partly* wired video: there is no lint code for `data-media-start` or for a media element's `data-track-index`, so a video with `id` and `data-start` but the wrong offset plays the wrong footage with every gate green. Every clip `<video>` carries the whole contract: `id` + `data-start="0"` + `data-duration` (the loader's full crossfade-extended window) + `data-media-start` (the frame's `clip_in` bullet) + `data-track-index="0"`. See `workflows/phase-3-design.md` § Clip scene

---

## Resources

- [workflows/](workflows/) — Phase workflow files
- [reasoning/](reasoning/) — The director's instrument: `scene-analysis.md` (per-frame questions, director keys, the single-source cognitive-load budgets) and `capability-catalog.md` (the capability-tag vocabulary and the capability→runtime procedure)
- [grammar/](grammar/) — When and why the camera moves, a motion principle applies, a metaphor explains, and when a frame earns Three.js: `camera.md`, `motion.md`, `metaphors.md`, `three-taxonomy.md`
- [compat/ecosystem.md](compat/ecosystem.md) — The only file holding upstream HyperFrames file paths; everywhere else names the skill plus a capability SYMBOL and lets this map resolve it
- [templates/](templates/) — Project scaffolding templates, including the copy-ready scene skeletons a frame packet ships as its starting point
- [sub-agents/](sub-agents/) — Role deltas for dispatched builders. `sub-agents/scene-builder-delta.md` is the scene-builder half of a frame packet: it re-points four conventions of `FRAME_WORKER_CORE` at this pipeline and adds the local law — the director keys are binding direction, a bound capture is the subject and is never redrawn, no number appears that the packet did not supply, one scene file out, no CLI
- [patterns/visual-patterns.md](patterns/visual-patterns.md) — Camera and depth on a captured still, the legibility floor, the emphasis-spending judgment and the repo DON'Ts; the motion mechanics themselves are delegated (`EASING_AND_STAGGER`, `RULES_INDEX`, `DETERMINISM_RULES`)
- [patterns/transition-catalog.md](patterns/transition-catalog.md) — Which transition fits which moment; seam law itself is `SEAM_LAW`, enforced by `SEAM_VERIFIER`
- [scripts/validate_brief.py](scripts/validate_brief.py) — Creative Brief validation, confirmations, fingerprints, and phase freshness
- [scripts/generate_voiceover.py](scripts/generate_voiceover.py) — voiceover-section assembly for **both** audio paths (`--assemble-only`): exact start times, silence spacers, pad to duration, overrun warning. Pure stdlib; no API key, no network. The ElevenLabs acquisition half was removed in M6
- [scripts/caption_gen.py](scripts/caption_gen.py) — Reviewed speech/speaker/sound captions bound to the final mixed-audio fingerprint

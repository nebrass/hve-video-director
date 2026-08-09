# Changelog

All notable changes to the **hve-video-director** skill are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

A remediation pass over a seven-agent audit of the skill (41 findings), plus an expert review
of the nine "premium motion" proposals that came out of it. The audit's P0 and P1 items shipped
as written. **Most of P2 did not**, and that is the substantive outcome: five of the nine
proposals contradicted decisions already recorded in the ADRs, and the real quality defects
turned out to be somewhere else entirely.

The through-line of the whole pass: this repo states most of its invariants in more than one
place, and every one of those duties had drifted at least once. What was missing was not
knowledge but enforcement — so nearly every fix below arrives with the guard that would have
caught it.

### Added

- **`keys-audit`** (`validate_brief.py`) — a structural audit of the director keys a storyboard
  carries: required keys, closed vocabularies, catalog tags, `blueprint:`/`motion:` presence, the
  hero-beat count, and every `runtime_rejected:` denial. It turns Step 1.4c, which was pure prose,
  into something a machine reads. It **reports and never gates** (`vo-budget`'s precedent, ADR-001),
  invents **no score** (ADR-005), reports **denials and never headroom** — "1 of 3 hero beats used"
  reads as an instruction to spend two more, and the contrast between flat and hero beats *is* the
  storytelling (ADR-008) — and **parses** its budget numbers out of the budget table rather than
  carrying a copy (ADR-008/C6).
- **`scripts/motion_register.py`** — reports when most of a scene's tweens share one ease across
  near-identical durations, resolving an ease held in a `var EASE = "…"` constant. That is the
  `same ease + same duration = same emotion` tell `patterns/anti-slop.md` names, and every
  mechanical gate passed it green because none was looking for character. Not a second
  `ANIMATION_MAP` (ADR-003): it reports no pacing verdict at all.
- **The staging contract** — a frame has to be lit, and it has to keep moving. One declared light
  direction per scene, which the ground origin, every shadow x-offset and the edge graze obey;
  three shadow layers with three jobs; a **named `transformOrigin`** on every camera move; one slow
  element still travelling when the seam fires; and static atmosphere (grain, vignette, resting
  blur). It ships through the two channels that reach a builder — the role delta and the scene
  skeletons — and refuses what it would otherwise invite: no pulse, no shimmer, no loop that fills
  silence.
- **`gsap-pin.json`** — the authoritative GSAP pin. Ten authored `<script>` tags must carry the
  version and hash as literals, so single-sourcing means naming the authority, not removing the
  copies. CI now re-fetches the pinned version and recomputes its SRI hash.
- **Nine new guard suites**, each for an invariant previously stated at several sites and enforced
  nowhere: the packet contract (ADR-004 — *the only major invariant in the repo with no test*), the
  execution-note registry, the voice map across its three sites, `compat/ecosystem.md`'s Used-by
  claims, the CLI-surface list, ADR citations, tilt caps, the staging contract, and `example/`'s
  consent record.
- **A provisioned CI job** that installs the HyperFrames ecosystem and runs the suite with
  `HVE_REQUIRE_ECOSYSTEM=1`, so the pointer-validity and storyboard probes — which ADR-007 calls
  the only thing protecting the registry — can no longer skip unnoticed.

### Changed

- **ADR status moved PROPOSED → ACCEPTED.** It had said PROPOSED since 2026-08-01 while M0–M6
  shipped against these decisions and every file cited them as binding law.
- **ADR-002 gained a precedence clause** for the recurring case where it and ADR-006 read as
  contradictory: this skill depends on upstream behavior no upstream file documents. ADR-006 decides
  where the capability belongs, ADR-002 decides what may be committed meanwhile, ADR-007's compat
  map is the register, and retirement waits for a real end-to-end run.
- **`surface_reading:` is the fifteenth director key**, emitted by a new Q13 (conditional: fires
  only where `material-realism` was derived and `runtime: three` selected). `grammar/three-taxonomy.md`
  had told frames to carry a surface reading since M1, correctly and unrecorded; it is now a key
  like any other. **ADR-010 proposed a second "execution note" vocabulary for this and was
  superseded the same day** — an adversarial review found that a parser split had shipped inside
  its own commit, that its stated ground for rejecting a fifteenth key was circular and false, that
  its boundary contradicted ADR-008's traceability clause, and that `keys-audit` could not see a
  misspelled note at all. The record is kept with the reasons. What survived is the better half:
  the cap on undeclared frame bullets now has *no* legal exit — add the question, or do not write
  it on a frame.
- **`SUBCOMP_CLONE_SEMANTICS`** registered as a behavior probe — a cloned module script throws,
  native `window` calls hit an injected scoped Proxy, and `hf-seek` delivers the **root** clock to a
  scene that believes it starts at zero. All three fail only once the film is assembled, with every
  gate green.
- **The tilt caps cover all three axes.** `rotateX` was usable, used in a sanctioned example, and
  capped nowhere; two presets said "Tilt ≤3°" naming no axis at all.
- **Q7's mapping is named.** The question that decides a frame's spatial tag said "the spatial tag
  it names" without naming the mapping, leaving the one step that turns a yes into a tag to be
  re-read per frame — the taste-shaped hole ADR-005 requires derivation not to have.
- **Phase 5's overlap-repair loop** is scoped to consented repairs: a word cut mid-syllable now
  goes to the user rather than being silently re-timed (ADR-001).

### Fixed

- `generate_voiceover.py` — a path containing an apostrophe broke concat-list quoting; ffmpeg's
  stderr was swallowed on failure.
- `verify_vo_sections.py` — `prepare` overwrote the pending marker instead of union-merging, so a
  second partial round could lose the record of what the first had cleared.
- `caption_gen.py` — `draft` now enforces its own delivery invariants: minimum cue duration
  (extend → borrow → merge) and line wrapping, with the audio duration probed *before* grouping.
- `capture_screen.py` — a Wayland recorder's startup cost is no longer charged against the clip's
  own duration.
- Freshness manifests are written atomically (tmp + fsync + `os.replace`).
- `SKILL.md` — stale claims that contradicted the phase-5 workflow about which audio paths exist,
  and a frontmatter/hygiene pass. `SKILL.md` is now covered by the instruction-parity suite, which
  had never included the one file every session reads.

### Security

- The provisioned CI job **executes** upstream code by design (the storyboard round-trip probe
  imports an upstream ESM module and drives it under node), and `skills-lock.json` — a file any PR
  can edit — decided what got cloned, with no validation. The source is now allowlisted and a
  `skillPath` may not escape its checkout. That stops the accident, not a hostile PR; what bounds
  the blast radius is the job holding nothing worth taking, so the constraint is now written where
  someone would break it: no secrets, read-only token, and never `pull_request_target`.

### Rejected, with reasons recorded

Five audit proposals were refused on recorded grounds rather than implemented: a hero
**under-spend report** (converts a ceiling into a quota and re-reads `visual_ceiling: derived` as
authorization to spend), a **`depth-staging` capability tag** (duplicate — `spatial-depth` already
spans both tiers and the discriminator is self-occlusion), an **atmosphere floor of ambient
motion** (banned by name in four files, and it would have masked the frozen-tail defect rather than
fixing it), a committed **`templates/scene-three.html`** (ADR-006 routes new scene archetypes to the
registry), and a **local `three` pin** (this repo authors no `three` version — `THREE_ADAPTER` owns
it). Elevation prompts and a retention tie-break were refused for the same reason as the first:
they move a decision from derivation to taste.

## [0.2.0] - 2026-08-04

Rebases the skill on the **HyperFrames ecosystem** ([#34](https://github.com/nebrass/hve-video-director/pull/34), milestones M0–M6). The finding behind it: roughly 70–85% of the phase prose had drifted into a hand-maintained shadow copy of the upstream manual, while the ecosystem had shipped real owners for nearly all of it. This release deletes the shadow copy and keeps the layer that has no upstream equivalent — the consent doctrine, revision fingerprints, capture determinism, and reviewed captions.

No generated project is stranded: nothing is gated on the storyboard's shape, and a project created before this release still resumes.

### Added

- **The reasoning layer** (M1) — `reasoning/` and `grammar/` are first-class skill directories, not documentation. `reasoning/scene-analysis.md` owns the twelve per-frame questions, the closed set of director keys, and — single-sourced — the cognitive-load budgets. `reasoning/capability-catalog.md` owns and versions the capability-tag vocabulary and turns a frame's derived tags into a runtime. `grammar/camera.md`, `motion.md`, `metaphors.md` and `three-taxonomy.md` supply the vocabulary those stages choose from.
- **`compat/ecosystem.md` — the compatibility thin waist** (ADR-007). The only file in the repo permitted to hold intra-skill paths for ecosystem skills: capability symbols, the CLI surface, behavior probes, and the pin/update policy. Everywhere else names a skill plus a capability SYMBOL and lets that map resolve it, so an upstream relayout is a one-row edit. Enforced in both directions by `test/unit/test_compat_pointers.py`.
- **Frame packets** (M5) — a scene builder now receives one ephemeral packet per frame (that frame's storyboard block verbatim with its director keys, `DESIGN.md`, the inlined bodies of the recipes it cites, the builder role, and the bound capture paths) and returns exactly one scene file. Packets are regenerated every run and never committed. Role delta: `sub-agents/scene-builder-delta.md`.
- **A numeric seam gate** (M3) — transition quality was previously enforced by prose DON'Ts. Phase 4 now writes a seam ledger, stamps the master seams from it (`SEAM_STAMP`), and verifies them (`SEAM_VERIFIER`, `motion-doctrine`). Velocity-matched cuts become checkable ledger rows; dissolves cannot be ledger rows, and Phase 4 reports the unverified boundary count either way.
- **The official storyboard shape** (M4) — generated `storyboard.md` adopts `STORYBOARD_FORMAT`, buying the upstream parser, the Studio contact-sheet review, and the structured `.hyperframes/frame-comments.json` feedback channel. This skill's own keys ride along as extra bullets and are preserved verbatim; the `STORYBOARD_EXTRA_KEYS` probe guards that assumption in `bash test/run.sh`. `validate_brief.py storyboard --json` reports a project's shape, and `migrate-storyboard` converts one **only when the user asks**, preserving the original alongside it.
- **Architecture decision records** ADR-001…ADR-008, plus the 29-section design review that produced them.

### Changed

- **Phase-5 audio generation is delegated** to the `media-use` audio engine (M2) — narration, music bed and SFX from one request. Delegation stops at generation: the exact-track music confirmation, the caption review state machine, the verified mix recipes, and render approval remain this skill's governance (ADR-001).
- **`npx hyperframes check` is the required final gate**; `validate`, `inspect` and `layout` are deprecated aliases that announce themselves under `--json`.
- **`example/` is regenerated** as a real end-to-end run against the HyperFrames-first pipeline, with every per-phase approval given by a human. Its `.hve/brief-state.json` is the consent record that makes the claim checkable.
- **`BRIEF_FORMAT` was deliberately NOT adopted.** Its companion contract skips questions the request already answers, which contradicts this skill's consent doctrine — recommend, never preselect. `project-plan.md` remains the Creative Brief and the single record of the levers the user owns.

### Removed

- **The local acquisition fallbacks** (M6). `generate_voiceover.py` loses its ElevenLabs half and its Whisper verification pass; the file itself survives and must not be deleted, because `--assemble-only` is the section assembler **both** audio paths still use. With no engine installed, narration is `npx hyperframes tts` on an explicitly confirmed local voice and the music bed is user-provided.

### Fixed

- **Sparse keyframes in normalized terminal clips** ([#35](https://github.com/nebrass/hve-video-director/pull/35)). `agg` emits change-only frames, so on mostly-static terminal output x264 could leave keyframes many seconds apart — a real capture produced an 8.33s interval, and the renderer then reports `sparse keyframes … causes seek failures and frame freezing` and renders the clip black or frozen **while `lint`, `check` and the seam gate all pass green**. The normalize recipe now pins `-g`/`-keyint_min` to the output fps in all five places it appears, and `scripts/stitch_clip.py` derives the GOP from its `--fps` argument so the two cannot desync. New `test/unit/test_stitch_clip.py` pins the interval at 24/25/30/50/60 fps.

## [0.1.0] - 2026-07-26

### Changed — BREAKING

- **The skill is renamed `hve-spielberg` → `hve-video-director`.** The previous name
  referenced a living public figure, which carried trademark and right-of-publicity
  exposure and implied an endorsement that never existed. The new name describes what the
  skill actually does, pairing an explicit domain (`video`) with the role it performs
  (`director`).

  **You must remove the old install — `npx skills update` does not complete the rename.**
  Because the old repository URL redirects, `update` resolves the new `SKILL.md`, keys it by
  its frontmatter `name`, and installs `hve-video-director` *alongside* `hve-spielberg`. It
  reports `✓ Updated 1 skill(s)` but never removes the old directory or its lock entry, so you
  are left with both — a live 0.1.0 and a stale 0.0.4 that still declares the old name and
  remains loadable by your agent. It also never converges: every later `update` reports the
  same pending update again.

  ```bash
  npx skills remove hve-spielberg --global
  npx skills add nebrass/hve-video-director --global
  ```

  See [`MIGRATION.md`](MIGRATION.md) for per-runtime instructions, including `git clone`
  installs and the Claude Code plugin marketplace.

  | | Before | After |
  |---|---|---|
  | Invocation | `/hve-spielberg` | `/hve-video-director` |
  | Repository | `nebrass/hve-spielberg` | `nebrass/hve-video-director` |
  | Install dir | `<skills-home>/hve-spielberg/` | `<skills-home>/hve-video-director/` |
  | Plugin name | `hve-spielberg` | `hve-video-director` |

  **Existing generated video projects are unaffected** — project scaffolding never embedded
  the skill name (`templates/` contains no reference to it). No phase, workflow, script, CLI
  flag, or file-format changed.

### Added

- **[`TRADEMARKS.md`](TRADEMARKS.md)** — nominative attribution for every third-party mark the
  skill references (runtimes, tooling, and the ten `design-systems/` brands), a statement that
  the design-system presets are original written descriptions rather than copied brand assets,
  and the licensing terms that attach to generated output.
- **[`MIGRATION.md`](MIGRATION.md)** — the `0.0.x` → `0.1.0` upgrade guide.
- **Rename-resilient skill resolution.** The `$SKILL_DIR` probes in `SKILL.md`,
  `workflows/phase-3-design.md`, and `workflows/phase-5-audio.md` now fall back to matching the
  skill's declared frontmatter `name` when no directory carries the expected name, so a clone left
  under a pre-`0.1.0` directory name still resolves instead of failing mid-pipeline. Matching
  identity rather than file layout means no unrelated skill sharing a skills home can be selected.

### Note

This release also carries the end-to-end pipeline hardening merged in
[#22](https://github.com/nebrass/hve-video-director/pull/22), which was not separately
changelogged.

## [0.0.4] - 2026-06-23

### Added

- **`scripts/check_requirements.sh` — toolchain doctor.** Verifies every prerequisite
  (Node ≥18, Python ≥3.10, ffmpeg/ffprobe, `chrome-headless-shell` via `hyperframes doctor`,
  the `hyperframes` CLI, the `hyperframes`/`gsap` companion skills across all `$SKILL_HOMES`,
  and the ELEVENLABS/FREESOUND env vars). Reports with ✓/○/✗ and per-OS install hints
  (macOS/Linux/WSL2 detected). `--fix` auto-installs the user-scoped pieces (companion skills via
  `npx skills add`, `chrome-headless-shell`, `pip --user openai-whisper`) and **prints — never
  runs — sudo/system commands**. Exit 1 if any required item is missing. On WSL it flags the
  `--docker` render path. Runs from a local checkout **or directly from GitHub** with no clone —
  `curl -fsSL …/scripts/check_requirements.sh | bash` (append `bash -s -- --fix` to auto-install).
- **GitHub Copilot CLI support — the skill is now agent-agnostic.** `hve-video-director`
  runs on both **Claude Code** (`~/.claude/skills/`) and **GitHub Copilot CLI**
  (`~/.copilot/skills/`). A new **Runtime Compatibility** section in `SKILL.md`
  documents the runtime-neutral conventions used throughout the workflows:
  - `{"questions": […]}` interaction blocks are a neutral schema rendered as a native
    multiple-choice prompt per runtime (`AskUserQuestion` on Claude Code, `ask_user`
    on Copilot CLI).
  - `Skill(<name>)` means "load that companion skill the way your runtime does it".
  - Companion skills (`hyperframes`, `gsap`) and helper scripts are resolved from
    **both** `~/.claude/skills/` and `~/.copilot/skills/`.
  - The `SKILL.md` frontmatter keeps the Claude Code skill schema; Copilot CLI loads
    the skill from `name`/`description` and harmlessly ignores the Claude-only fields.
  - Prerequisite probes, the Phase 3/5 `SKILL_DIR` resolution, and the `patterns/`
    references now detect either skills home.
  - `README.md`, `CLAUDE.md`, and `.github/copilot-instructions.md` document
    installation and usage for both agents.
- **Claude Code plugin manifest + skills-CLI-first install docs.** Added root-level
  `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` (MIT; skills source points at
  the repo root `./` because `SKILL.md` lives at the root, not under `skills/`), plus a root
  `AGENTS.md` pointer. `README.md`, `CLAUDE.md`, and
  `.github/copilot-instructions.md` now lead with
  `npx skills add nebrass/hve-video-director [--agent github-copilot] [--global]` and collapse
  the hand-paired `~/.claude` / `~/.copilot` git-clone and `cp -r` install blocks into a
  single CLI path with one manual git-clone fallback — the CLI auto-detects the agent and
  resolves its scanned skills home.
- **OpenCode & Pi support (documented).** Both agents discover skills by directory
  convention and read the same Agent Skills `SKILL.md` format. OpenCode scans
  `.claude/skills/`, `~/.claude/skills/`, `.agents/skills/`, `~/.agents/skills/`,
  `.opencode/skills/`, `~/.config/opencode/skills/`; Pi scans `~/.pi/agent/skills/`,
  `~/.agents/skills/`, `.pi/skills/`, and project `.agents/skills/` (once trusted).
  Since `npx skills add nebrass/hve-video-director` already installs a `<name>/SKILL.md`
  subdir into a scanned home, no plugin or `package.json` is needed — both pick the
  skill up natively and load it on demand. Documented in `README.md` and `AGENTS.md`.
  Skill *loading* follows each agent's documented convention; a full Phase 0→5 run on
  OpenCode/Pi is not yet verified (proven on Claude Code and GitHub Copilot CLI).

### Documentation

- **Codex & Cursor are natively discovered — dead manifests removed.** Per the official
  [Codex](https://developers.openai.com/codex/skills) and [Cursor](https://cursor.com/docs/skills)
  skills docs, both agents discover skills by directory convention (scanning `.agents/skills/`,
  `.claude/skills/`, etc.) and read **no** `plugin.json` manifest. The `.codex-plugin/` and
  `.cursor-plugin/` manifests shipped earlier were no-ops, so they are removed; only Claude Code
  uses a manifest (`.claude-plugin/`). `README.md` and `AGENTS.md` now group Codex and Cursor with
  OpenCode and Pi under native discovery — `npx skills add` installs into a scanned home and all
  are picked up natively. Skill *loading* follows each agent's documented convention; a full Phase
  0→5 run on these agents is not yet verified (proven on Claude Code and GitHub Copilot CLI).

### Changed

- **Phase 5 audio mix and render hardened from a real Copilot CLI end-to-end run.** Two
  environment fixes verified by rendering the `example/` build to MP4:
  - The sidechain mix now forces both legs to stereo with
    `aformat=…:channel_layouts=stereo` (was a bare `aresample=44100`). ElevenLabs and the
    `hyperframes tts` fallback often emit a **mono** voiceover, and `sidechaincompress` aborts
    (`Failed to inject frame into filter network`) when the key and music differ in channel
    layout. Updated in `workflows/phase-5-audio.md` and `example/README.md`.
  - Documented the WSL2 render path: native render can fail at
    `Protocol error (Page.captureScreenshot)`; add `--docker` to render in a container, and on
    machines with ≤8 GB RAM also add `--no-low-memory-mode` (low-memory mode forces the failing
    screenshot capture). Added to the Phase 5 "Known issues" list and the `example/README.md`
    render step.
- **Phase 5 music mix now sits the soundtrack under the voice as a ducked bed.**
  The static `volume=0.22` blend in `workflows/phase-5-audio.md` is replaced with:
  music normalized to a known base (`loudnorm I=-30`), EQ space carved for speech
  (`highpass=100` + `-3 dB @ 2.5 kHz`), and **sidechain ducking** keyed off the
  voiceover so the music dips under speech and breathes back in the gaps. Mastered
  with a peak limiter (`alimiter`, ~-1 dBFS) while the voiceover's -16 LUFS
  normalization carries loudness — a dynamic `loudnorm` master was rejected
  because it rides gain and reverses the duck. `aresample` guards keep
  mismatched-rate sources working through `amix`. `example/README.md` updated to
  match.

### Fixed

- **True-peak ceiling breach in the audio master.** The old `alimiter=limit=0.95`
  could leave the final mix above the -1 dBTP target (measured true peak -0.3 dBTP); the
  new master lands well under it (~-3.8 dBTP). The Step 5.3a clip-audio re-master is
  aligned to the same ceiling.

## [0.0.3] - 2026-06-08

Added a professional, skill-driven asciinema + agg CLI recording path so
terminal scenes can be captured autonomously — no user keyboard required.
The prior Phase 2 path treated asciinema as a one-line user-side note;
this release wires it as a first-class capture source on par with Chrome
DevTools screenshots and screencast clips.

### Added

- **Autonomous asciinema recording.** The skill drives `asciinema rec
  --command "<cmd>"` itself via its Bash tool: PTY-isolated, env-scrubbed
  (`env -i HOME=$HOME PATH=$PATH SHELL=/bin/bash PS1='$ '`), and bounded
  by `timeout Ns` so runaway / non-terminating commands can't stall the
  phase. The user never opens a terminal. `agg` then renders the cast to
  MP4 in the same autonomous sequence.
- `patterns/cli-terminal-capture.md` — end-to-end guide: when to use the
  asciinema path vs. the authored-terminal fallback, install per OS,
  autonomous recording sequence, edge cases (long-running commands,
  piped input, secrets-without-leaking, PTY allocation fallback to
  `script -qc`), agg theme→palette pairing, quality gate, troubleshooting.
- `templates/scene-terminal-clip.html` — Layer-A clip-scene archetype that
  wraps the agg-rendered MP4 in a macOS-style window for brand parity
  with browser-mockup scenes. Animates the `.term-frame` wrapper only
  (respects the no-`<video>`-dimension-tween rule).
- `templates/storyboard.md` — new `Capture: terminal-clip` value plus
  required `Command:` and `Record timeout:` fields so storyboards carry
  the inputs the autonomous path needs.
- README "Updating" section documenting how to pull the latest skill
  version (carried over from Unreleased).

### Changed

- `SKILL.md` frontmatter — `description` broadened so Phase 2 reads as a
  multi-source step ("Chrome DevTools screenshots + screencast clips,
  asciinema terminal recording") instead of screenshots only;
  `allowed-tools` gains `Bash(asciinema:*), Bash(agg:*),
  Bash(timeout:*), Bash(ffprobe:*)`; prerequisites block prints an
  actionable per-OS install hint when asciinema/agg are missing.
- `workflows/phase-2-capture.md` — replaces the 3-line asciinema note
  with the full autonomous record → render → verify sequence,
  preconditions, and the edge-case matrix.
- `README.md` prerequisites table — concrete install commands and a link
  to the new pattern doc.
- `patterns/INDEX.md` and `CLAUDE.md` — register the new pattern doc and
  template so future editing sessions find them.

### Fixed

- **Clip `<video>` timing contract.** Clip scenes previously used a bare
  `<video>` and told authors *not* to add timing attributes. The runtime only
  frame-syncs videos carrying `data-start`, so with 2+ clip scenes footage
  cross-routed (one scene played another's footage, another played black)
  while `lint`/`inspect`/`validate` all passed green. Both clip templates and
  the phase-3/4 docs now mandate the explicit contract: `id` +
  `data-start="0"` + `data-duration` + `data-media-start` +
  `data-track-index="0"`. Also added to the central `## DON'Ts` list and as a
  carve-out in `patterns/transition-catalog.md`.
- **`Clip in/out` trim now lands in the scene** via `data-media-start`
  (= storyboard `Clip in`). Previously the trim was silently ignored — the
  video played from source `t=0` and desynced from Phase 5's clip-audio
  extraction (`CIN`).
- **Clips no longer blank during crossfades.** The inner video's
  `data-duration` is the scene loader's full crossfade-extended window (per
  `patterns/transition-catalog.md`), not the bare clip length — an
  expired track goes `visibility:hidden` mid-crossfade otherwise.
- **Phase 1 now surfaces `Capture: terminal-clip`** (with `Command:` /
  `Record timeout:`) so new-mode storyboards can actually trigger the
  autonomous asciinema path.
- **asciinema record env keeps `LANG`** (`LANG="${LANG:-C.UTF-8}"` through
  `env -i`) — asciinema 2.x aborts without a UTF-8 locale.
- **agg no longer passes `--cols`/`--rows`** — it reads the size from the
  cast header; the previous hardcoded `144×32` mismatched the recorded
  `175×32` and wrapped/letterboxed wide output. The intermediate GIF now goes
  to `$TMPDIR` instead of `public/clips/`, and the verify step reads
  `nb_frames` from the header instead of a full `-count_frames` decode.
- **`timeout` is feature-detected** (GNU coreutils; absent on stock macOS —
  install hint now says `brew install asciinema agg coreutils`), and the
  PTY-failure fallback documents both `script` syntaxes (GNU `-qc` vs
  BSD/macOS positional). `allowed-tools` gains `Bash(script:*)` and
  `mcp__chrome-devtools__emulate` (used for viewport + dark-mode emulation).
- **Dark-mode MutationObserver guidance inverted to the working order** —
  inject *after* `navigate_page` (navigation wipes the page's JS context;
  hydration re-renders don't navigate, so the observer survives them).
- **Mandatory hero-frame content check in Phase 4** (`inspect --at` scene
  midpoints, then read the PNGs) — the mechanical gates can't see wrong
  content; this is how the bare-`<video>` cross-route shipped unnoticed.

### Security

- **Subresource Integrity on the GSAP CDN tag.** Every `<script>` loading
  `gsap@3.14.2` from jsDelivr (4 templates, the phase-3/phase-4 skeletons, and
  all `example/` scenes) now carries `integrity="sha384-…" crossorigin="anonymous"`,
  so a tampered CDN response is rejected by the browser instead of executing in
  `preview`/render. `CLAUDE.md` documents the hash-recompute step required on any
  future GSAP version bump.

### Unchanged (by design)

- If `asciinema`/`agg` are missing, the skill silently falls back to the
  authored-terminal scene (`templates/scene-terminal.html`). No install
  prompts — the user is told once, then Phase 2 proceeds.

## [0.0.2] - 2026-06-04

Migrated the rendering engine from **Remotion** (React, server-rendered) to
**HyperFrames** (HTML + GSAP + headless Chromium) across the whole 6-phase
pipeline, then extended it with first-class video-clip capture and a new
tutorial content mode. Released via [PR #2](https://github.com/nebrass/hve-video-director/pull/2).

### Changed

- **Rendering engine: Remotion → HyperFrames.** All six `workflows/phase-*.md`
  rewritten. New scene authoring model (sub-compositions + `data-composition-id`
  + GSAP timelines registered on `window.__timelines`) replaces Remotion JSX
  compositions. Phase contracts (the `continue`/`jump` detection logic,
  prerequisite lists, project-structure diagrams) updated end-to-end across
  `SKILL.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`.
- Phase 2 capture contract generalized from "screenshots" to **capture
  artifacts** (`public/screenshots/` and/or `public/clips/`).
- `patterns/visual-patterns.md` fully rewritten for GSAP — adds the
  `tl.fromTo()` stagger-trap rule, `autoAlpha` guidance, and `tl.set` for
  late-entry elements.
- `patterns/metallic-swoosh.md` reworked as an inline root-timeline pattern
  (transitions straddle two scenes and can't be sub-comps).

### Added

- **Tutorial / walkthrough content mode** — a third mode beside promo and
  showcase: task-ordered chapters with a cold-open on the payoff, required
  baked captions, footage-time legibility punch-in for sub-24px UI text,
  a recap archetype (`templates/scene-recap.html`), a "Step N of M" / chapter
  overlay, and a ~90s segment cap. Warns-and-degrades to stills when clips are
  absent; missing captions is the only hard gate.
- **Video-clip capability** — real motion footage as a first-class,
  source-agnostic capture artifact:
  - _Capture target_ — clip-scene archetype `templates/scene-clip.html`
    ("Wiring S"): a muted `<video>` in a sub-composition, `currentTime`-synced
    by the runtime; footage-locked durations (`data-duration = (out - in) / speed`).
    Optional per-scene storyboard clip fields (`Capture`, `Clip`, `Clip in/out`,
    `Speed`, `Clip audio`, `Captions`).
  - _Capture sources_ — Chrome DevTools `screencast` for web (experimental,
    feature-detected, falls back to screenshots) and a dependency-free terminal
    path for CLI (`templates/scene-terminal.html`, with optional `asciinema`+`agg`),
    plus a footage quality gate (resolution/fps floor, one-clean-take review).
- **10 vendored brand design presets** in `design-systems/<slug>/DESIGN.md`
  (Stripe, Linear, Apple, Notion, Vercel, Airbnb, GitHub, Cal, Arc, Bento) —
  original MIT-licensed prose — plus `design-systems/CONTRIBUTING.md` codifying
  the quality bar.
- New pattern files: `patterns/INDEX.md` (wayfinding), `anti-slop.md`,
  `marker-highlight.md` (5 word-emphasis modes), `transition-catalog.md`.
- `example/` — a self-contained reference promo project built by the pipeline
  itself (storyboard, design seed, 5 scene HTMLs, `voiceover.py`,
  `example/README.md` reproduction guide).
- `CLAUDE.md` — codebase guide for future Claude Code sessions, and a top-level
  `.gitignore`.
- Opt-in clip-own audio mixed under a ducked voiceover (sidechain) in Phase 5,
  with an ffprobe gate proving it reaches `out/final.mp4`.
- CLI inventory entries `add` and `doctor`; `screencast_*` + `resize_page`
  added to `allowed-tools`.

### Fixed

- `scripts/generate_voiceover.py` hardening: absolute-path ffmpeg concat,
  list-or-dict transcript parser, `mktemp` → `mkstemp`, non-zero exit on a
  failed TTS section, guards for null word timestamps and ffprobe `N/A`
  durations, a mid-loop tempfile leak, word-level timestamps for overlap
  detection, and voiceover-overrun warnings.
- HyperFrames `lint`/`inspect`/`validate`/`render` gates take a project
  directory, not a file.
- `gsap.from()` → `tl.fromTo()` (the stagger trap) across workflows, patterns,
  and templates.
- Three rounds of Copilot review fixes plus a max-effort code-review pass
  (phase-contract, no-music audio path, audio element id, design-system refs,
  license posture, and example consistency).

### Removed

- The Remotion / React rendering path.
- The committed `example/out/final.mp4` binary (3.4 MB) — no longer tracked in
  git (regenerable build artifact; the demo lives on YouTube).

## [0.0.1] - 2026-04-28

Initial release of the hve-video-director skill.

### Added

- 6-phase AI video production orchestrator (`SKILL.md`) with per-phase approval
  checkpoints and `new`/`continue`/`jump` entry modes: Discovery → Storytelling
  → Capture (Chrome DevTools screenshots) → Design → Production → Audio & Render
  (Remotion-based rendering).
- Promo and showcase content modes.
- ElevenLabs voiceover generation with Whisper timing verification
  (`scripts/generate_voiceover.py`).
- Freesound CC music search (`scripts/search_music.py`), switched over from an
  earlier Pixabay integration.
- README with install instructions and an MIT license.

[Unreleased]: https://github.com/nebrass/hve-video-director/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/nebrass/hve-video-director/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/nebrass/hve-video-director/compare/v0.0.4...v0.1.0
[0.0.4]: https://github.com/nebrass/hve-video-director/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/nebrass/hve-video-director/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/nebrass/hve-video-director/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/nebrass/hve-video-director/releases/tag/v0.0.1

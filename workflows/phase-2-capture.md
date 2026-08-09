# Phase 2: Capture (web, native screen, terminal, or supplied media)

Automatically capture **artifacts** (still screenshots and/or recorded clips) for use in video scenes.

Tool names in this workflow are capability names. Resolve their exact runtime-specific identifiers
using `SKILL.md` § Runtime Compatibility before invoking them; do not copy Claude Code's
`mcp__...` qualification into another agent.

Before doing any Phase-2 work, require the accepted storyboard to match the current confirmed
story fingerprint:

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" require phase-1
```

A nonzero exit routes back to Phase 1 even when `storyboard.md` exists.

Read the confirmed `theme` from the Creative Brief before capture. Every capture must show that
theme: emulate the selected color scheme for navigated web apps, ask the user to prepare it in an
attached authenticated tab, configure native apps before recording, and choose a matching
terminal theme. If the product cannot render the confirmed theme, return to Phase 1 and let the
user change `theme`; never capture the opposite theme and silently recolor it.

## Phase 2 routing

Everything this phase reads from `storyboard.md` is either a frontmatter key (`product_surface`,
`capture_plan`, `web_capture_source`) or a `- key: value` bullet in a frame's metadata block
(`capture`, `screenshot`, `clip`, `capture_duration`, `capture_region`, `command`,
`record_timeout`). Read `product_surface` and every frame's `capture` bullet before asking for a
web source:

- If `product_surface: none`, `capture_plan` plans no artifacts (Phase 1 writes
  `none — skip Phase 2`), **and every frame has `capture: none`**, mark Phase 2 **skipped** in
  `project-plan.md` and proceed to Phase 3. If any frame requests capture, that frame wins over a
  stale `capture_plan`. Do not ask for a URL and do not create empty directories as fake
  completion markers. Use the checkpoint's Phase-2 stamp to record the intentional skip before
  proceeding.
- Run the web path (Steps 2.1–2.2) only for `screenshot` or `screencast` frames.
- Run the native screen path only for `screen-recording` frames.
- Run the terminal path only for `terminal` or `terminal-clip` frames.
- For `supplied`, verify the storyboard's exact file exists and is non-empty.
- If `product_surface: ui` but no real product artifact is bound to a frame (web capture,
  native screen recording, or supplied screenshot/clip), return to Phase 1 and repair the
  capture plan; the real product cannot be the spine without a bound artifact.

## Capture artifacts: stills and clips

Phase 2 produces **capture artifacts**: still screenshots in `public/screenshots/`
and/or recorded clips in `public/clips/`. A frame's `capture` bullet (from the
storyboard) decides which. Recording sources (Chrome screencast for web, the
native screen helper for desktop/non-browser apps, and the terminal path for CLI)
are wired in **Layer B**; in Layer A, clip scenes consume a
`public/clips/scene-{NN}-{slug}.mp4` produced by any source (including a user-supplied
file). Stills remain the default and the fallback.

### Capture-source detection (graceful, never hard-fail)

A frame's `capture` value selects a source; each is feature-detected and degrades cleanly:

- `none`: no Phase-2 work for that connective frame.
- `screenshot` / `screencast` under the frontmatter `web_capture_source: attached-session`:
  requires a Chrome DevTools MCP connection to the user's running browser. If `list_pages` fails
  or the selected tab disappears, pause with the documented setup/re-authentication handoff;
  never open or navigate a replacement page automatically.
- `screencast` (web): usable only if the chrome-devtools MCP exposes `screencast_start`
  AND the server was started with `--experimentalScreencast=true`. Detect by attempting
  it; if the tool is absent or it errors about the flag, **fall back to `take_screenshot`**,
  set that frame's `capture: screenshot`, and tell the user how to enable it:
  restart the chrome-devtools MCP server with `--experimentalScreencast=true`.
- `screen-recording` (native desktop/non-browser app): requires a positive
  `capture_duration` and an exact `clip` output path; `capture_region: x,y,w,h` is optional.
  Invoke `scripts/capture_screen.py` as described below. A missing or failed expected output
  leaves Phase 2 incomplete; do not silently substitute a web screenshot.
- `terminal` (CLI): the default path is dependency-free (author a terminal scene from real
  output, see "Recording a CLI scene"). The optional `asciinema`→video path is used only if
  `asciinema` and `agg` are on PATH; otherwise use the default authored-scene path.
- `supplied`: the user provides the exact storyboard-bound `screenshot` or `clip` file directly.

Stills remain the universal fallback for unavailable screencast/terminal tooling. A missing
`supplied` file **does block** until the user provides it or the storyboard capture type changes.

### Canonical native capture + clip helpers (don't re-author per run)

The skill ships two reviewed, pure-stdlib helpers. Invoke them instead of writing throwaway
capture or stitching scripts:

- `scripts/capture_screen.py` orchestrates fixed-duration native desktop/region capture, invokes
  its sibling `stitch_clip.py` with an explicit `::0::<capture_duration>` trim, validates
  duration and frame count within one 30fps frame, and atomically publishes the destination
  plus its capture metadata only after success. It records no audio. Existing destinations and
  successful metadata survive every failure; the output-local raw `.mov`/`.mkv` is retained for
  recovery on failure.
- `scripts/stitch_clip.py` remains the canonical normalizer/stitcher for supplied captures,
  trimming, and multi-take assembly. It enforces constant 30fps, H.264 High / yuv420p, even
  dimensions, no audio, and `+faststart`. Multiple takes use ffmpeg's concat **filter**, not the
  concat demuxer, so heterogeneous sparse-VFR inputs normalize onto one canvas.

Copy both into the project's `scripts/` directory like the voiceover script (locate the skill dir
the way `workflows/phase-5-audio.md` § "Step 5.0: Resolve the tools this phase runs" resolves
`$SKILL_DIR`), then run:

```bash
mkdir -p scripts
cp "$SKILL_DIR/scripts/capture_screen.py" "$SKILL_DIR/scripts/stitch_clip.py" scripts/
# capture the full native desktop for six seconds, normalize, validate, then publish atomically
python3 scripts/capture_screen.py --duration 6 -o public/clips/scene-02-dashboard.mp4
# capture a region; odd source dimensions are accepted and normalized to even output dimensions
python3 scripts/capture_screen.py --duration 6 --region 100,80,1281,721 \
  -o public/clips/scene-02-dashboard.mp4
# verify the deterministic completion state against the storyboard values
python3 scripts/capture_screen.py --check --duration 6 --region 100,80,1281,721 \
  -o public/clips/scene-02-dashboard.mp4
# normalize one raw capture to the clip path
python3 scripts/stitch_clip.py raw.mp4 -o public/clips/scene-02-dashboard.mp4
# trim a sub-range (path::START::DURATION, in seconds)
python3 scripts/stitch_clip.py raw.mov::1.5::6 -o public/clips/scene-02-dashboard.mp4
# stitch several takes onto a shared canvas
python3 scripts/stitch_clip.py a.mp4 b.mp4::0::4 --width 1920 --height 1080 -o public/clips/scene-03-flow.mp4
```

`capture_screen.py --backend auto` uses:

- **macOS:** built-in `screencapture -v -V<seconds>` with optional `-R<x,y,w,h>`. It never passes
  microphone (`-g`) or system-audio (`-A`) flags. Screen Recording permission is required.
- **MCP screencast:** `--experimentalScreencast=true` is necessary but not sufficient — the MCP
  server's own PATH must also carry `ffmpeg` (it shells out to it), and that is a *different*
  machine's PATH from the one running this skill whenever the MCP is remote. A missing ffmpeg there
  fails the capture, not the feature detection, so it reads as a broken page rather than a missing
  dependency.
- **Windows:** ffmpeg `gdigrab` desktop capture, including regions.
- **Linux/X11:** ffmpeg `x11grab` using `DISPLAY`, including regions. Full-desktop capture
  feature-detects `xdpyinfo`/`xrandr`; if neither can report the desktop size, pass `--region`.
- **Wayland:** `wf-recorder` only when feature-detected. If it is unavailable or the compositor
  blocks unattended capture, stop with the helper's explicit instructions and use the desktop
  recorder; do not claim generic FFmpeg PipeWire support.
- **WSL:** no direct adapter. Record on the Windows host, make the file visible to WSL, then invoke
  `stitch_clip.py`.

Use native capture only when the frame needs the desktop or a non-browser app. Keep Chrome DevTools
screencast for DOM-page interactions and asciinema+agg for terminal motion. For multi-take edits or
supplied footage, invoke `stitch_clip.py` directly.

### Recording a native screen scene

When `capture: screen-recording`:

1. Read the required positive `capture_duration` and exact `clip` path from that frame.
   If either is absent or invalid, return to Phase 1 and repair the storyboard before recording.
2. If `capture_region` is present, require exactly four comma-separated integers
   `x,y,w,h` with positive `w` and `h`; otherwise record the full desktop.
3. Put the app and visible operating-system chrome in the confirmed theme, then visually verify
   the target region. If the app cannot provide that theme, return to Phase 1 instead of recording.
4. Invoke the canonical helper with the storyboard values:
   `python3 scripts/capture_screen.py --duration "<seconds>" [--region "<x,y,w,h>"] -o
   "<exact clip path>"`.
5. The helper first atomically acquires `<clip>.capture.lock` with an attempt/owner token, then
   writes `<clip>.capture.pending` **before** attempting capture. A concurrent attempt for the
   same output fails without touching capture state. The marker records schema version plus
   requested duration, region, backend, and output. A
   successful capture is normalized to the requested duration, validated as CFR30 within a
   one-frame duration/frame-count tolerance, then published with `<clip>.capture.json`. The
   sidecar records the successful request, resolved backend, validated media properties, file
   size, and SHA-256 fingerprint. Pending is removed only after both clip and sidecar publish.
6. Accept completion only when the frame's exact `clip` path is non-empty,
   `<clip>.capture.pending` is absent, `<clip>.capture.json` exists, and this command passes with
   the exact storyboard values:
   `python3 scripts/capture_screen.py --check --duration "<seconds>"`
   `[--region "<x,y,w,h>"] -o "<exact clip path>"`.
7. Publication, rollback, and pending cleanup happen while the attempt lock is owned; success
   and ordinary failure release that lock. If a lock remains after a crash, inspect its owner,
   PID, host, creation time, and age diagnostic. Never remove an active lock; remove the exact
   lock manually only after confirming its owner stopped. On capture, normalization, validation,
   or publication failure, the pending marker remains, so
   an older clip/sidecar cannot satisfy continue or jump checks. Keep Phase 2 incomplete. Inspect
   the retained raw/candidate diagnostics and retry the same helper command; retry atomically
   refreshes pending, and only a successful retake replaces the prior valid clip/sidecar and
   clears it. If the intended duration/region changed, repair the storyboard first and rerun with
   those new values. Never clear pending manually merely because the older clip still plays.

### Recording a web scene (screencast)

When `capture: screencast` and screencast is available (see detection above):

1. For `navigate`, size the viewport to the Phase-1 canvas with `resize_page`. For
   `attached-session`, resize only after the explicit viewport choice below, and retain the
   original dimensions for mandatory restoration.
2. Reach the frame's view according to `web_capture_source`: for `navigate`, use
   `navigate_page` + `wait_for`; for `attached-session`, keep the selected live tab at its current
   URL and use only the already-visible state. Never route an attached session through navigation.
3. Invoke `screencast_start` with a raw path beside the frame's `clip` destination,
   `filePath: "public/clips/.scene-{NN}-{slug}.screencast-raw.mp4"`.
4. Drive the scripted interaction with the existing input tools (`click`, `wait_for`,
   `evaluate_script` for scroll). In an attached session, each input action requires the exact
   per-action consent defined below. Keep the meaningful action **one continuous take** — never
   cut mid-action.
5. Invoke `screencast_stop`, then normalize the raw recording with the copied canonical helper
   into the frame's exact `clip` path:
   `python3 scripts/stitch_clip.py public/clips/.scene-{NN}-{slug}.screencast-raw.mp4 -o
   public/clips/scene-{NN}-{slug}.mp4`. Remove the raw file only after that succeeds. Keep the
   clip short (≤ ~8s) unless it's a deliberate real-time beat (e.g. a live process); over-long
   clips bloat render + repo.
6. Verify the final file exists and is non-empty (`ffprobe` duration > 0). If screencast was
   unavailable, the raw file is empty, or normalization fails, retain any raw capture for
   diagnosis, fall back to `take_screenshot`, and record `capture: screenshot` on that frame.

The recorded `public/clips/scene-{NN}-{slug}.mp4` is consumed by the Layer-A clip-scene
archetype (`templates/scene-clip.html`) in Phase 3 — no extra wiring here.

> **Screencast frames are change-driven.** CDP emits a frame only when something on the
> page visually changes — a static view (or a take that opens before any motion) yields a
> 0-byte / near-empty clip with sparse, irregular PTS. Two fixes: **lead every take with
> motion** (start `screencast_start` *before* the scripted action, or nudge a scroll/cursor
> first) so the opening frame is captured, and after `screencast_stop` **normalize the PTS**
> with `stitch_clip.py` (step 5) so the change-driven timing becomes a constant 30fps the
> renderer can footage-lock. If the clip is still empty, fall back to `take_screenshot` (step 6).

### Recording a CLI scene (terminal)

CLI tools cannot be screencast (no DOM page). Two paths — pick by the
storyboard's intent and what's installed.

**Default — authored terminal scene (deterministic, no dependency):**
1. Run the real command and capture its stdout (a Bash run, trimmed to the salient lines).
2. Author a scene from `templates/scene-terminal.html` into `scenes/{NN}-terminal.html`,
   replacing `CMD` with the real command and the `.oline` rows with the real output. Replace the
   template palette with a readable palette in the confirmed theme.
3. This is an authored **scene** (not a clip) — it composes like any Phase-3 scene; no
   `public/clips/` file is produced. It is deterministic and on-brand.

**Recommended for motion-heavy CLI — autonomous real-time recording with `asciinema` + `agg`:**

Use this when the *motion is the point* (streaming build logs, spinners,
TUIs like `lazygit`/`htop`, an interactive prompt). For full guidance —
shell pre-flight, cast editing, theme/font choices, troubleshooting — see
[`patterns/cli-terminal-capture.md`](../patterns/cli-terminal-capture.md).

**The skill drives `asciinema` itself via the Bash tool — the user does NOT
open a terminal or run anything by hand.** This works because
`asciinema rec --command "<cmd>"` is non-interactive: asciinema allocates
its own PTY, runs the command headless, captures stdout/stderr/timing,
and exits when the command exits. Wrap in `timeout` so a runaway or
non-terminating command (`htop`, dev server) can't stall the phase.

Preconditions (silently fall back to the authored-terminal path if any fail —
and when falling back, rewrite that frame's `capture` bullet to `terminal`
so downstream phases don't expect a clip that was never recorded):
- `command -v asciinema && command -v agg` both succeed
- `command -v timeout` succeeds (GNU coreutils — absent on stock macOS;
  `brew install coreutils` provides it)
- The frame's metadata block has `capture: terminal-clip` AND a `command` bullet
  carrying the exact shell command to record

Autonomous sequence the skill executes (no user input between steps):

```bash
# (Canonical copy: patterns/cli-terminal-capture.md § Recording mode — autonomous.
#  Edit BOTH together.)
# 1. Record — non-interactive, PTY-isolated, timeout-bounded.
#    --idle-time-limit collapses dead air (npm install would be 90% waiting otherwise).
#    PS1='$ ' is exported into the child PTY so the prompt is brand-clean.
#    LANG must survive the env scrub — asciinema 2.x (Python) aborts without a
#    UTF-8 locale ("asciinema needs a UTF-8 native locale to run").
#    COLUMNS/LINES set the terminal size — portable across asciinema 2.x (Python)
#    and 3.x (Rust); `rec --cols/--rows` exist only on 3.x and error out on 2.x.
#    COLUMNS=175 keeps wide output (kubectl get, docker ps) from wrapping.
#    RECORD_TIMEOUT comes from the frame's `record_timeout` bullet (default the
#    frame's duration + 2s) — bounds non-terminating commands to the frame's slot.
RECORD_TIMEOUT="${RECORD_TIMEOUT:-60}"   # seconds, from the frame's `record_timeout`
WORK_DIR=$(mktemp -d "${TMPDIR:-/tmp}/hve-terminal-clip.XXXXXX")
CAST_TMP="$WORK_DIR/scene.cast"
GIF_TMP="$WORK_DIR/scene.gif"
MP4_TMP="$WORK_DIR/scene.mp4"
CAST_OUT="public/clips/scene-{NN}-{slug}.cast"
MP4_OUT="public/clips/scene-{NN}-{slug}.mp4"

# Quarantine any previous result before this attempt. This preserves the old files
# for recovery while preventing continuation logic from accepting them as fresh output.
mkdir -p public/clips
[ ! -e "$CAST_OUT" ] || mv "$CAST_OUT" "$WORK_DIR/previous.cast" ||
  { echo "cannot quarantine previous cast — aborting terminal capture" >&2; exit 1; }
[ ! -e "$MP4_OUT" ] || mv "$MP4_OUT" "$WORK_DIR/previous.mp4" ||
  { echo "cannot quarantine previous MP4 — aborting terminal capture" >&2; exit 1; }

record_ok=
if timeout "${RECORD_TIMEOUT}s" env -i HOME="$HOME" PATH="$PATH" SHELL=/bin/bash TERM=xterm-256color \
  LANG="${LANG:-C.UTF-8}" COLUMNS=175 LINES=32 PS1='$ ' \
  asciinema rec --idle-time-limit 1.5 \
    --command "<cmd-from-storyboard>" \
    "$CAST_TMP"; then
  record_ok=1
else
  status=$?
  # 124 is an intentional timeout; every other non-zero status is a real failure.
  [ "$status" -eq 124 ] && [ -s "$CAST_TMP" ] && record_ok=1
fi

# 2. Render — agg emits a GIF (it ignores the output extension), so render to a
#    TEMP .gif (it's a multi-MB intermediate; don't park it in public/clips/).
#    Never pass --cols/--rows: agg reads the size from the cast header, which
#    already records the COLUMNS/LINES set above — a mismatch wraps/letterboxes.
if [ -n "$record_ok" ] && [ -s "$CAST_TMP" ] &&
  agg --font-size 28 --theme monokai --fps-cap 30 "$CAST_TMP" "$GIF_TMP" &&
  ffmpeg -y -i "$GIF_TMP" \
    -vf "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2" \
    -c:v libx264 -profile:v high -g 30 -keyint_min 30 -pix_fmt yuv420p -movflags +faststart \
    "$MP4_TMP" &&
  [ -s "$MP4_TMP" ] &&
  ffprobe -v error -select_streams v:0 \
    -show_entries stream=nb_frames,avg_frame_rate -of default=noprint_wrappers=1 \
    "$MP4_TMP"; then
  mv "$CAST_TMP" "$CAST_OUT"
  mv "$MP4_TMP" "$MP4_OUT"
  clip_ready=1
else
  clip_ready=
  echo "terminal clip failed — switching this frame to the authored-terminal path" >&2
  # STOP the clip branch here. Rewrite the frame's `capture` bullet to terminal in
  # storyboard.md and author scenes/{NN}-terminal.html; never run later clip steps
  # or accept an older public/clips/scene-{NN}-{slug}.mp4 as this attempt's output.
fi
```

Branch on the result: when `clip_ready=1`, author from
`templates/scene-terminal-clip.html` into `scenes/{NN}-terminal-clip.html`. Otherwise rewrite that
frame's `capture` bullet to `terminal` and author `scenes/{NN}-terminal.html` from the real command
output. Never author a terminal-clip scene after the fallback branch.

**Edge cases the autonomous path handles:**

- *Long-running / non-terminating commands.* `timeout` bounds them; the
  partial cast is still valid. Set `RECORD_TIMEOUT` from the frame's
  `record_timeout` bullet (a 6s frame shouldn't record 60s of footage — default
  is the frame's `duration` + 2s).
- *Commands needing piped input.* Use `--command "bash -c '...'"` with a
  here-doc or `printf ... | <cmd>` inside. asciinema records the resulting PTY.
- *Commands needing secrets.* Inject only the needed variable into the
  scrubbed env (`env -i ... DEPLOY_TOKEN="$DEPLOY_TOKEN" asciinema rec ...`) —
  see the pattern doc's edge-case matrix; never drop `env -i` wholesale.
- *TTY allocation failure in the sandbox.* If `asciinema rec` errors with
  *"could not allocate pty"*, the skill falls back to `script`:
  GNU/Linux `script -qc "<cmd>" /dev/null` · BSD/macOS `script -q /dev/null <cmd>`
  (BSD `script` has no `-c`), then converts the typescript via a stub cast
  header — documented in the pattern doc. If that also fails, fall back to the
  authored-terminal path.
- *agg always emits a GIF (it ignores the output extension) with change-only
  frames.* That's why step 3's ffmpeg normalize is mandatory — not an older-agg
  special case: it rebuilds a constant 30fps timeline so seek-driven `<video>`
  sync and ordinary players can open the clip.

The Footage-quality gate (below) still applies — bonus terminal-clip checks:
font ≥ 24px effective, no prompt cruft, no idle gaps > 1s, theme contrast
matches the scene background.

If `asciinema` / `agg` are missing, do **not** prompt the user to install —
fall back to the authored-terminal path and tell them once: *"asciinema/agg
not detected — using the authored terminal scene. Install with
`brew install asciinema agg` to enable autonomous terminal recording."*

## Step 2.1: Choose web capture source (web captures only)

If the `web_capture_source` frontmatter key in `storyboard.md` already contains `navigate` or
`attached-session`, reuse that explicit choice on resume. If it contains `pending`/a placeholder,
or if the user explicitly requests a change, present:

```json
{
  "questions": [{
    "question": "How should I reach the web app for capture?",
    "header": "Web source",
    "options": [
      { "label": "Attach authenticated tab", "description": "Use an already-open Chrome tab and keep its SSO/MFA session; requires a configured Chrome DevTools MCP connection." },
      { "label": "localhost:3000", "description": "Local dev server (default React/Next.js)" },
      { "label": "localhost:5173", "description": "Local dev server (Vite)" },
      { "label": "Deployed URL", "description": "I'll provide the URL" }
    ],
    "multiSelect": false
  }]
}
```

Record `attached-session` or `navigate` in the storyboard's frontmatter
`web_capture_source` before any browser action. Changing this value makes every existing
web capture stale: keep the old files for diagnosis, but do not accept them for the new source.

### Attached authenticated-session path

Use this path only after the user chooses **Attach authenticated tab**. Read
[`patterns/authenticated-browser-capture.md`](../patterns/authenticated-browser-capture.md) before
connecting.

1. Confirm that the active Chrome DevTools MCP is connected to the user's running Chrome:
   - Preferred: Chrome 144 or newer, remote debugging enabled at
     `chrome://inspect/#remote-debugging`, and the MCP server configured with `--autoConnect`.
   - Sandboxed/remote fallback: an MCP server configured with
     `--browser-url=http://127.0.0.1:9222` and a dedicated non-default Chrome profile.
   MCP configuration and Chrome's permission dialog are user-owned manual setup. Never edit a
   runtime's MCP configuration, launch a debuggable browser, or enable remote debugging without
   explicit user action. After configuration changes, stop Phase 2 and let the user restart the
   runtime, then resume.
2. Invoke `list_pages` as the connection test. If it fails, or the expected tab is absent, stop
   with the setup handoff from the pattern. Do not create a replacement page or silently switch
   to URL capture.
3. Build a selection list from the real returned pages. Show only a sanitized title plus
   scheme/host/path; omit the URL query and fragment because they may contain tokens. Present at
   most three tabs plus **More tabs**, paging until every page remains reachable:

   ```json
   {
     "questions": [{
       "question": "Which already-open Chrome tab should I capture?",
       "header": "Tab",
       "options": [
         { "label": "1. <sanitized title>", "description": "<scheme>://<host>/<path>; query and fragment omitted." },
         { "label": "2. <sanitized title>", "description": "<scheme>://<host>/<path>; query and fragment omitted." },
         { "label": "3. <sanitized title>", "description": "<scheme>://<host>/<path>; query and fragment omitted." },
         { "label": "More tabs", "description": "Show the next page of open Chrome tabs." }
       ],
       "multiSelect": false
     }]
   }
   ```

   Keep the returned page IDs only in memory for this selection; never write IDs or URLs into
   project files.
4. Invoke `select_page` with the exact ID mapped to the user's choice. Invoke `list_pages` again
   and verify that the same ID is selected. Report its sanitized title/origin and confirm:

   ```json
   {
     "questions": [{
       "question": "Use this exact authenticated tab for the bound captures?",
       "header": "Tab check",
       "options": [
         { "label": "Use this tab", "description": "Capture the selected live tab without changing its URL." },
         { "label": "Choose another", "description": "Return to the open-tab list." },
         { "label": "Stop capture", "description": "Leave the browser untouched and pause Phase 2." }
       ],
       "multiSelect": false
     }]
   }
   ```

5. Attached mode is read-only by default. Never read or persist cookies, `localStorage`,
   `sessionStorage`, authorization headers, saved passwords, or authentication tokens. Never
   submit forms, change account/app settings, publish, purchase, delete, log out, or follow links.
   If a storyboard beat genuinely requires an in-page click, scroll, or keypress, name the exact
   action and obtain per-action consent first; consent for one action does not cover another.
6. Before any temporary resize, record the selected page's original outer width and height.
   Present the viewport choice from the pattern. If the user approves resizing, use `resize_page`
   for the confirmed canvas and restore the original viewport after the last capture and on every
   failure path. If restoration fails, report it explicitly.
7. For an unchanged still, invoke `take_screenshot` directly. Use `take_snapshot` only after the
   user consents to a specific interaction; its accessibility tree may expose more than the
   visible viewport, so never persist or quote unrelated nodes. Use the screencast recipe above
   for a consented motion beat. Do not use full-page capture without separate consent because it
   may expose off-screen private data. If the confirmed theme is not already active, ask the user
   to change it manually or return to Phase 1; do not mutate a persistent theme setting in the
   authenticated profile.
8. At completion, restore the original viewport. Never close the tab or browser, and leave its
   URL and history unchanged. If the session expires or the tab closes, let the user
   re-authenticate manually and start again from `list_pages`; do not navigate to a sign-in page.

### URL navigation path

For any non-attach choice, record `web_capture_source: navigate` in the frontmatter, resolve the
selected/custom URL, and use the existing dev-server flow below.

If the app isn't running, offer to start it:
```bash
# Detect and start dev server
if [ -f "package.json" ]; then
  npm run dev &
  sleep 5
fi
```

## Step 2.2: Capture the selected web source

**Capture richly — more than one frame per view where it strengthens a beat.** A single flat
screenshot per storyboard frame is what makes the spine monotonous. For each meaningful view,
grab the states that give Phase 3 something to build motion and depth from: the default state,
the view **populated with real (or seeded) data**, a **hover / active / focus** state, an opened
menu/modal, and a **tight hero crop** of the key UI region (for a punch-in or anchored
callout). Stay on the locked Phase-1 canvas/aspect — extra viewports are for variety and
cropping only, never a second output aspect. Variety here is what lets Phase 3 frame a product
spine instead of repeating one image.

For each view bound to a frame in the storyboard (Phase 1, Step 1.6):

1. **Reach the view**:
   - For `attached-session`, retain the selected page and current URL from Step 2.1; skip this
     navigation branch entirely.
   - For `navigate`, use the Chrome DevTools `navigate_page` capability with `type: "url"` and
     the target URL, then wait for page load with `wait_for`.

2. **Set viewport** for consistent captures:
   - For `navigate`: desktop uses `emulate` with `1920x1080x2` (retina); mobile uses
     `390x844x3,mobile,touch`.
   - For `attached-session`: follow the explicit resize/keep choice and restoration contract;
     do not apply emulation or resize implicitly.

3. **Interact** if needed (click buttons, open modals, fill forms):
   - In `attached-session`, follow the read-only/per-action-consent contract above; filling or
     submitting forms is prohibited.
   - Take a snapshot first with `take_snapshot`
   - Click elements with `click` using the uid from the snapshot
   - Wait for state with `wait_for` and the target text

4. **Capture** the screenshot:
   - Invoke `take_screenshot` with `filePath` set to that frame's exact `screenshot` path
     (`public/screenshots/scene-{NN}-{description}.png`)
   - For `navigate` full-page captures: set `fullPage: true`.
   - For `attached-session`: never set `fullPage: true` without its separate consent.

5. **Repeat** for each storyboard frame

## Step 2.3: Capture Gallery

After all screenshots are taken, present them to the user:

```bash
find public/screenshots public/clips -type f 2>/dev/null | sort
find scenes -maxdepth 1 -type f -name '*terminal*.html' 2>/dev/null | sort
```

Show each screenshot with the frame it is bound to. **Also report coverage:** *N of M storyboard
frames that should show the product (per `product_surface` + the Step-1.7 binding) now have a
capture.* Call out any spine frame still missing its capture. This gallery is a **checkpoint,
not a hard gate** — the blocking capture-coverage gate runs at Phase-3 entry (see `SKILL.md`);
here you are giving the user a chance to fill gaps before design starts. Ask:

```json
{
  "questions": [{
    "question": "Screenshots look good? Any views to recapture or add?",
    "header": "Review",
    "options": [
      { "label": "All good", "description": "Proceed to design phase" },
      { "label": "Recapture some", "description": "I'll specify which ones" },
      { "label": "Add more views", "description": "I need additional screenshots" }
    ],
    "multiSelect": false
  }]
}
```

### Footage quality gate

Before accepting any recorded clip, check (retake if it fails):

- **Resolution** matches the composition canvas; **fps ≥ 30**.
- **Theme** visibly matches the confirmed Creative Brief theme, including supplied media.
- **No dev artifacts** in frame: browser notifications, autofill dropdowns, devtools/console
  overlays, extension badges, or personal data (emails, tokens, real names).
- **The meaningful action is one clean, uninterrupted take** (no mid-action cut, no stray
  cursor jitter, no accidental clicks).
- **Duration** within the frame's planned slot (Phase 4 will footage-lock it).

In the Phase-2 gallery review, present each clip and prompt the user to **accept or retake**.
A rejected clip falls back to a screenshot or a re-record.

## Capture Tips

- **Wait for animations** — Use `wait_for` to ensure page is fully loaded before capturing
- **Hide cookie banners (`navigate` only)** — Use `evaluate_script` to hide overlay elements:
  ```javascript
  () => {
    document.querySelectorAll('[class*="cookie"], [class*="consent"], [class*="banner"]')
      .forEach(el => el.style.display = 'none');
  }
  ```
- **Attached-session overlays** — Do not hide or remove DOM elements. Ask the user to dismiss an
  overlay manually, or obtain exact per-action consent for a reversible in-page dismissal.
- **Confirmed theme (media-query apps, `navigate` only)** — If the app reads
  `prefers-color-scheme`, use the
  Chrome DevTools `emulate` capability with `colorScheme` set to the confirmed `light` or `dark`.
- **Confirmed theme (class-based / Tailwind `.dark`, `navigate` only)** — `colorScheme` does
  nothing for apps that
  toggle a `.dark` class (most Next.js / shadcn). A one-shot class change is **clobbered by SPA
  hydration**. Inject a `MutationObserver` via `evaluate_script` **after `navigate_page`
  completes**. Re-inject after every navigation:
  ```javascript
  (confirmedTheme) => {
    const html = document.documentElement;
    const set = () => html.classList.toggle('dark', confirmedTheme === 'dark');
    set();
    new MutationObserver(set).observe(html, { attributes: true, attributeFilter: ['class'] });
  }
  ```
  Pass the exact confirmed theme; do not hard-code `dark`.
- **Attached-session theme** — Do not apply either override above. Ask the user to prepare the
  confirmed theme in the selected tab without changing a persistent app/account setting.
- **Retina quality** — Always use devicePixelRatio 2+ for crisp screenshots in video

## Output

Accepted outputs are saved to the exact paths bound by each frame's `screenshot` / `clip` bullet
in `storyboard.md`: screenshots under `public/screenshots/`, clips under `public/clips/`, or
authored terminal scenes under `scenes/`.

## Checkpoint

After the user accepts the capture set (or the intentional no-capture skip), stamp Phase 2:

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" stamp phase-2
```

Do not advance on a nonzero exit.

> "Capture phase complete. [N] bound artifacts are ready ([S] screenshots, [C] clips,
> [T] authored terminal scenes).
>
> Ready to move to Phase 3: Design?"

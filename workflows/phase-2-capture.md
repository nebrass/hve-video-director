# Phase 2: Capture (Chrome DevTools)

Automatically capture **artifacts** (still screenshots and/or recorded clips) for use in video scenes.

## Capture artifacts: stills and clips

Phase 2 produces **capture artifacts**: still screenshots in `public/screenshots/`
and/or recorded clips in `public/clips/`. A scene's `Capture:` field (from the
storyboard) decides which. Recording sources (Chrome screencast for web, the
terminal path for CLI) are wired in **Layer B**; in Layer A, clip scenes consume
a `public/clips/scene-{NN}-{slug}.mp4` produced by any source (including a
user-supplied file). Stills remain the default and the fallback.

### Capture-source detection (graceful, never hard-fail)

A scene's `Capture:` value selects a source; each is feature-detected and degrades cleanly:

- `screencast` (web): usable only if the chrome-devtools MCP exposes `screencast_start`
  AND the server was started with `--experimentalScreencast=true`. Detect by attempting
  it; if the tool is absent or it errors about the flag, **fall back to `take_screenshot`**,
  set the scene's `Capture: screenshot`, and tell the user how to enable it:
  restart the chrome-devtools MCP server with `--experimentalScreencast=true`.
- `terminal` (CLI): the default path is dependency-free (author a terminal scene from real
  output, see "Recording a CLI scene"). The optional `asciinema`→video path is used only if
  `asciinema` and `agg` are on PATH; otherwise use the default authored-scene path.
- `supplied`: the user provides `public/clips/scene-{NN}-{slug}.mp4` directly.

Stills remain the universal fallback — a missing source never blocks Phase 2.

### Canonical clip helper — normalize & stitch (don't re-author per run)

`scripts/stitch_clip.py` is the reviewed, portable normalizer/stitcher shipped with the skill —
invoke it instead of writing a throwaway `stitch-clip` each run (issue #19). It enforces the
Phase-2 clip contract (constant 30fps, H.264 high / yuv420p, even dimensions, `+faststart`) and
stitches multiple takes with ffmpeg's concat **filter** — each segment is re-encoded onto a shared
canvas, so heterogeneous captures with sparse VFR stitch cleanly (the concat *demuxer* / `.ffconcat`
list needs byte-identical inputs and is **not** used).

Copy it into the project like the voiceover script (locate the skill dir the way
`workflows/phase-5-audio.md` § "Generate with ElevenLabs" resolves `$SKILL_DIR`), then run:

```bash
cp "$SKILL_DIR/scripts/stitch_clip.py" ./
# normalize one raw capture to the clip path
python3 ./stitch_clip.py raw.mp4 -o public/clips/scene-02-dashboard.mp4
# trim a sub-range (path::START::DURATION, in seconds)
python3 ./stitch_clip.py raw.mov::1.5::6 -o public/clips/scene-02-dashboard.mp4
# stitch several takes onto a shared canvas
python3 ./stitch_clip.py a.mp4 b.mp4::0::4 --width 1920 --height 1080 -o public/clips/scene-03-flow.mp4
```

Use it for anything beyond a trivial single-file re-time (which the inline `ffmpeg -r 30 …` note
below still covers).

**Native screen *capture* (`capture-screen`) is intentionally not shipped** — a portable capture
backend is impossible (macOS AVFoundation, Windows gdigrab/ddagrab, X11 x11grab, Wayland portal, and
WSL all differ). Produce raw clips via the screencast (below) or asciinema+agg (CLI) paths, or have
the user supply a recording, then normalize/stitch them here. A native capture backend is a separate
follow-up (issue #19).

### Recording a web scene (screencast)

When `Capture: screencast` and screencast is available (see detection above):

1. Size the viewport to the composition canvas: `mcp__chrome-devtools__resize_page`
   to the Phase-1 dimensions (e.g. 1920×1080) so the recording matches render size.
2. Navigate to the scene's view and let it settle (`navigate_page` + `wait_for`).
3. `mcp__chrome-devtools__screencast_start` with `filePath: "public/clips/scene-{NN}-{slug}.mp4"`.
4. Drive the scripted interaction with the existing input tools (`click`, `wait_for`,
   `evaluate_script` for scroll). Keep the meaningful action **one continuous take** —
   never cut mid-action.
5. `mcp__chrome-devtools__screencast_stop`. Keep the clip short (≤ ~8s) unless it's a
   deliberate real-time beat (e.g. a live process); over-long clips bloat render + repo.
6. Verify the file exists and is non-empty (`ffprobe` duration > 0). If screencast was
   unavailable or the file is empty, fall back to `take_screenshot` for this scene and
   record `Capture: screenshot` in the storyboard.

The recorded `public/clips/scene-{NN}-{slug}.mp4` is consumed by the Layer-A clip-scene
archetype (`templates/scene-clip.html`) in Phase 3 — no extra wiring here.

> **Screencast frames are change-driven.** CDP emits a frame only when something on the
> page visually changes — a static view (or a take that opens before any motion) yields a
> 0-byte / near-empty clip with sparse, irregular PTS. Two fixes: **lead every take with
> motion** (start `screencast_start` *before* the scripted action, or nudge a scroll/cursor
> first) so the opening frame is captured, and after `screencast_stop` **normalize the PTS**
> with `ffmpeg -i in.mp4 -r 30 -pix_fmt yuv420p out.mp4` so the change-driven timing becomes a
> constant 30fps the renderer can footage-lock. If the clip is still empty, fall back to
> `take_screenshot` (step 6).

### Recording a CLI scene (terminal)

CLI tools cannot be screencast (no DOM page). Two paths — pick by the
storyboard's intent and what's installed.

**Default — authored terminal scene (deterministic, no dependency):**
1. Run the real command and capture its stdout (a Bash run, trimmed to the salient lines).
2. Author a scene from `templates/scene-terminal.html` into `scenes/{NN}-terminal.html`,
   replacing `CMD` with the real command and the `.oline` rows with the real output.
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
and when falling back, rewrite the scene's storyboard `Capture:` to `terminal`
so downstream phases don't expect a clip that was never recorded):
- `command -v asciinema && command -v agg` both succeed
- `command -v timeout` succeeds (GNU coreutils — absent on stock macOS;
  `brew install coreutils` provides it)
- The scene's storyboard entry has `Capture: terminal-clip` AND a `Command:` field
  with the exact shell command to record

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
#    RECORD_TIMEOUT comes from the storyboard's `Record timeout` field (default
#    scene_duration + 2s) — bounds non-terminating commands to the scene's slot.
RECORD_TIMEOUT="${RECORD_TIMEOUT:-60}"   # seconds, from storyboard `Record timeout`
timeout "${RECORD_TIMEOUT}s" env -i HOME="$HOME" PATH="$PATH" SHELL=/bin/bash TERM=xterm-256color \
  LANG="${LANG:-C.UTF-8}" COLUMNS=175 LINES=32 PS1='$ ' \
  asciinema rec --idle-time-limit 1.5 \
    --command "<cmd-from-storyboard>" \
    public/clips/scene-{NN}-{slug}.cast \
  || true   # exit 124 (timeout) is non-fatal — the cast up to that point is valid.
            # Verify the .cast exists before step 2: || true also masks a real
            # failure (missing binary, locale error), and step 2 needs the file.
[ -s public/clips/scene-{NN}-{slug}.cast ] || { echo "no cast recorded — falling back to authored-terminal"; }

# 2. Render — agg emits a GIF (it ignores the output extension), so render to a
#    TEMP .gif (it's a multi-MB intermediate; don't park it in public/clips/).
#    Never pass --cols/--rows: agg reads the size from the cast header, which
#    already records the COLUMNS/LINES set above — a mismatch wraps/letterboxes.
agg --font-size 28 --theme monokai --fps-cap 30 \
  public/clips/scene-{NN}-{slug}.cast \
  "${TMPDIR:-/tmp}/scene-{NN}-{slug}.gif"

# 3. Normalize to constant-fps MP4 — REQUIRED: agg emits change-only frames (a
#    short clip may be 2–4 frames) that break seek-driven <video> sync. If the
#    narration outlasts the clip, swap the filter for
#    tpad=stop_mode=clone:stop_duration=N,fps=30 (N = scene − clip; see the pattern doc).
ffmpeg -y -i "${TMPDIR:-/tmp}/scene-{NN}-{slug}.gif" \
  -vf "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2" \
  -c:v libx264 -profile:v high -pix_fmt yuv420p -movflags +faststart \
  public/clips/scene-{NN}-{slug}.mp4

# 4. Verify — fail closed (fall back to authored-terminal) if the MP4 is bad.
#    Expect ~30 × duration frames, not 2–4 sparse ones. nb_frames comes from the
#    container header ffmpeg just wrote — no need for a full -count_frames decode.
ffprobe -v error -select_streams v:0 \
  -show_entries stream=nb_frames,avg_frame_rate -of default=noprint_wrappers=1 \
  public/clips/scene-{NN}-{slug}.mp4
```

Then author the scene from `templates/scene-terminal-clip.html` into
`scenes/{NN}-terminal-clip.html` — it wraps the MP4 in a macOS-style
window for brand parity with browser-mockup scenes. Animate the
`.term-frame` wrapper, never the `<video>` itself.

**Edge cases the autonomous path handles:**

- *Long-running / non-terminating commands.* `timeout` bounds them; the
  partial cast is still valid. Set `RECORD_TIMEOUT` from the storyboard's
  `Record timeout` (a 6s scene shouldn't record 60s of footage — default is
  `scene_duration + 2s`).
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

## Step 2.1: Get App URL

```json
{
  "questions": [{
    "question": "What's the app URL to capture?",
    "header": "URL",
    "options": [
      { "label": "localhost:3000", "description": "Local dev server (default React/Next.js)" },
      { "label": "localhost:5173", "description": "Local dev server (Vite)" },
      { "label": "Deployed URL", "description": "I'll provide the URL" }
    ],
    "multiSelect": false
  }]
}
```

If the app isn't running, offer to start it:
```bash
# Detect and start dev server
if [ -f "package.json" ]; then
  npm run dev &
  sleep 5
fi
```

## Step 2.2: Navigate and Capture

For each view defined in the storyboard (Phase 1, Step 1.6):

1. **Navigate** to the URL:
   - Use `mcp__chrome-devtools__navigate_page` with `type: "url"` and the target URL
   - Wait for page load with `mcp__chrome-devtools__wait_for`

2. **Set viewport** for consistent captures:
   - Desktop: `mcp__chrome-devtools__emulate` with viewport `1920x1080x2` (retina)
   - Mobile: `mcp__chrome-devtools__emulate` with viewport `390x844x3,mobile,touch`

3. **Interact** if needed (click buttons, open modals, fill forms):
   - Take a snapshot first: `mcp__chrome-devtools__take_snapshot`
   - Click elements: `mcp__chrome-devtools__click` with uid from snapshot
   - Wait for state: `mcp__chrome-devtools__wait_for` with target text

4. **Capture** the screenshot:
   - `mcp__chrome-devtools__take_screenshot` with `filePath: "public/screenshots/scene-{NN}-{description}.png"`
   - For full-page captures: set `fullPage: true`

5. **Repeat** for each storyboard scene

## Step 2.3: Capture Gallery

After all screenshots are taken, present them to the user:

```bash
ls -la public/screenshots/
```

Show each screenshot with its scene number. Ask:

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
- **No dev artifacts** in frame: browser notifications, autofill dropdowns, devtools/console
  overlays, extension badges, or personal data (emails, tokens, real names).
- **The meaningful action is one clean, uninterrupted take** (no mid-action cut, no stray
  cursor jitter, no accidental clicks).
- **Duration** within the scene's planned slot (Phase 4 will footage-lock it).

In the Phase-2 gallery review, present each clip and prompt the user to **accept or retake**.
A rejected clip falls back to a screenshot or a re-record.

## Capture Tips

- **Wait for animations** — Use `wait_for` to ensure page is fully loaded before capturing
- **Hide cookie banners** — Use `evaluate_script` to hide overlay elements:
  ```javascript
  () => {
    document.querySelectorAll('[class*="cookie"], [class*="consent"], [class*="banner"]')
      .forEach(el => el.style.display = 'none');
  }
  ```
- **Dark mode (media-query apps)** — If the app reads `prefers-color-scheme`, use `mcp__chrome-devtools__emulate` with `colorScheme: "dark"`
- **Dark mode (class-based / Tailwind `.dark`)** — `colorScheme` does nothing for apps that toggle a `.dark` class (most Next.js / shadcn). A one-shot injected class is **clobbered by SPA hydration** (React re-renders the root and overwrites it). Inject a `MutationObserver` via `evaluate_script` **after `navigate_page` completes** — the observer re-adds the class every time hydration strips it (hydration re-renders don't navigate, so the observer survives them). Order matters: `evaluate_script` runs in the current document only, and any navigation wipes the page's JS context — an observer injected *before* navigating is destroyed by the navigation itself. Re-inject after every `navigate_page`:
  ```javascript
  () => {
    const html = document.documentElement;
    const set = () => html.classList.add('dark');   // or your app's theme class
    set();
    new MutationObserver(set).observe(html, { attributes: true, attributeFilter: ['class'] });
  }
  ```
- **Retina quality** — Always use devicePixelRatio 2+ for crisp screenshots in video

## Output

Screenshots saved to `public/screenshots/scene-{NN}-{description}.png`

## Checkpoint

> "Captured [N] screenshots from [URL].
>
> Ready to move to Phase 3: Design?"
